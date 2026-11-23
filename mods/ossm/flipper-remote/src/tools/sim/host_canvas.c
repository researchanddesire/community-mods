// Minimal Canvas implementation on top of u8g2, mirroring the Flipper's
// applications/services/gui/canvas.c closely enough for screenshots.
#include <gui/gui.h>
#include <stdio.h>
#include "u8g2.h"

struct Canvas { u8g2_t fb; };
static uint8_t buf[128 * 64 / 8];

static const u8x8_display_info_t info = {
    .chip_enable_level = 0, .chip_disable_level = 1, .post_chip_enable_wait_ns = 0,
    .pre_chip_disable_wait_ns = 0, .reset_pulse_width_ms = 0, .post_reset_wait_ms = 0,
    .sda_setup_time_ns = 0, .sck_pulse_width_ns = 0, .sck_clock_hz = 4000000UL,
    .spi_mode = 0, .i2c_bus_clock_100kHz = 4, .data_setup_time_ns = 0,
    .write_pulse_width_ns = 0, .tile_width = 16, .tile_height = 8,
    .default_x_offset = 0, .flipmode_x_offset = 0, .pixel_width = 128, .pixel_height = 64};

static uint8_t d_cb(u8x8_t* u8x8, uint8_t msg, uint8_t a, void* p) {
    (void)a; (void)p;
    if(msg == U8X8_MSG_DISPLAY_SETUP_MEMORY) u8x8_d_helper_display_setup_memory(u8x8, &info);
    return 1;
}
static uint8_t nop_cb(u8x8_t* u8x8, uint8_t msg, uint8_t a, void* p) {
    (void)u8x8; (void)msg; (void)a; (void)p; return 1;
}

Canvas* sim_canvas_alloc(void) {
    static Canvas c;
    u8g2_SetupDisplay(&c.fb, d_cb, u8x8_cad_001, nop_cb, nop_cb);
    u8g2_SetupBuffer(&c.fb, buf, 8, u8g2_ll_hvline_vertical_top_lsb, U8G2_R0);
    u8g2_InitDisplay(&c.fb);
    u8g2_SetBitmapMode(&c.fb, 1);
    return &c;
}

int sim_pixel(Canvas* c, int x, int y) {
    (void)c;
    return (buf[(y / 8) * 128 + x] >> (y % 8)) & 1;
}

void canvas_clear(Canvas* c) { u8g2_ClearBuffer(&c->fb); }
void canvas_set_color(Canvas* c, Color color) { u8g2_SetDrawColor(&c->fb, color); }
void canvas_set_font(Canvas* c, Font f) {
    u8g2_SetFontMode(&c->fb, 1);
    if(f == FontPrimary) u8g2_SetFont(&c->fb, u8g2_font_helvB08_tr);
    else if(f == FontSecondary) u8g2_SetFont(&c->fb, u8g2_font_haxrcorp4089_tr);
    else if(f == FontKeyboard) u8g2_SetFont(&c->fb, u8g2_font_profont11_mr);
    else u8g2_SetFont(&c->fb, u8g2_font_profont22_tn);
}
void canvas_draw_str(Canvas* c, int32_t x, int32_t y, const char* s) { u8g2_DrawStr(&c->fb, x, y, s); }
void canvas_draw_str_aligned(Canvas* c, int32_t x, int32_t y, Align h, Align v, const char* s) {
    if(h == AlignRight) x -= u8g2_GetUTF8Width(&c->fb, s);
    else if(h == AlignCenter) x -= u8g2_GetUTF8Width(&c->fb, s) / 2;
    if(v == AlignTop) y += u8g2_GetAscent(&c->fb);
    else if(v == AlignCenter) y += u8g2_GetAscent(&c->fb) / 2;
    u8g2_DrawUTF8(&c->fb, x, y, s);
}
uint16_t canvas_string_width(Canvas* c, const char* s) { return u8g2_GetStrWidth(&c->fb, s); }
void canvas_draw_box(Canvas* c, int32_t x, int32_t y, size_t w, size_t h) { u8g2_DrawBox(&c->fb, x, y, w, h); }
void canvas_draw_rbox(Canvas* c, int32_t x, int32_t y, size_t w, size_t h, size_t r) { u8g2_DrawRBox(&c->fb, x, y, w, h, r); }
void canvas_draw_frame(Canvas* c, int32_t x, int32_t y, size_t w, size_t h) { u8g2_DrawFrame(&c->fb, x, y, w, h); }
void canvas_draw_rframe(Canvas* c, int32_t x, int32_t y, size_t w, size_t h, size_t r) { u8g2_DrawRFrame(&c->fb, x, y, w, h, r); }
void canvas_draw_line(Canvas* c, int32_t x1, int32_t y1, int32_t x2, int32_t y2) { u8g2_DrawLine(&c->fb, x1, y1, x2, y2); }
void canvas_draw_circle(Canvas* c, int32_t x, int32_t y, size_t r) { u8g2_DrawCircle(&c->fb, x, y, r, U8G2_DRAW_ALL); }
void canvas_draw_disc(Canvas* c, int32_t x, int32_t y, size_t r) { u8g2_DrawDisc(&c->fb, x, y, r, U8G2_DRAW_ALL); }
void canvas_draw_dot(Canvas* c, int32_t x, int32_t y) { u8g2_DrawPixel(&c->fb, x, y); }
void canvas_draw_icon(Canvas* c, int32_t x, int32_t y, const Icon* icon) {
    int stride = (icon->w + 7) / 8;
    for(int j = 0; j < icon->h; j++)
        for(int i = 0; i < icon->w; i++)
            if(icon->data[j * stride + i / 8] & (1 << (i % 8)))
                if(x + i >= 0 && x + i < 128 && y + j >= 0 && y + j < 64)
                    u8g2_DrawPixel(&c->fb, x + i, y + j);
}
void canvas_draw_triangle(Canvas* c, int32_t x, int32_t y, size_t base, size_t height, CanvasDirection dir) {
    if(dir == CanvasDirectionLeftToRight) {
        canvas_draw_line(c, x, y - base / 2, x, y + base / 2);
        canvas_draw_line(c, x, y - base / 2, x + height - 1, y);
        canvas_draw_line(c, x + height - 1, y, x, y + base / 2);
    }
}
