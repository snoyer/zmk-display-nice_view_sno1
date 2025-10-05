#include "drawing-util.h"
#include <zephyr/kernel.h>

#define draw_text_90_canvas_w 68
#define draw_text_90_canvas_h 26
static uint8_t draw_text_90_canvas_buf[LV_IMG_BUF_SIZE_ALPHA_1BIT(draw_text_90_canvas_w,
                                                                  draw_text_90_canvas_h)];
lv_obj_t *draw_text_90_canvas = NULL;

void canvas_draw_text_90(lv_obj_t *canvas, lv_coord_t x0, lv_coord_t y0, lv_coord_t max_w,
                         lv_draw_label_dsc_t *dsc, const char *text, bool single_line) {

    if (draw_text_90_canvas == NULL) {
        draw_text_90_canvas = lv_canvas_create(NULL);
        lv_canvas_set_buffer(draw_text_90_canvas, draw_text_90_canvas_buf, draw_text_90_canvas_w,
                             draw_text_90_canvas_h, LV_IMG_CF_ALPHA_1BIT);
    }

    const lv_color_t color = dsc->color;
    const lv_opa_t opa = dsc->opa;
    const lv_color_t tmp_bg = lv_color_white();
    const lv_color_t tmp_fg = lv_color_black();

    lv_obj_t *tmp_canvas = draw_text_90_canvas;
    lv_canvas_fill_bg(tmp_canvas, tmp_bg, LV_OPA_COVER);
    dsc->color = tmp_fg;
    dsc->opa = LV_OPA_COVER;
    if (single_line) {
        lv_point_t size;
        lv_txt_get_size(&size, text, dsc->font, dsc->letter_space, dsc->line_space, LV_COORD_MAX,
                        dsc->flag);
        max_w = MAX(max_w, size.x);
    }
    lv_canvas_draw_text(tmp_canvas, 0, 0, max_w, dsc, text);
    dsc->color = color;
    dsc->opa = opa;

    lv_img_dsc_t *tmp_img = lv_canvas_get_img(tmp_canvas);
    lv_img_dsc_t *dst_img = lv_canvas_get_img(canvas);

    const int32_t src_w = draw_text_90_canvas_w;
    const int32_t src_h = draw_text_90_canvas_h;
    const int32_t dst_w = ((lv_canvas_t *)canvas)->dsc.header.w;
    const int32_t dst_h = ((lv_canvas_t *)canvas)->dsc.header.h;
    const int32_t copy_h = MIN(src_h, dst_w);
    const int32_t copy_w = MIN(src_w, dst_h);
    for (int32_t y = 0; y < copy_h; ++y) {
        for (int32_t x = 0; x < copy_w; ++x) {
            if (lv_img_buf_get_px_alpha(tmp_img, x, y) == LV_OPA_COVER) {
                const int dst_x = x0 + dst_w - y - 1;
                const int dst_y = y0 + x;
                lv_img_buf_set_px_color(dst_img, dst_x, dst_y, color);
                // lv_img_buf_set_px_alpha(dst_img, dst_x, dst_y, opa);
            }
        }
    }
}

lv_draw_img_dsc_t init_img_dsc() {
    lv_draw_img_dsc_t img_dsc;
    lv_draw_img_dsc_init(&img_dsc);
    return img_dsc;
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
