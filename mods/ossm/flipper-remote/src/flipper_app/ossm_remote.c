// OSSM Remote for Flipper Zero
// Controls an OSSM the way the RADR remote does, through a small ESP32 BLE
// bridge on the GPIO header (the Flipper cannot be a BLE central itself).

#include "ossm_remote.h"

#include <math.h>
#include <string.h>

#define TICK_MS          33 // ~30 fps animations
#define PING_MS          300
#define HI_MS            1000
#define SEND_MIN_MS      60 // throttle BLE writes
#define RAMP_PER_TICK    3 // % speed per tick when resuming (~1 s to 100%)
#define ESTOP_SHOW_MS    1400
#define SPLASH_MS        1700

typedef enum {
    EvInput,
    EvTick,
} EvType;

typedef struct {
    EvType type;
    InputEvent input;
} Event;

static const char* default_patterns[] = {
    "Simple Stroke",
    "Teasing Pounding",
    "Robo Stroke",
    "Half'n'Half",
    "Deeper",
    "Stop'n'Go",
    "Insist",
};

static void goto_screen(OssmModel* m, Screen s) {
    m->screen = s;
    m->screen_since = furi_get_tick();
}

static void toast(OssmModel* m, const char* text) {
    strlcpy(m->toast, text, sizeof(m->toast));
    m->toast_at = furi_get_tick();
}

// ---------- callbacks ----------

static void input_cb(InputEvent* input, void* ctx) {
    OssmApp* app = ctx;
    Event ev = {.type = EvInput, .input = *input};
    furi_message_queue_put(app->queue, &ev, 0);
}

static void timer_cb(void* ctx) {
    OssmApp* app = ctx;
    Event ev = {.type = EvTick};
    furi_message_queue_put(app->queue, &ev, 0);
}

// ---------- actions ----------

static void emergency_stop(OssmApp* app) {
    OssmModel* m = &app->m;
    m->playing = false;
    m->out_speed = 0;
    m->sent[ParamSpeed] = 0;
    m->estop_at = furi_get_tick();
    // Handled by the bridge before anything queued: speed 0, then go:menu.
    ossm_link_send(app, "STOP");
    notification_message(app->notify, &sequence_set_red_255);
    notification_message(app->notify, &sequence_double_vibro);
}

static void enter_mode(OssmApp* app, OssmMode mode) {
    OssmModel* m = &app->m;
    m->mode = mode;
    m->playing = false;
    m->out_speed = 0;
    m->value[ParamSpeed] = 0;
    m->sent[ParamSpeed] = -1;
    m->cursor = ParamSpeed;
    m->last_edit = 0;
    ossm_link_cmd(app, "set:speed:0");
    if(mode == ModeStrokeEngine) {
        ossm_link_cmd(app, "go:strokeEngine");
        furi_delay_ms(250);
        ossm_link_cmd(app, "go:strokeEngine"); // RADR sends it twice too
    } else {
        ossm_link_cmd(app, "go:simplePenetration");
    }
    ossm_link_send(app, "PAT?");
    goto_screen(m, ScreenControl);
    notification_message(app->notify, &sequence_single_vibro);
}

static void leave_to_menu(OssmApp* app) {
    OssmModel* m = &app->m;
    m->playing = false;
    m->out_speed = 0;
    ossm_link_cmd(app, "set:speed:0");
    ossm_link_cmd(app, "go:menu");
    goto_screen(m, ScreenMode);
}

static void adjust(OssmModel* m, int delta) {
    Param p = m->cursor;
    if(p == ParamPattern) {
        int n = m->pattern_count ? m->pattern_count : 7;
        int v = m->value[p] + (delta > 0 ? 1 : -1);
        m->value[p] = (v + n) % n;
    } else {
        int v = m->value[p] + delta;
        if(v < 0) v = 0;
        if(v > 100) v = 100;
        m->value[p] = v;
    }
    m->last_edit = furi_get_tick();
}

static void move_cursor(OssmModel* m, int dir) {
    int c = m->cursor;
    for(int i = 0; i < ParamCount; i++) {
        c = (c + dir + ParamCount) % ParamCount;
        if(ossm_param_visible(m, (Param)c)) break;
    }
    m->cursor = (Param)c;
}

