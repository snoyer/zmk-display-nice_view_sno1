#pragma once
#include <zephyr/devicetree.h>
#include <zmk/display.h>

#include <lvgl.h>

#define DISPLAY_WIDTH DT_PROP(DT_CHOSEN(zephyr_display), width)
#define DISPLAY_HEIGHT DT_PROP(DT_CHOSEN(zephyr_display), height)

// TODO figure out how to make it work with 1 bit ?
#define WIDGET_BUF_FMT LV_IMG_CF_TRUE_COLOR
#define WIDGET_BUF_SIZE(w, h) LV_IMG_BUF_SIZE_TRUE_COLOR(w, h)

#define LVGL_BG IS_ENABLED(CONFIG_NICE_VIEW_WIDGET_INVERTED) ? lv_color_black() : lv_color_white()
#define LVGL_FG IS_ENABLED(CONFIG_NICE_VIEW_WIDGET_INVERTED) ? lv_color_white() : lv_color_black()

void canvas_draw_text_90(lv_obj_t *canvas, lv_coord_t x0, lv_coord_t y0, lv_coord_t max_w,
                         lv_draw_label_dsc_t *draw_dsc, const char *text, bool single_line);

lv_draw_img_dsc_t init_img_dsc();
lv_draw_label_dsc_t init_label_dsc(lv_color_t color, const lv_font_t *font, lv_text_align_t align);
lv_draw_rect_dsc_t init_rect_dsc(lv_color_t bg_color);
