// All drawing. 128x64, 1-bit. Everything animates off furi_get_tick() and
// the model's phase/beat so screens stay smooth at the 30 fps tick.

#include "ossm_remote.h"
#include "ossm_remote_icons.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

#define PI_F 3.14159265f

static const char* labels[ParamCount] = {"Speed", "Depth", "Stroke", "Sens.", "Pattern"};
static const char* gauge_labels[ParamCount] = {"SPEED", "DEPTH", "STROKE", "SENS", "PAT"};
static const Icon* param_icons[ParamCount] = {
    &I_ic_speed,
    &I_ic_depth,
    &I_ic_stroke,
    &I_ic_sens,
    &I_ic_pattern,
};

const char* ossm_param_label(Param p) {
    return labels[p];
}

static float ease_out(float t) {
    if(t < 0) t = 0;
    if(t > 1) t = 1;
    return 1.0f - (1.0f - t) * (1.0f - t) * (1.0f - t);
}

// ---------- shared bits ----------

static void draw_signal(Canvas* c, int x, int y, int rssi, bool up) {
    // 4 bars, bottom-aligned at y
    int bars = !up ? 0 : rssi > -60 ? 4 : rssi > -70 ? 3 : rssi > -80 ? 2 : 1;
    for(int i = 0; i < 4; i++) {
        int h = 2 + i * 2;
        if(i < bars)
            canvas_draw_box(c, x + i * 3, y - h, 2, h);
        else
            canvas_draw_dot(c, x + i * 3, y - 1);
    }
}

static void draw_header(Canvas* c, const char* title, const OssmModel* m) {
    canvas_set_color(c, ColorBlack);
    canvas_draw_box(c, 0, 0, 128, 11);
    canvas_set_color(c, ColorWhite);
    canvas_set_font(c, FontSecondary);
    canvas_draw_str(c, 15, 8, title);
    draw_signal(c, 116, 9, m->rssi, m->link == LinkUp);
    canvas_set_color(c, ColorBlack);
}

static void draw_toast(Canvas* c, const OssmModel* m) {
    uint32_t age = furi_get_tick() - m->toast_at;
    if(!m->toast_at || age > 900) return;
    canvas_set_font(c, FontPrimary);
    int w = canvas_string_width(c, m->toast) + 12;
    int x = 87 - w / 2;
    // slide up then hold
    int y = 64 - (int)(14 * ease_out(age / 150.0f));
    canvas_set_color(c, ColorWhite);
    canvas_draw_rbox(c, x - 1, y - 1, w + 2, 14, 4);
    canvas_set_color(c, ColorBlack);
    canvas_draw_rbox(c, x, y, w, 12, 3);
    canvas_set_color(c, ColorWhite);
    canvas_draw_str_aligned(c, x + w / 2, y + 6, AlignCenter, AlignCenter, m->toast);
    canvas_set_color(c, ColorBlack);
}

// ---------- splash ----------

static void draw_splash(Canvas* c, const OssmModel* m) {
    uint32_t t = furi_get_tick() - m->screen_since;

    // Wordmark drops in.
    int ly = -22 + (int)(26 * ease_out(t / 450.0f));
    canvas_draw_icon(c, 21, ly, &I_logo);

    // Heartbeat line traces across.
    int base = 48;
    int head = (int)(128 * ease_out((t - 250) / 900.0f));
    if(t < 250) head = 0;
    int prev_y = base;
    for(int x = 0; x <= head && x < 128; x++) {
        int y = base;
        int k = x - 52;
        if(k >= 0 && k < 6) y = base - k * 2; // up
        else if(k >= 6 && k < 14) y = base - 12 + (k - 6) * 3; // down past base
        else if(k >= 14 && k < 18) y = base + 12 - (k - 14) * 3; // back
        else if(k >= 24 && k < 28) y = base - (k - 24); // small bump
        else if(k >= 28 && k < 32) y = base - 4 + (k - 28);
        if(x > 0) canvas_draw_line(c, x - 1, prev_y, x, y);
        prev_y = y;
    }
    if(head > 0 && head < 128) canvas_draw_disc(c, head, prev_y, 2);

    if(t > 1150) {
        // heart lands at the end of the trace and pulses
        int pulse = ((t - 1150) / 180) % 2;
        canvas_set_color(c, ColorWhite);
        canvas_draw_box(c, 112, 42, 16, 12);
        canvas_set_color(c, ColorBlack);
        canvas_draw_icon(c, 116 - pulse, 44 - pulse, &I_heart);
        if(pulse) canvas_draw_icon(c, 117, 44, &I_heart);
    }
    if(t > 900) {
        canvas_set_font(c, FontSecondary);
        canvas_draw_str_aligned(c, 64, 34, AlignCenter, AlignBottom, "wireless remote");
    }
}

