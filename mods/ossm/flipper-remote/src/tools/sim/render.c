// Renders each screen of the app to PBM files for review.
#include "../../flipper_app/ossm_remote.h"
#include <stdio.h>
#include <string.h>

uint32_t sim_tick = 0;
Canvas* sim_canvas_alloc(void);
int sim_pixel(Canvas* c, int x, int y);
size_t strlcpy(char* d, const char* s, size_t n) {
    size_t l = strlen(s);
    if(n) { size_t k = l < n - 1 ? l : n - 1; memcpy(d, s, k); d[k] = 0; }
    return l;
}

static OssmApp app;

static void shot(const char* name) {
    Canvas* c = sim_canvas_alloc();
    ossm_ui_draw(c, &app);
    char fn[128];
    snprintf(fn, sizeof(fn), "out/%s.pbm", name);
    FILE* f = fopen(fn, "w");
    fprintf(f, "P1\n128 64\n");
    for(int y = 0; y < 64; y++) {
        for(int x = 0; x < 128; x++) fputc(sim_pixel(c, x, y) ? '1' : '0', f);
        fputc('\n', f);
    }
    fclose(f);
}

static const char* pats[] = {"Simple Stroke", "Teasing Pounding", "Robo Stroke", "Half'n'Half", "Deeper", "Stop'n'Go", "Insist"};

int main(void) {
    OssmModel* m = &app.m;
    for(int i = 0; i < 7; i++) strlcpy(m->patterns[i], pats[i], OSSM_PATTERN_NAME_LEN);
    m->pattern_count = 7;
    strlcpy(m->ossm_name, "OSSM", sizeof(m->ossm_name));

    // splash frames
    m->screen = ScreenSplash; m->screen_since = 1000;
    sim_tick = 1000 + 300; shot("01_splash_a");
    sim_tick = 1000 + 800; shot("02_splash_b");
    sim_tick = 1000 + 1600; shot("03_splash_c");

    m->screen = ScreenConnect; m->screen_since = 5000;
    m->link = LinkNoBridge; sim_tick = 5500; shot("04_no_bridge");
    m->link = LinkScanning; sim_tick = 6210; shot("05_scanning");
    m->link = LinkConnecting; sim_tick = 6800; shot("06_connecting");
    m->link = LinkUp; m->rssi = -58; sim_tick = 7000; shot("07_connected");

    m->screen = ScreenMode; m->mode_cursor = 0; sim_tick = 8000; shot("08_mode_stroke");
    m->mode_cursor = 1; sim_tick = 8300; shot("09_mode_simple");

    m->screen = ScreenControl; m->mode = ModeStrokeEngine;
    m->value[ParamSpeed] = 65; m->value[ParamDepth] = 80; m->value[ParamStroke] = 55;
    m->value[ParamSensation] = 40; m->value[ParamPattern] = 1;
    m->playing = true; m->out_speed = 65; m->cursor = ParamSpeed;
    m->phase = 1.2f; m->beat = 0.8f; sim_tick = 9000; shot("10_control_speed");
    m->cursor = ParamDepth; m->phase = 3.0f; m->beat = 0.1f; shot("11_control_depth");
    m->cursor = ParamPattern; m->phase = 4.5f; shot("12_control_pattern");
    m->playing = false; m->out_speed = 0; m->cursor = ParamSpeed; sim_tick = 9500; shot("13_control_paused");
    m->toast_at = 9400; strlcpy(m->toast, "Paused", sizeof(m->toast)); sim_tick = 9700; shot("14_toast");
    m->toast_at = 0;
    m->mode = ModeSimple; m->playing = true; m->out_speed = 30; m->value[ParamSpeed] = 30; m->phase = 2.0f; m->beat = 0.6f;
    shot("15_control_simple");
    m->mode = ModeStrokeEngine;
    strlcpy(m->ossm_state, "strokeEngine.preflight", OSSM_STATE_LEN); shot("16_preflight");
    strlcpy(m->ossm_state, "homing.forward", OSSM_STATE_LEN); shot("17_homing");
    m->ossm_state[0] = 0;
    m->estop_at = 9600; shot("18_estop");
    return 0;
}
