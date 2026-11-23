// Direct Bluetooth link to a stock OSSM, the way the RADR remote does it.
//
// The Flipper connects as a BLE central (needs the flipper-ble-scanner
// firmware: Momentum + ST Full radio stack; see ossm_central.c), finds the
// OSSM by its service UUID, then:
//   - writes text commands ("set:speed:40", "go:strokeEngine", ...) to the
//     command characteristic,
//   - subscribes to the state characteristic (JSON) and long-reads it when a
//     notification is cut short by the MTU,
//   - reads the pattern list once.
// See docs/PROTOCOL.md for the characteristics.

#include "ossm_remote.h"

#include "ossm_central.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TAG "OssmBle"

#define EVENT_DATA_MAX     255
#define READ_BUF_MAX       1536
#define CMD_QUEUE_LEN      8
#define CMD_LEN            40
#define CONNECT_TIMEOUT_MS 6000
#define SETUP_TIMEOUT_MS   8000
#define STATE_POLL_MS      2000
#define RSSI_POLL_MS       2000

// 522b443a-4f53-534d-XXXX-420badbabe69, little-endian as sent over the air
#define OSSM_UUID(hi, lo)                                                                   \
    {0x69, 0xbe, 0xba, 0xad, 0x0b, 0x42, lo, hi, 0x4d, 0x53, 0x53, 0x4f, 0x3a, 0x44, 0x2b, 0x52}
static const uint8_t uuid_service[16] = OSSM_UUID(0x00, 0x01);
static const uint8_t uuid_command[16] = OSSM_UUID(0x10, 0x00);
static const uint8_t uuid_knob[16] = OSSM_UUID(0x10, 0x10);
static const uint8_t uuid_state[16] = OSSM_UUID(0x20, 0x00);
static const uint8_t uuid_patterns[16] = OSSM_UUID(0x30, 0x00);

typedef enum {
    StepIdle,
    StepScanning,
    StepConnecting,
    StepMtu,
    StepDiscCommand,
    StepDiscState,
    StepDiscPatterns,
    StepDiscKnob,
    StepSubscribe,
    StepKnobOff,
    StepReadState,
    StepReadPatterns,
    StepUp,
} Step;

typedef enum {
    ReadNone,
    ReadState,
    ReadPatterns,
} ReadKind;

typedef struct {
    OssmCentralEventType type;
    uint8_t addr[6];
    uint8_t addr_type;
    int8_t rssi;
    uint8_t status;
    uint16_t handle;
    uint8_t len;
    uint8_t data[EVENT_DATA_MAX];
} BleMsg;

typedef struct OssmBle {
    FuriMessageQueue* events;
    bool acquired;
    bool want_scan;
    Step step;
    uint32_t step_since;

    uint8_t peer[6];
    uint8_t peer_type;
    bool have_peer;
    char peer_name[20];

    uint16_t h_command, h_state, h_patterns, h_knob;
    uint16_t found_handle; // result of the current discovery

    bool busy; // a GATT procedure is running
    ReadKind reading;
    char read_buf[READ_BUF_MAX + 1];
    size_t read_len;
    bool want_state, want_patterns;
    uint32_t last_state_read;
    uint32_t last_rssi;

    char cmds[CMD_QUEUE_LEN][CMD_LEN];
    uint8_t cmd_head, cmd_count;
} OssmBle;

// ---------- advertising data ----------

// Does this AD payload list the OSSM service? Copies the name if present.
static bool ad_parse(const uint8_t* d, uint8_t len, bool* has_ossm, char* name, size_t name_len) {
    size_t i = 0;
    bool any = false;
    while(i + 1 < len) {
        uint8_t field_len = d[i];
        if(field_len == 0 || i + 1 + field_len > len) break;
        uint8_t type = d[i + 1];
        const uint8_t* v = &d[i + 2];
        uint8_t vlen = field_len - 1;
        if(type == 0x06 || type == 0x07) { // 128-bit service UUIDs
            for(uint8_t k = 0; k + 16 <= vlen; k += 16) {
                if(memcmp(&v[k], uuid_service, 16) == 0) *has_ossm = true;
            }
            any = true;
        } else if((type == 0x08 || type == 0x09) && name) { // local name
            size_t n = vlen < name_len - 1 ? vlen : name_len - 1;
            memcpy(name, v, n);
            name[n] = 0;
            any = true;
        }
        i += 1 + field_len;
    }
    return any;
}

