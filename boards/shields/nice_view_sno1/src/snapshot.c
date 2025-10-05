
#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(sno, CONFIG_ZMK_LOG_LEVEL);

#include <zephyr/devicetree.h>
#define DISPLAY_X_RES DT_PROP(DT_CHOSEN(zephyr_display), width)
#define DISPLAY_Y_RES DT_PROP(DT_CHOSEN(zephyr_display), height)

#include <lvgl.h>

void print_snapshot(lv_obj_t *screen) {
    const char *SEXTANTS[64] = {" ", "🬞", "🬏", "🬭", "🬇", "🬦", "🬖", "🬵", "🬃", "🬢", "🬓", "🬱", "🬋",
                                "🬩", "🬚", "🬹", "🬁", "🬠", "🬑", "🬯", "🬉", "▐", "🬘", "🬷", "🬅", "🬤",
                                "🬔", "🬳", "🬍", "🬫", "🬜", "🬻", "🬀", "🬟", "🬐", "🬮", "🬈", "🬧", "🬗",
                                "🬶", "🬄", "🬣", "▌", "🬲", "🬌", "🬪", "🬛", "🬺", "🬂", "🬡", "🬒", "🬰",
                                "🬊", "🬨", "🬙", "🬸", "🬆", "🬥", "🬕", "🬴", "🬎", "🬬", "🬝", "█"};

    const lv_img_cf_t fmt = LV_IMG_CF_TRUE_COLOR;
    lv_color_t buf[LV_IMG_BUF_SIZE_TRUE_COLOR(DISPLAY_X_RES, DISPLAY_Y_RES)];
    lv_img_dsc_t img;
    const lv_color_t bg = lv_obj_get_style_bg_color(screen, LV_PART_MAIN);

    const int w = lv_obj_get_width(screen);
    const int h = lv_obj_get_height(screen);

    bool get_px(int x, int y) {
        return (x >= 0 && y >= 0 && x < w && y < h) &&
               lv_img_buf_get_px_color(&img, x, y, bg).full != bg.full;
    }
    if (lv_snapshot_take_to_buf(screen, fmt, &img, buf, sizeof(buf)) != LV_RES_INV) {
        LOG_INF("%dx%d lvgl snapshot...", w, h);
        for (int y = 0; y < h; y += 3) {
            char line[(MAX(DISPLAY_X_RES, DISPLAY_Y_RES) / 2 + 1) * 4] = {0};
            char *line_i = line;
            for (int x = 0; x < w; x += 2) {
                const char *s = SEXTANTS[(get_px(x + 0, y + 0) << 5) + (get_px(x + 1, y + 0) << 4) +
                                         (get_px(x + 0, y + 1) << 3) + (get_px(x + 1, y + 1) << 2) +
                                         (get_px(x + 0, y + 2) << 1) + (get_px(x + 1, y + 2) << 0)];
                while ((*line_i++ = *s++))
                    ;
                line_i--;
            }
            printf("%s\n", line); // LOG_xxx() doesn't work, some characters get mangled
        }
    } else {
        LOG_WRN("snapshot failed");
    }
}