// ---------- connect ----------

static void draw_connect(Canvas* c, const OssmModel* m) {
    uint32_t t = furi_get_tick();
    draw_header(c, "Find your OSSM", m);
    canvas_set_color(c, ColorWhite);
    canvas_draw_icon(c, 2, 1, &I_gear_11);
    canvas_set_color(c, ColorBlack);

    if(m->link == LinkNoBridge) {
        // This firmware can't connect out over Bluetooth.
        if((t / 500) % 2) canvas_draw_icon(c, 57, 15, &I_gear_15);
        canvas_set_font(c, FontPrimary);
        canvas_draw_str_aligned(c, 64, 37, AlignCenter, AlignCenter, "Update your Flipper");
        canvas_set_font(c, FontSecondary);
        canvas_draw_str_aligned(c, 64, 50, AlignCenter, AlignCenter, "Install the Full BLE stack");
        canvas_draw_str_aligned(c, 64, 59, AlignCenter, AlignCenter, "to talk to your OSSM");
    } else {
        // Ripples spreading out from the open source gear.
        int cx = 64, cy = 30;
        for(int k = 0; k < 3; k++) {
            int r = (int)((t / 30 + k * 12) % 36);
            if(r > 6 && m->link != LinkUp) canvas_draw_circle(c, cx, cy, r);
        }
        if(m->link == LinkUp) {
            canvas_draw_circle(c, cx, cy, 14);
            canvas_draw_circle(c, cx, cy, 16);
        }
        canvas_set_color(c, ColorWhite);
        canvas_draw_disc(c, cx, cy, 10);
        canvas_set_color(c, ColorBlack);
        canvas_draw_icon(c, cx - 7, cy - 6, &I_gear_15);

        // Mask the bottom so text sits on a clean band.
        canvas_set_color(c, ColorWhite);
        canvas_draw_box(c, 0, 50, 128, 14);
        canvas_set_color(c, ColorBlack);

        char line[40];
        const char* dots = &"..."[2 - (t / 300) % 3];
        switch(m->link) {
        case LinkScanning:
            snprintf(line, sizeof(line), "Searching%s", dots);
            break;
        case LinkConnecting:
            snprintf(line, sizeof(line), "Connecting to %s%s", m->ossm_name, dots);
            break;
        case LinkUp:
            snprintf(line, sizeof(line), "Connected to %s", m->ossm_name);
            break;
        default:
            snprintf(line, sizeof(line), "OK to search again");
            break;
        }
        canvas_set_font(c, FontSecondary);
        canvas_draw_str_aligned(c, 64, 58, AlignCenter, AlignCenter, line);
    }

    if(m->link_lost_at && t - m->link_lost_at < 3000) {
        canvas_set_color(c, ColorWhite);
        canvas_draw_rbox(c, 18, 13, 92, 13, 3);
        canvas_set_color(c, ColorBlack);
        canvas_draw_rframe(c, 18, 13, 92, 13, 3);
        canvas_set_font(c, FontSecondary);
        canvas_draw_str_aligned(c, 64, 19, AlignCenter, AlignCenter, "Connection lost");
    }
}

// ---------- mode select ----------

static void draw_mode_card(Canvas* c, int x, bool sel, const Icon* icon, const char* label, int lift) {
    int y = 14 - lift;
    if(sel) {
        canvas_draw_rbox(c, x, y, 57, 39, 4);
        canvas_set_color(c, ColorWhite);
    } else {
        canvas_draw_rframe(c, x, y, 57, 39, 4);
    }
    canvas_draw_icon(c, x + 16, y + 3, icon);
    canvas_set_font(c, FontSecondary);
    canvas_draw_str_aligned(c, x + 28, y + 33, AlignCenter, AlignCenter, label);
    canvas_set_color(c, ColorBlack);
}

static void draw_mode(Canvas* c, const OssmModel* m) {
    uint32_t t = furi_get_tick();
    canvas_set_font(c, FontPrimary);
    canvas_draw_str_aligned(c, 64, 6, AlignCenter, AlignCenter, "Choose a mode");
    int lift = (int)(1.5f + 1.5f * sinf(t / 220.0f));
    draw_mode_card(c, 4, m->mode_cursor == 0, &I_mode_stroke, "Patterns", m->mode_cursor == 0 ? lift : 0);
    draw_mode_card(c, 66, m->mode_cursor == 1, &I_mode_simple, "Simple", m->mode_cursor == 1 ? lift : 0);
    canvas_set_font(c, FontSecondary);
    canvas_draw_str_aligned(
        c, 64, 60, AlignCenter, AlignCenter,
        m->mode_cursor == 0 ? "Stroke Engine  -  OK to start" : "Simple Penetration  -  OK");
}

// ---------- control ----------