// Runs on the BLE event thread: filter hard, copy, hand to the app thread.
static void central_cb(const OssmCentralEvent* event, void* context) {
    OssmBle* ble = context;
    BleMsg msg = {.type = event->type};

    if(event->type == OssmCentralEventTypeAdvReport) {
        if(ble->step != StepScanning) return;
        bool has_ossm = false;
        char name[20] = {0};
        ad_parse(event->data, event->data_len, &has_ossm, name, sizeof(name));
        bool is_peer = ble->have_peer && memcmp(event->addr, ble->peer, 6) == 0;
        if(!has_ossm && !is_peer) return; // most traffic ends here
        memcpy(msg.addr, event->addr, 6);
        msg.addr_type = event->addr_type;
        msg.rssi = event->rssi;
        msg.status = has_ossm;
        msg.len = strlen(name);
        memcpy(msg.data, name, msg.len);
    } else {
        msg.status = event->status;
        msg.handle = event->handle;
        if(event->type == OssmCentralEventTypeConnected) {
            memcpy(msg.addr, event->addr, 6);
        }
        if(event->data && event->data_len) {
            msg.len = event->data_len;
            memcpy(msg.data, event->data, msg.len);
        }
    }
    furi_message_queue_put(ble->events, &msg, 0);
}

// ---------- tiny JSON helpers (the OSSM's payloads are flat) ----------

static const char* json_find(const char* json, const char* key) {
    char pat[24];
    snprintf(pat, sizeof(pat), "\"%s\":", key);
    const char* p = strstr(json, pat);
    return p ? p + strlen(pat) : NULL;
}

static int json_int(const char* json, const char* key, int def) {
    const char* p = json_find(json, key);
    return p ? atoi(p) : def;
}

static bool json_str(const char* json, const char* key, char* out, size_t out_len) {
    const char* p = json_find(json, key);
    if(!p || *p != '"') return false;
    p++;
    size_t n = 0;
    while(*p && *p != '"' && n < out_len - 1)
        out[n++] = *p++;
    out[n] = 0;
    return true;
}

static void apply_state(OssmApp* app, const char* json) {
    OssmModel* m = &app->m;
    char st[OSSM_STATE_LEN];
    if(!json_str(json, "state", st, sizeof(st))) return;
    strlcpy(m->ossm_state, st, sizeof(m->ossm_state));
    m->remote_speed = json_int(json, "speed", 0);
    m->bridge_seen = true;
    m->bridge_last_rx = furi_get_tick();
    // Adopt the OSSM's values unless the user is mid-edit. Speed belongs to
    // the Flipper (play/pause + ramp) and is never adopted.
    if(furi_get_tick() - m->last_edit > 1500) {
        int pat = json_int(json, "pattern", m->value[ParamPattern]);
        m->value[ParamStroke] = json_int(json, "stroke", m->value[ParamStroke]);
        m->value[ParamDepth] = json_int(json, "depth", m->value[ParamDepth]);
        m->value[ParamSensation] = json_int(json, "sensation", m->value[ParamSensation]);
        if(pat >= 0 && pat < OSSM_PATTERN_MAX) m->value[ParamPattern] = pat;
        for(int p = ParamStroke; p < ParamCount; p++)
            m->sent[p] = m->value[p];
    }
}

static void apply_patterns(OssmApp* app, const char* json) {
    // [{"name":"Simple Stroke","idx":0},...]
    OssmModel* m = &app->m;
    const char* p = json;
    uint8_t count = 0;
    while((p = strstr(p, "\"name\":\"")) != NULL) {
        char name[OSSM_PATTERN_NAME_LEN];
        if(!json_str(p - 0, "name", name, sizeof(name))) break;
        int idx = json_int(p, "idx", count);
        if(idx >= 0 && idx < OSSM_PATTERN_MAX) {
            strlcpy(m->patterns[idx], name, OSSM_PATTERN_NAME_LEN);
            if(idx + 1 > count) count = idx + 1;
        }
        p += 8;
    }
    if(count) m->pattern_count = count;
}

