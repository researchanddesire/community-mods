#pragma once

#include <furi.h>
#include <furi_hal.h>
#include <gui/gui.h>
#include <input/input.h>
#include <notification/notification_messages.h>

#define OSSM_PATTERN_MAX     12
#define OSSM_PATTERN_NAME_LEN 24
#define OSSM_STATE_LEN       32

typedef enum {
    ScreenSplash,
    ScreenConnect,
    ScreenMode,
    ScreenControl,
} Screen;

typedef enum {
    LinkNoBridge, // this firmware has no BLE central role (needs the OSSM firmware)
    LinkIdle,
    LinkScanning,
    LinkConnecting,
    LinkUp,
} LinkState;

typedef enum {
    ModeStrokeEngine,
    ModeSimple,
} OssmMode;

typedef enum {
    ParamSpeed,
    ParamDepth,
    ParamStroke,
    ParamSensation,
    ParamPattern,
    ParamCount,
} Param;

typedef struct {
    // --- navigation ---
    Screen screen;
    uint32_t screen_since; // tick the current screen was entered
    uint8_t mode_cursor; // 0 stroke engine, 1 simple
    OssmMode mode;
    Param cursor;

    // --- bridge / BLE link ---
    LinkState link;
    bool bridge_seen;
    uint32_t bridge_last_rx;
    int rssi;
    char ossm_name[20];
    uint32_t link_lost_at; // tick a drop was shown, 0 = none

    // --- what the OSSM reports ---
    char ossm_state[OSSM_STATE_LEN];
    int remote_speed;

    // --- what the user wants ---
    int value[ParamCount]; // 0..100, pattern = index
    bool playing;
    int out_speed; // ramped speed actually sent
    int sent[ParamCount]; // last value written, -1 = never
    uint32_t last_send;
    uint32_t last_edit; // tick of last local edit (pauses syncing from OSSM)

    // --- patterns ---
    char patterns[OSSM_PATTERN_MAX][OSSM_PATTERN_NAME_LEN];
    uint8_t pattern_count;
    uint8_t pattern_rx; // patterns received in the current PAT burst

    // --- effects ---
    uint32_t estop_at; // tick the STOP overlay was raised, 0 = none
    float phase; // piston animation phase, radians
    float beat; // heart pulse 0..1
    uint32_t toast_at;
    char toast[24];
} OssmModel;

typedef struct {
    FuriMutex* mutex;
    OssmModel m;

    Gui* gui;
    ViewPort* view_port;
    FuriMessageQueue* queue;
    FuriTimer* timer;
    NotificationApp* notify;

    // Direct BLE link to the OSSM (ossm_ble.c)
    struct OssmBle* ble;
    uint32_t last_ping;
    uint32_t last_hi;
} OssmApp;

// ossm_ble.c: talks straight to the OSSM over Bluetooth, the way RADR does.
// Accepts the same commands the old UART bridge did: "CMD <ossm command>",
// "STOP", "SCAN", "DISC", "PAT?", "ST?" ("PING"/"HI" are ignored).
void ossm_link_start(OssmApp* app);
void ossm_link_stop(OssmApp* app);
void ossm_link_send(OssmApp* app, const char* line);
void ossm_link_cmd(OssmApp* app, const char* fmt, ...);
void ossm_link_poll(OssmApp* app); // parse queued RX lines into the model

// ossm_ui.c
void ossm_ui_draw(Canvas* canvas, void* ctx);
const char* ossm_param_label(Param p);

static inline bool ossm_param_visible(const OssmModel* m, Param p) {
    if(m->mode == ModeSimple) return p == ParamSpeed || p == ParamDepth || p == ParamStroke;
    return true;
}