static void draw_gauge(Canvas* c, const OssmModel* m) {
    const int cx = 23, cy = 32, r = 17;
    Param p = m->cursor;
    float frac, target = -1;
    int shown;
    if(p == ParamSpeed) {
        frac = m->out_speed / 100.0f;
        target = m->value[ParamSpeed] / 100.0f;
        shown = m->value[ParamSpeed];
    } else if(p == ParamPattern) {
        int n = m->pattern_count > 1 ? m->pattern_count : 2;
        frac = m->value[p] / (float)(n - 1);
        shown = m->value[p] + 1;
    } else {
        frac = m->value[p] / 100.0f;
        shown = m->value[p];
    }

    // 240 degree arc of ticks, open at the bottom so the label sits clear of it.
    const int ticks = 31;
    for(int i = 0; i < ticks; i++) {
        float f = i / (float)(ticks - 1);
        float a = (150.0f + 240.0f * f) * PI_F / 180.0f;
        int x = cx + (int)roundf(r * cosf(a));
        int y = cy + (int)roundf(r * sinf(a));
        if(f <= frac + 0.001f && frac > 0) {
            canvas_draw_disc(c, x, y, 1);
        } else {
            canvas_draw_dot(c, x, y);
        }
    }
    if(target >= 0) {
        // notch outside the ring marks where speed is heading
        float a = (150.0f + 240.0f * target) * PI_F / 180.0f;
        int x1 = cx + (int)roundf((r + 3) * cosf(a)), y1 = cy + (int)roundf((r + 3) * sinf(a));
        int x2 = cx + (int)roundf((r + 5) * cosf(a)), y2 = cy + (int)roundf((r + 5) * sinf(a));
        canvas_draw_line(c, x1, y1, x2, y2);
    }

    char buf[8];
    if(p != ParamPattern && shown >= 100) {
        canvas_set_font(c, FontPrimary);
        canvas_draw_str_aligned(c, cx, cy, AlignCenter, AlignCenter, "MAX");
    } else {
        snprintf(buf, sizeof(buf), "%d", shown);
        canvas_set_font(c, FontBigNumbers);
        canvas_draw_str_aligned(c, cx, cy, AlignCenter, AlignCenter, buf);
    }
    canvas_set_font(c, FontSecondary);
    canvas_draw_str_aligned(c, cx, cy + 19, AlignCenter, AlignCenter, gauge_labels[p]);
}

static void draw_piston(Canvas* c, const OssmModel* m) {
    // Tiny side view of the machine: body, rail, rod that strokes live.
    const int y = 58;
    canvas_draw_rbox(c, 1, y - 3, 7, 7, 1);
    canvas_draw_line(c, 8, y + 3, 44, y + 3);
    float depth = m->value[ParamDepth], stroke = m->value[ParamStroke];
    if(m->mode == ModeSimple) depth = 100; // simple mode strokes from the back
    float pos = depth - stroke * (0.5f + 0.5f * cosf(m->phase));
    if(pos < 0) pos = 0;
    int tip = 9 + (int)(pos * 33 / 100);
    canvas_draw_box(c, 8, y - 1, tip - 8, 2);
    canvas_draw_disc(c, tip, y, 2);
    // depth limit tick
    int lim = 9 + (int)(depth * 33 / 100);
    canvas_draw_line(c, lim, y + 1, lim, y + 2);
}

static void draw_row(Canvas* c, const OssmModel* m, Param p, int y) {
    bool sel = m->cursor == p;
    if(sel) {
        canvas_draw_rbox(c, 47, y, 81, 10, 2);
        canvas_set_color(c, ColorWhite);
    }
    canvas_draw_icon(c, 50, y + 1, param_icons[p]);
    canvas_set_font(c, FontSecondary);
    if(p == ParamPattern) {
        const char* name = m->patterns[m->value[p] % OSSM_PATTERN_MAX];
        char buf[OSSM_PATTERN_NAME_LEN];
        strlcpy(buf, name, sizeof(buf));
        // trim to fit the row
        while(strlen(buf) > 1 && canvas_string_width(c, buf) > (sel ? 56 : 64))
            buf[strlen(buf) - 1] = 0;
        canvas_draw_str(c, 60, y + 8, buf);
        if(sel) {
            canvas_draw_str(c, 119, y + 8, "<>");
        }
    } else {
        canvas_draw_str(c, 60, y + 8, labels[p]);
        int v = p == ParamSpeed ? m->value[p] : m->value[p];
        canvas_draw_rframe(c, 91, y + 2, 34, 6, 1);
        int w = v * 30 / 100;
        if(w > 0) canvas_draw_box(c, 93, y + 4, w, 2);
        if(p == ParamSpeed && m->playing) {
            // live speed marker inside the bar
            int ow = m->out_speed * 30 / 100;
            canvas_draw_line(c, 93 + ow, y + 3, 93 + ow, y + 6);
        }
    }
    canvas_set_color(c, ColorBlack);
}