// ---------- link steps ----------

static void set_step(OssmBle* ble, Step step) {
    ble->step = step;
    ble->step_since = furi_get_tick();
}

static void link_down(OssmApp* app, bool lost) {
    OssmBle* ble = app->ble;
    if(lost && app->m.link == LinkUp) app->m.link_lost_at = furi_get_tick();
    app->m.link = ble->acquired ? LinkIdle : LinkNoBridge;
    ble->busy = false;
    ble->reading = ReadNone;
    ble->cmd_count = 0;
    ble->h_command = ble->h_state = ble->h_patterns = ble->h_knob = 0;
    set_step(ble, StepIdle);
}

static void start_scan(OssmApp* app) {
    OssmBle* ble = app->ble;
    ble->have_peer = false;
    if(ossm_central_scan_start(true)) {
        set_step(ble, StepScanning);
        app->m.link = LinkScanning;
    }
}

static bool discover(OssmBle* ble, const uint8_t uuid[16], Step step) {
    ble->found_handle = 0;
    if(!ossm_central_discover_char(uuid)) return false;
    ble->busy = true;
    set_step(ble, step);
    return true;
}

static bool start_read(OssmBle* ble, uint16_t handle, ReadKind kind) {
    if(!handle || ble->busy) return false;
    ble->read_len = 0;
    if(!ossm_central_read(handle)) return false;
    ble->busy = true;
    ble->reading = kind;
    return true;
}

// Called when a GATT procedure finishes, to move setup along.
static void setup_next(OssmApp* app, uint8_t status) {
    OssmBle* ble = app->ble;
    ble->busy = false;
    switch(ble->step) {
    case StepMtu:
        discover(ble, uuid_command, StepDiscCommand);
        break;
    case StepDiscCommand:
        ble->h_command = ble->found_handle;
        if(!ble->h_command) {
            FURI_LOG_E(TAG, "No command characteristic");
            ossm_central_disconnect();
            break;
        }
        discover(ble, uuid_state, StepDiscState);
        break;
    case StepDiscState:
        ble->h_state = ble->found_handle;
        discover(ble, uuid_patterns, StepDiscPatterns);
        break;
    case StepDiscPatterns:
        ble->h_patterns = ble->found_handle;
        discover(ble, uuid_knob, StepDiscKnob);
        break;
    case StepDiscKnob:
        ble->h_knob = ble->found_handle;
        // NimBLE puts the CCCD right after a notify characteristic's value.
        if(ble->h_state && ossm_central_subscribe(ble->h_state + 1, true)) {
            ble->busy = true;
            set_step(ble, StepSubscribe);
            break;
        }
        // fall through: no notifications, we poll instead
        /* FALLTHRU */
    case StepSubscribe:
        // Same as RADR: BLE speed independent of the OSSM's own knob.
        if(ble->h_knob &&
           ossm_central_write(ble->h_knob, (const uint8_t*)"false", 5, true)) {
            ble->busy = true;
            set_step(ble, StepKnobOff);
            break;
        }
        /* FALLTHRU */
    case StepKnobOff:
        set_step(ble, StepReadState);
        if(!start_read(ble, ble->h_state, ReadState)) setup_next(app, 0);
        break;
    case StepReadState:
        set_step(ble, StepReadPatterns);
        if(!start_read(ble, ble->h_patterns, ReadPatterns)) setup_next(app, 0);
        break;
    case StepReadPatterns:
        set_step(ble, StepUp);
        app->m.link = LinkUp;
        ble->last_state_read = furi_get_tick();
        break;
    default:
        break;
    }
    UNUSED(status);
}

static void finish_read(OssmApp* app) {
    OssmBle* ble = app->ble;
    ble->read_buf[ble->read_len] = 0;
    if(ble->reading == ReadState) {
        apply_state(app, ble->read_buf);
        ble->last_state_read = furi_get_tick();
    } else if(ble->reading == ReadPatterns) {
        apply_patterns(app, ble->read_buf);
    }
    ble->reading = ReadNone;
}

