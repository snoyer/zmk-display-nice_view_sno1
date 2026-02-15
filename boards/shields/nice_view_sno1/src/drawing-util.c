#include "drawing-util.h"
#include <zephyr/kernel.h>

#define draw_text_90_canvas_w 68
#define draw_text_90_canvas_h 26

static uint8_t draw_text_90_canvas_buf[LV_CANVAS_BUF_SIZE(
    draw_text_90_canvas_w, draw_text_90_canvas_h, LV_COLOR_FORMAT_GET_BPP(LV_COLOR_FORMAT_L8),
    LV_DRAW_BUF_STRIDE_ALIGN)];
lv_obj_t *draw_text_90_canvas = NULL;

void canvas_draw_text_90(lv_obj_t *canvas, lv_coord_t x0, lv_coord_t y0, lv_coord_t max_w,
                         lv_draw_label_dsc_t *dsc, const char *text, bool single_line) {

    if (draw_text_90_canvas == NULL) {
        draw_text_90_canvas = lv_canvas_create(NULL);
        lv_canvas_set_buffer(draw_text_90_canvas, draw_text_90_canvas_buf, draw_text_90_canvas_w,
                             draw_text_90_canvas_h, LV_COLOR_FORMAT_L8);
    }

    const lv_color_t tmp_bg = lv_color_white();
    const lv_color_t tmp_fg = lv_color_black();
    lv_obj_t *tmp_canvas = draw_text_90_canvas;

    const lv_color_t color = dsc->color;
    const lv_opa_t opa = dsc->opa;

    dsc->color = tmp_fg;
    dsc->opa = LV_OPA_COVER;
    if (single_line) {
        lv_point_t size;
        lv_text_get_size(&size, text, dsc->font, dsc->letter_space, dsc->line_space, LV_COORD_MAX,
                         dsc->flag);
        max_w = MAX(max_w, size.x);
    }

    lv_canvas_fill_bg(tmp_canvas, tmp_bg, LV_OPA_COVER);

    lv_layer_t layer;
    lv_canvas_init_layer(tmp_canvas, &layer);
    lv_area_t coords = {0, 0, max_w - 1, draw_text_90_canvas_h - 1};
    dsc->text = text;
    lv_draw_label(&layer, dsc, &coords);

    lv_canvas_finish_layer(tmp_canvas, &layer);

    dsc->color = color;
    dsc->opa = opa;

    lv_draw_buf_t *tmp_draw_buf = lv_canvas_get_draw_buf(tmp_canvas);
    lv_draw_buf_t *dst_draw_buf = lv_canvas_get_draw_buf(canvas);

    const int32_t src_w = tmp_draw_buf->header.w;
    const int32_t src_h = tmp_draw_buf->header.h;
    const int32_t dst_w = dst_draw_buf->header.w;
    const int32_t dst_h = dst_draw_buf->header.h;
    const int32_t copy_h = MIN(src_h, dst_w);
    const int32_t copy_w = MIN(src_w, dst_h);
    for (int32_t y = 0; y < copy_h; ++y) {
        for (int32_t x = 0; x < copy_w; ++x) {
            const uint8_t *tmp_px = lv_draw_buf_goto_xy(tmp_draw_buf, x, y);
            if (*tmp_px == 0) {
                const int dst_x = x0 + dst_w - y - 1;
                const int dst_y = y0 + x;
                uint8_t *dst_px = lv_draw_buf_goto_xy(dst_draw_buf, dst_x, dst_y);
#if IS_ENABLED(CONFIG_NICE_VIEW_WIDGET_INVERTED)
                *dst_px = 255;
#else
                *dst_px = 0;
#endif
            }
        }
    }
}

lv_draw_label_dsc_t init_label_dsc(lv_color_t color, const lv_font_t *font, lv_text_align_t align) {
    lv_draw_label_dsc_t label_dsc;
    lv_draw_label_dsc_init(&label_dsc);
    label_dsc.color = color;
    label_dsc.font = font;
    label_dsc.align = align;
    return label_dsc;
}

lv_draw_rect_dsc_t init_rect_dsc(lv_color_t color) {
    lv_draw_rect_dsc_t rect_dsc;
    lv_draw_rect_dsc_init(&rect_dsc);
    rect_dsc.bg_color = color;
    return rect_dsc;
}

void draw_rect(lv_layer_t *layer, lv_coord_t x, lv_coord_t y, lv_coord_t w, lv_coord_t h,
               lv_draw_rect_dsc_t *draw_dsc) {
    const lv_area_t coords = {x, y, x + w - 1, y + h - 1};
    lv_draw_rect(layer, draw_dsc, &coords);
}

void draw_img(lv_layer_t *layer, lv_coord_t x, lv_coord_t y, const lv_image_dsc_t *src) {
    draw_dithered_img(layer, x, y, src, false);
}

void draw_dithered_img(lv_layer_t *layer, lv_coord_t x, lv_coord_t y, const lv_image_dsc_t *src,
               bool greyed_out) {
    lv_draw_image_dsc_t img_dsc;
    lv_draw_image_dsc_init(&img_dsc);

    img_dsc.recolor = LVGL_BG;
#if IS_ENABLED(CONFIG_NICE_VIEW_WIDGET_INVERTED)
    img_dsc.recolor_opa = greyed_out ? 126 : 0;
#else
    img_dsc.recolor_opa = greyed_out ? 127 : 0;
#endif

    img_dsc.src = src;
    lv_area_t coords = {x, y, x + src->header.w - 1, y + src->header.h - 1};
    lv_draw_image(layer, &img_dsc, &coords);
}