// Push changed values to the OSSM, throttled.
static void flush_values(OssmApp* app) {
    OssmModel* m = &app->m;
    if(m->link != LinkUp) return;
    uint32_t now = furi_get_tick();

    // Speed ramps up gently on resume, but drops instantly.
    int target = m->playing ? m->value[ParamSpeed] : 0;
    if(m->out_speed > target) {
        m->out_speed = target;
    } else if(m->out_speed < target) {
        m->out_speed += RAMP_PER_TICK;
        if(m->out_speed > target) m->out_speed = target;
    }

    if(m->out_speed != m->sent[ParamSpeed]) {
        bool urgent = m->out_speed < m->sent[ParamSpeed];
        if(urgent || now - m->last_send >= SEND_MIN_MS) {
            ossm_link_cmd(app, "set:speed:%d", m->out_speed);
            m->sent[ParamSpeed] = m->out_speed;
            m->last_send = now;
        }
    }

    static const char* keys[ParamCount] = {NULL, "depth", "stroke", "sensation", "pattern"};
    for(int p = ParamDepth; p < ParamCount; p++) {
        if(!ossm_param_visible(m, p)) continue;
        if(m->value[p] == m->sent[p]) continue;
        if(now - m->last_send < SEND_MIN_MS) break;
        ossm_link_cmd(app, "set:%s:%d", keys[p], m->value[p]);
        m->sent[p] = m->value[p];
        m->last_send = now;
    }
}

// ---------- input ----------

static bool handle_input(OssmApp* app, InputEvent* in) {
    OssmModel* m = &app->m;

    // STOP is always one press away while driving.
    if(m->screen == ScreenControl && in->key == InputKeyBack && in->type == InputTypeShort) {
        emergency_stop(app);
        return true;
    }

    switch(m->screen) {
    case ScreenSplash:
        if(in->type == InputTypeShort) goto_screen(m, ScreenConnect);
        if(in->key == InputKeyBack && in->type == InputTypeLong) return false;
        break;

    case ScreenConnect:
        if(in->key == InputKeyBack && in->type == InputTypeShort) return false;
        if(in->key == InputKeyOk && in->type == InputTypeShort) ossm_link_send(app, "SCAN");
        break;

    case ScreenMode:
        if(in->type != InputTypeShort) break;
        if(in->key == InputKeyLeft || in->key == InputKeyRight || in->key == InputKeyUp ||
           in->key == InputKeyDown) {
            m->mode_cursor ^= 1;
        } else if(in->key == InputKeyOk) {
            enter_mode(app, m->mode_cursor == 0 ? ModeStrokeEngine : ModeSimple);
        } else if(in->key == InputKeyBack) {
            return false;
        }
        break;

    case ScreenControl:
        if(in->key == InputKeyBack && in->type == InputTypeLong) {
            leave_to_menu(app);
            break;
        }
        if(m->estop_at && in->type == InputTypeShort) {
            m->estop_at = 0; // any key dismisses the STOP card
            notification_message(app->notify, &sequence_reset_red);
            break;
        }
        if(in->key == InputKeyUp && (in->type == InputTypeShort || in->type == InputTypeRepeat)) {
            move_cursor(m, -1);
        } else if(
            in->key == InputKeyDown &&
            (in->type == InputTypeShort || in->type == InputTypeRepeat)) {
            move_cursor(m, 1);
        } else if(in->key == InputKeyLeft || in->key == InputKeyRight) {
            int dir = in->key == InputKeyRight ? 1 : -1;
            if(in->type == InputTypeShort) adjust(m, dir);
            else if(in->type == InputTypeRepeat || in->type == InputTypeLong) adjust(m, dir * 5);
        } else if(in->key == InputKeyOk && in->type == InputTypeShort) {
            m->playing = !m->playing;
            if(m->playing && m->value[ParamSpeed] == 0) {
                m->value[ParamSpeed] = 10;
                m->cursor = ParamSpeed;
            }
            toast(m, m->playing ? "Play" : "Paused");
            notification_message(app->notify, &sequence_single_vibro);
        }
        break;
    }
    return true;
}

// ---------- tick ----------