static void draw_overlay_card(Canvas* c, const Icon* icon, const char* title, const char* sub) {
    canvas_set_color(c, ColorWhite);
    canvas_draw_rbox(c, 6, 14, 116, 44, 4);
    canvas_set_color(c, ColorBlack);
    canvas_draw_rframe(c, 6, 14, 116, 44, 4);
    canvas_draw_rframe(c, 8, 16, 112, 40, 3);
    if(icon) canvas_draw_icon(c, 14, 26, icon);
    canvas_set_font(c, FontPrimary);
    canvas_draw_str(c, icon ? 36 : 14, 29, title);
    canvas_set_font(c, FontSecondary);
    canvas_draw_str(c, icon ? 36 : 14, 41, sub);
}

static void draw_control(Canvas* c, const OssmModel* m) {
    uint32_t t = furi_get_tick();
    const char* title = m->mode == ModeStrokeEngine ? "STROKE ENGINE" : "SIMPLE";
    draw_header(c, title, m);

    // play / pause glyph, left of the title
    canvas_set_color(c, ColorWhite);
    if(m->playing) {
        canvas_draw_triangle(c, 4, 5, 8, 8, CanvasDirectionLeftToRight);
    } else if((t / 400) % 2 || m->estop_at) {
        canvas_draw_box(c, 3, 2, 2, 7);
        canvas_draw_box(c, 7, 2, 2, 7);
    }
    // heart beats with each stroke
    if(m->playing && m->beat > 0.35f) {
        canvas_draw_icon(c, 104, 1, &I_heart);
    } else if(m->playing) {
        canvas_draw_box(c, 107, 3, 3, 3);
    }
    canvas_set_color(c, ColorBlack);

    draw_gauge(c, m);
    draw_piston(c, m);

    canvas_draw_line(c, 46, 13, 46, 63);
    int y = 13;
    for(int p = 0; p < ParamCount; p++) {
        if(!ossm_param_visible(m, p)) continue;
        draw_row(c, m, p, y);
        y += 10;
    }
    if(m->mode == ModeSimple) {
        canvas_set_font(c, FontSecondary);
        canvas_draw_str(c, 52, 53, "OK  play/pause");
        canvas_draw_str(c, 52, 62, "Back  STOP");
    }

    draw_toast(c, m);

    // Machine-side states that block motion.
    if(strstr(m->ossm_state, "preflight")) {
        draw_overlay_card(c, &I_knob_16, "Knob to zero", "Turn the OSSM's");
        canvas_draw_str(c, 36, 50, "speed knob down");
    } else if(strncmp(m->ossm_state, "homing", 6) == 0) {
        draw_overlay_card(c, NULL, "Homing...", "Finding the ends");
        int w = (int)((t / 8) % 100);
        canvas_draw_rframe(c, 14, 46, 100, 6, 2);
        canvas_draw_box(c, 14 + (w > 80 ? 80 : w), 47, 20, 4);
    } else if(strcmp(m->ossm_state, "error") == 0) {
        draw_overlay_card(c, NULL, "OSSM error", "Check the machine,");
        canvas_draw_str(c, 14, 51, "then hold Back for menu");
    }

    if(m->estop_at) {
        // Full-screen STOP card.
        canvas_draw_box(c, 0, 0, 128, 64);
        canvas_set_color(c, ColorWhite);
        canvas_draw_icon(c, 6, 12, &I_stop_40);
        canvas_set_color(c, ColorBlack);
        canvas_set_font(c, FontPrimary);
        canvas_draw_str_aligned(c, 26, 32, AlignCenter, AlignCenter, "STOP");
        canvas_set_color(c, ColorWhite);
        canvas_draw_str(c, 54, 26, "Stopped");
        canvas_set_font(c, FontSecondary);
        canvas_draw_str(c, 54, 38, "Speed is 0 and");
        canvas_draw_str(c, 54, 47, "OSSM is parked");
        canvas_draw_str(c, 54, 60, "OK to continue");
        canvas_set_color(c, ColorBlack);
    }
}

void ossm_ui_draw(Canvas* canvas, void* ctx) {
    OssmApp* app = ctx;
    furi_mutex_acquire(app->mutex, FuriWaitForever);
    canvas_clear(canvas);
    canvas_set_color(canvas, ColorBlack);
    switch(app->m.screen) {
    case ScreenSplash:
        draw_splash(canvas, &app->m);
        break;
    case ScreenConnect:
        draw_connect(canvas, &app->m);
        break;
    case ScreenMode:
        draw_mode(canvas, &app->m);
        break;
    case ScreenControl:
        draw_control(canvas, &app->m);
        break;
    }
    furi_mutex_release(app->mutex);
}