static void handle_msg(OssmApp* app, BleMsg* msg) {
    OssmBle* ble = app->ble;
    OssmModel* m = &app->m;

    switch(msg->type) {
    case OssmCentralEventTypeAdvReport:
        if(ble->step != StepScanning) break;
        if(msg->status) { // advertises the OSSM service
            memcpy(ble->peer, msg->addr, 6);
            ble->peer_type = msg->addr_type;
            ble->have_peer = true;
            m->rssi = msg->rssi;
        }
        if(msg->len) {
            size_t n = msg->len < sizeof(ble->peer_name) - 1 ? msg->len : sizeof(ble->peer_name) - 1;
            memcpy(ble->peer_name, msg->data, n);
            ble->peer_name[n] = 0;
            strlcpy(m->ossm_name, ble->peer_name, sizeof(m->ossm_name));
        }
        if(ble->have_peer) {
            ossm_central_scan_stop();
            if(ossm_central_connect(ble->peer, ble->peer_type)) {
                set_step(ble, StepConnecting);
                m->link = LinkConnecting;
            } else {
                link_down(app, false);
            }
        }
        break;

    case OssmCentralEventTypeConnected:
        set_step(ble, StepMtu);
        if(ossm_central_exchange_mtu()) {
            ble->busy = true;
        } else {
            setup_next(app, 0);
        }
        break;

    case OssmCentralEventTypeConnectFailed:
        FURI_LOG_W(TAG, "Connect failed: %02X", msg->status);
        link_down(app, false);
        break;

    case OssmCentralEventTypeDisconnected:
        FURI_LOG_I(TAG, "Disconnected: %02X", msg->status);
        link_down(app, true);
        break;

    case OssmCentralEventTypeCharFound:
        if(!ble->found_handle) ble->found_handle = msg->handle;
        break;

    case OssmCentralEventTypeNotification:
        if(msg->handle == ble->h_state) {
            msg->data[msg->len < EVENT_DATA_MAX ? msg->len : EVENT_DATA_MAX - 1] = 0;
            const char* s = (const char*)msg->data;
            if(msg->len && s[0] == '{' && s[msg->len - 1] == '}') {
                apply_state(app, s);
            } else {
                ble->want_state = true; // cut short by the MTU: read it all
            }
        }
        break;

    case OssmCentralEventTypeReadData:
        if(ble->reading != ReadNone) {
            size_t room = READ_BUF_MAX - ble->read_len;
            size_t n = msg->len < room ? msg->len : room;
            memcpy(ble->read_buf + ble->read_len, msg->data, n);
            ble->read_len += n;
        }
        break;

    case OssmCentralEventTypeGattError:
        FURI_LOG_W(TAG, "GATT error %02X on %04X", msg->status, msg->handle);
        break;

    case OssmCentralEventTypeProcComplete:
        if(ble->reading != ReadNone) finish_read(app);
        if(ble->step != StepUp) {
            setup_next(app, msg->status);
        } else {
            ble->busy = false;
        }
        break;

    case OssmCentralEventTypeMtu:
        break;
    }
}

// ---------- commands ----------

static void cmd_push(OssmBle* ble, const char* cmd, bool front) {
    if(ble->cmd_count == CMD_QUEUE_LEN) {
        // drop the oldest; speed updates supersede each other anyway
        ble->cmd_head = (ble->cmd_head + 1) % CMD_QUEUE_LEN;
        ble->cmd_count--;
    }
    uint8_t slot;
    if(front) {
        ble->cmd_head = (ble->cmd_head + CMD_QUEUE_LEN - 1) % CMD_QUEUE_LEN;
        slot = ble->cmd_head;
    } else {
        slot = (ble->cmd_head + ble->cmd_count) % CMD_QUEUE_LEN;
    }
    strlcpy(ble->cmds[slot], cmd, CMD_LEN);
    ble->cmd_count++;
}

static void cmd_flush(OssmBle* ble) {
    while(ble->cmd_count && ble->step == StepUp && ble->h_command) {
        const char* cmd = ble->cmds[ble->cmd_head];
        if(!ossm_central_write(ble->h_command, (const uint8_t*)cmd, strlen(cmd), false)) {
            break; // TX pool full, try next tick
        }
        ble->cmd_head = (ble->cmd_head + 1) % CMD_QUEUE_LEN;
        ble->cmd_count--;
    }
}

// ---------- public ----------