static void handle_tick(OssmApp* app) {
    OssmModel* m = &app->m;
    uint32_t now = furi_get_tick();

    ossm_link_poll(app);

    if(now - app->last_ping >= PING_MS) {
        app->last_ping = now;
        ossm_link_send(app, "PING");
    }
    if(!m->bridge_seen && now - app->last_hi >= HI_MS) {
        app->last_hi = now;
        ossm_link_send(app, "HI");
    }

    // Animation clocks. Stroke rate ~0..3 Hz follows the speed actually sent.
    float hz = m->playing ? (0.15f + 2.8f * m->out_speed / 100.0f) : 0.0f;
    m->phase += 2.0f * (float)M_PI * hz * TICK_MS / 1000.0f;
    if(m->phase > 2.0f * (float)M_PI) m->phase -= 2.0f * (float)M_PI;
    m->beat = m->playing ? powf(fabsf(sinf(m->phase)), 6.0f) : 0.0f;

    switch(m->screen) {
    case ScreenSplash:
        if(now - m->screen_since > SPLASH_MS) goto_screen(m, ScreenConnect);
        break;
    case ScreenConnect:
        if(m->link == LinkIdle && now - app->last_hi >= 2000) {
            app->last_hi = now;
            ossm_link_send(app, "SCAN");
        }
        if(m->link == LinkUp && now - m->screen_since > 600) {
            notification_message(app->notify, &sequence_success);
            goto_screen(m, ScreenMode);
        }
        break;
    case ScreenMode:
    case ScreenControl:
        if(m->link != LinkUp) {
            m->playing = false;
            m->out_speed = 0;
            notification_message(app->notify, &sequence_error);
            goto_screen(m, ScreenConnect);
        }
        break;
    }

    if(m->estop_at && now - m->estop_at > ESTOP_SHOW_MS) {
        m->estop_at = 0;
        notification_message(app->notify, &sequence_reset_red);
    }

    if(m->screen == ScreenControl) flush_values(app);
}

// ---------- entry ----------

int32_t ossm_remote_app(void* p) {
    UNUSED(p);
    OssmApp* app = malloc(sizeof(OssmApp));
    memset(app, 0, sizeof(OssmApp));
    OssmModel* m = &app->m;

    m->link = LinkNoBridge;
    m->value[ParamSpeed] = 0;
    m->value[ParamDepth] = 50;
    m->value[ParamStroke] = 50;
    m->value[ParamSensation] = 50;
    m->value[ParamPattern] = 0;
    for(int i = 0; i < ParamCount; i++)
        m->sent[i] = -1;
    for(size_t i = 0; i < COUNT_OF(default_patterns); i++)
        strlcpy(m->patterns[i], default_patterns[i], OSSM_PATTERN_NAME_LEN);
    m->pattern_count = COUNT_OF(default_patterns);
    strlcpy(m->ossm_name, "OSSM", sizeof(m->ossm_name));
    goto_screen(m, ScreenSplash);

    app->mutex = furi_mutex_alloc(FuriMutexTypeNormal);
    app->queue = furi_message_queue_alloc(16, sizeof(Event));
    app->notify = furi_record_open(RECORD_NOTIFICATION);
    notification_message(app->notify, &sequence_display_backlight_enforce_on);

    ossm_link_start(app);
    ossm_link_send(app, "HI");
    ossm_link_send(app, "SCAN");

    app->view_port = view_port_alloc();
    view_port_draw_callback_set(app->view_port, ossm_ui_draw, app);
    view_port_input_callback_set(app->view_port, input_cb, app);
    app->gui = furi_record_open(RECORD_GUI);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);

    app->timer = furi_timer_alloc(timer_cb, FuriTimerTypePeriodic, app);
    furi_timer_start(app->timer, furi_ms_to_ticks(TICK_MS));

    Event ev;
    bool running = true;
    while(running) {
        if(furi_message_queue_get(app->queue, &ev, FuriWaitForever) != FuriStatusOk) continue;
        furi_mutex_acquire(app->mutex, FuriWaitForever);
        if(ev.type == EvInput) {
            running = handle_input(app, &ev.input);
        } else {
            handle_tick(app);
        }
        furi_mutex_release(app->mutex);
        view_port_update(app->view_port);
    }

    // Leave the machine stopped and parked.
    ossm_link_cmd(app, "set:speed:0");
    ossm_link_cmd(app, "go:menu");
    ossm_link_send(app, "DISC");
    furi_delay_ms(50);

    furi_timer_stop(app->timer);
    furi_timer_free(app->timer);
    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    furi_record_close(RECORD_GUI);

    ossm_link_stop(app);

    notification_message(app->notify, &sequence_reset_rgb);
    notification_message(app->notify, &sequence_display_backlight_enforce_auto);
    furi_record_close(RECORD_NOTIFICATION);
    furi_message_queue_free(app->queue);
    furi_mutex_free(app->mutex);
    free(app);
    return 0;
}