void ossm_link_start(OssmApp* app) {
    OssmBle* ble = malloc(sizeof(OssmBle));
    memset(ble, 0, sizeof(OssmBle));
    app->ble = ble;
    ble->events = furi_message_queue_alloc(16, sizeof(BleMsg));
    ble->want_scan = true;
    set_step(ble, StepIdle);
    ble->acquired = ossm_central_acquire(central_cb, ble);
    app->m.link = ble->acquired ? LinkIdle : LinkNoBridge;
    app->m.bridge_seen = ble->acquired;
    if(!ble->acquired) FURI_LOG_E(TAG, "BLE central not available on this firmware");
}

void ossm_link_stop(OssmApp* app) {
    OssmBle* ble = app->ble;
    if(ble->acquired) {
        // last chance to park the machine
        if(ble->step == StepUp && ble->h_command) {
            ossm_central_write(ble->h_command, (const uint8_t*)"set:speed:0", 11, false);
            furi_delay_ms(30);
            ossm_central_write(ble->h_command, (const uint8_t*)"go:menu", 7, false);
            furi_delay_ms(30);
        }
        ossm_central_release();
    }
    furi_message_queue_free(ble->events);
    free(ble);
    app->ble = NULL;
}

void ossm_link_send(OssmApp* app, const char* line) {
    OssmBle* ble = app->ble;
    if(!ble->acquired) return;

    if(strncmp(line, "CMD ", 4) == 0) {
        cmd_push(ble, line + 4, false);
        cmd_flush(ble);
    } else if(strcmp(line, "STOP") == 0) {
        // Emergency stop jumps the queue.
        ble->cmd_count = 0;
        cmd_push(ble, "set:speed:0", false);
        cmd_push(ble, "go:menu", false);
        cmd_flush(ble);
    } else if(strcmp(line, "SCAN") == 0) {
        ble->want_scan = true;
        if(ble->step == StepIdle) start_scan(app);
    } else if(strcmp(line, "DISC") == 0) {
        ble->want_scan = false;
        ossm_central_scan_stop();
        ossm_central_connect_cancel();
        ossm_central_disconnect();
    } else if(strcmp(line, "PAT?") == 0) {
        ble->want_patterns = true;
    } else if(strcmp(line, "ST?") == 0) {
        ble->want_state = true;
    }
    // PING / HI were for the UART bridge: nothing to do.
}

void ossm_link_cmd(OssmApp* app, const char* fmt, ...) {
    char buf[CMD_LEN + 4] = "CMD ";
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf + 4, sizeof(buf) - 4, fmt, args);
    va_end(args);
    ossm_link_send(app, buf);
}

void ossm_link_poll(OssmApp* app) {
    OssmBle* ble = app->ble;
    if(!ble->acquired) return;

    BleMsg msg;
    while(furi_message_queue_get(ble->events, &msg, 0) == FuriStatusOk) {
        handle_msg(app, &msg);
    }

    uint32_t now = furi_get_tick();
    switch(ble->step) {
    case StepIdle:
        if(ble->want_scan) start_scan(app);
        break;
    case StepScanning:
        break;
    case StepConnecting:
        if(now - ble->step_since > CONNECT_TIMEOUT_MS) {
            ossm_central_connect_cancel();
            link_down(app, false);
        }
        break;
    case StepUp:
        cmd_flush(ble);
        if(!ble->busy) {
            if(ble->want_patterns) {
                ble->want_patterns = !start_read(ble, ble->h_patterns, ReadPatterns);
            } else if(ble->want_state || now - ble->last_state_read > STATE_POLL_MS) {
                ble->want_state = false;
                ble->last_state_read = now;
                start_read(ble, ble->h_state, ReadState);
            }
        }
        if(now - ble->last_rssi > RSSI_POLL_MS) {
            ble->last_rssi = now;
            int8_t rssi;
            if(ossm_central_get_rssi(&rssi)) app->m.rssi = rssi;
        }
        app->m.bridge_last_rx = now;
        break;
    default:
        // Setting up: give up if the OSSM stops answering.
        if(now - ble->step_since > SETUP_TIMEOUT_MS) {
            FURI_LOG_W(TAG, "Setup stalled at step %d", ble->step);
            ossm_central_disconnect();
            link_down(app, false);
        }
        break;
    }
}
