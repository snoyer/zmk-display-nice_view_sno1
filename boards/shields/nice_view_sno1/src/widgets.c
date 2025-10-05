#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(sno, CONFIG_ZMK_LOG_LEVEL);

#include <stdio.h>

#include "widgets.h"
#include "widget-icons.h" // generated
#include "symbol-fonts.h" // generated
#include "text-fonts.h"   // generated

void setup_widgets(struct widget_set *widgets, lv_obj_t *screen) {
    WIDGET_INIT(screen, widgets->batteries_widget, BATTERY_WIDGET_W, BATTERY_WIDGET_H)
    WIDGET_INIT(screen, widgets->output_widget, OUTPUT_WIDGET_W, OUTPUT_WIDGET_H)
    WIDGET_INIT(screen, widgets->profiles_widget, PROFILES_WIDGET_W, PROFILES_WIDGET_H)
    WIDGET_INIT(screen, widgets->layer_widget, LAYER_WIDGET_W, LAYER_WIDGET_H)
    WIDGET_INIT(screen, widgets->locks_widget, LOCKS_WIDGET_W, LOCKS_WIDGET_H)

    update_main_screen_layout_targets(widgets);
    update_main_screen_layout(widgets);
}

void update_main_screen_layout_targets(struct widget_set *widgets) {
    const int bat_w = widgets->batteries_widget.w;
    const int gap1_ratio = 3;
    const int out_w = widgets->output_widget.w;
    const int gap2_ratio = 1;
    const int prof_w = widgets->profiles_widget.w;
    const int gap3_ratio = 3;
    const int layer_w = widgets->layer_widget.w;
    const int gap4_ratio = widgets->locks_widget.w == 0 ? 0 : 1;
    const int locks_w = widgets->locks_widget.w;

    const int total_gaps = DISPLAY_WIDTH - (bat_w + out_w + prof_w + layer_w + locks_w);
    const int total_gap_ratios = gap1_ratio + gap2_ratio + gap3_ratio + gap4_ratio;
    const int gap1 = total_gaps * gap1_ratio / total_gap_ratios;
    const int gap2 = total_gaps * gap2_ratio / total_gap_ratios;
    const int gap4 = total_gaps * gap4_ratio / total_gap_ratios;
    const int gap3 = total_gaps - gap1 - gap2 - gap4;

    int x = 0;
    x += bat_w + gap1;
    widgets->output_widget.target_x = -x;
    x += out_w + gap2;
    widgets->profiles_widget.target_x = -x;
    x += prof_w + gap3;
    widgets->layer_widget.target_x = -x;
    x += layer_w + gap4;
    widgets->locks_widget.target_x = -x;
}

bool update_main_screen_layout(struct widget_set *widgets) {
    bool update_pos(struct widget * widget) {
        if (widget->x == WIDGET_DUMMY_POS_VAL)
            widget->x = widget->target_x;
        widget->x += CLAMP(widget->target_x - widget->x, -4, +4);
        return widget->x == widget->target_x;
    }

    const bool a = update_pos(&widgets->batteries_widget);
    const bool b = update_pos(&widgets->output_widget);
    const bool c = update_pos(&widgets->profiles_widget);
    const bool d = update_pos(&widgets->layer_widget);
    const bool e = update_pos(&widgets->locks_widget);
    const bool all_done = a && b && c && d && e;

    const lv_align_t align = LV_ALIGN_RIGHT_MID;
    lv_obj_align(widgets->batteries_widget.canvas, align, widgets->batteries_widget.x, 0);
    lv_obj_align(widgets->output_widget.canvas, align, widgets->output_widget.x, 0);
    lv_obj_align(widgets->profiles_widget.canvas, align, widgets->profiles_widget.x, 0);
    lv_obj_align(widgets->layer_widget.canvas, align, widgets->layer_widget.x, 0);
    lv_obj_align(widgets->locks_widget.canvas, align, widgets->locks_widget.x, 0);

    return all_done;
}

////////////////////////////////////////////////////////////////////////////////

void battery_widget_update(struct widget *widget, const struct batteries_state *state) {
    lv_canvas_fill_bg(widget->canvas, LVGL_BG, LV_OPA_COVER);

    lv_draw_rect_dsc_t rect_dsc_fg = init_rect_dsc(LVGL_FG);
    lv_draw_img_dsc_t img_dsc = init_img_dsc();

    const int h = icon_battery.header.h;
    const int w = icon_battery.header.w;
    const int charge_h_max = h - 6;

    void draw_battery(const struct battery_state *bat, const int x, const int y) {
        const int charge_h = (bat->percentage / 100.) * charge_h_max;
        lv_canvas_draw_rect(widget->canvas, x + 4, y + 3, w - 8, charge_h, &rect_dsc_fg);

        lv_canvas_draw_img(widget->canvas, x, y,
                           bat->percentage <= 0 ? &icon_battery_na : &icon_battery, &img_dsc);
        if (bat->power_state == BAT_CHARGING || bat->power_state == BAT_POWERED)
            lv_canvas_draw_img(widget->canvas, x, y, &icon_battery_dither, &img_dsc);
        if (bat->power_state == BAT_CHARGING) {
            const int x2 = x + (w - icon_battery_bolt.header.w) / 2;
            const int y2 = y + (h - icon_battery_bolt.header.h) / 2;
            lv_canvas_draw_img(widget->canvas, x2, y2, &icon_battery_bolt, &img_dsc);
        }
    }

#if DISPLAYED_BATTERY_COUNT == 2 && CONFIG_ZMK_SPLIT_CENTRAL_IS_RIGHT_SIDE
    draw_battery(&state->batteries[0], 0, BATTERY_WIDGET_H - h + 1);
    draw_battery(&state->batteries[1], 0, -1);
#elif DISPLAYED_BATTERY_COUNT == 2
    draw_battery(&state->batteries[0], 0, -1);
    draw_battery(&state->batteries[1], 0, BATTERY_WIDGET_H - h + 1);
#elif DISPLAYED_BATTERY_COUNT == 1
    draw_battery(&state->batteries[0], 0, BATTERY_WIDGET_H / 2 - h / 2);
#endif
}

////////////////////////////////////////////////////////////////////////////////

const lv_img_dsc_t *digit_imgs[10] = {&icon_n0, &icon_n1, &icon_n2, &icon_n3, &icon_n4,
                                      &icon_n5, &icon_n6, &icon_n7, &icon_n8, &icon_n9};

void output_widget_update(struct widget *widget, const struct output_state *state) {
    lv_canvas_fill_bg(widget->canvas, LVGL_BG, LV_OPA_COVER);

    void show_icon(const lv_img_dsc_t *img, int x, int y) {
        const int dx = OUTPUT_WIDGET_W / 2 - img->header.w / 2;
        const int dy = OUTPUT_WIDGET_H / 2 - img->header.h / 2;
        lv_draw_img_dsc_t img_dsc = init_img_dsc();
        lv_canvas_draw_img(widget->canvas, x + dx, y + dy, img, &img_dsc);
    }

    void show_usb_icon(int y) {
        const lv_img_dsc_t *usb_icon =
            state->usb_state == ZMK_USB_CONN_HID ? &icon_endpoint_usb_ok : &icon_endpoint_usb_na;
        show_icon(usb_icon, 0, y);
    }

    void show_ble_icon(int y) {
        const enum ble_profile_state status = state->profile_statuses[state->active_profile_index];
        const lv_img_dsc_t *ble_icon = status == BLE_CONNECTED ? &icon_endpoint_ble_ok
                                       : status == BLE_BOUND   ? &icon_endpoint_ble_na
                                                               : &icon_endpoint_ble_open;
        show_icon(ble_icon, 0, y);

        const int x = ble_icon->header.w / 2;
        int y2 = y + ble_icon->header.h / 2 - 1;
        for (int num = state->active_profile_index + 1; num > 0; num /= 10) {
            const lv_img_dsc_t *num_icon = digit_imgs[num % 10];
            show_icon(num_icon, x - num_icon->header.w / 2, y2 - num_icon->header.h / 2);
            y2 -= num_icon->header.h - 1;
        }
    }

    const int y_usb = -13;
    const int y_ble = +13;
    switch (state->selected_endpoint.transport) {
    case ZMK_TRANSPORT_USB: // draw USB over greyed-out BLE
        show_ble_icon(y_ble);
        show_icon(&icon_endpoint_dither, 0, y_ble);
        show_usb_icon(y_usb);
        break;
    case ZMK_TRANSPORT_BLE: // draw BLE over greyed-out USB
        show_usb_icon(y_usb);
        show_icon(&icon_endpoint_dither, 0, y_usb);
        show_ble_icon(y_ble);
        break;
    default: // draw both greyed-out
        show_usb_icon(y_usb);
        show_icon(&icon_endpoint_dither, 0, y_usb);
        show_ble_icon(y_ble);
        show_icon(&icon_endpoint_dither, 0, y_ble);
        break;
    }
}

////////////////////////////////////////////////////////////////////////////////

void profiles_widget_update(struct widget *widget, const struct output_state *state) {
    lv_canvas_fill_bg(widget->canvas, LVGL_BG, LV_OPA_COVER);

    char str[MIN(CONFIG_TRACKED_PROFILE_COUNT, 9) + 1] = {0};
    uint8_t c = 0;
    for (int i = 0; i < MIN(CONFIG_TRACKED_PROFILE_COUNT, 9); ++i) {
        switch (state->profile_statuses[i]) {
        case BLE_CONNECTED:
            str[c++] = 'A' + i + 1; // font's `A`...`J` is `0`...`9` digits highlighted
            break;
        case BLE_BOUND:
            str[c++] = 'a' + i + 1; // font's `a`...`j` is `0`...`9` digits
            break;
        default:
            break;
        }
    }
    const lv_font_t *font = c < 5 ? &font_profiles_s : &font_profiles_xs;
    lv_draw_label_dsc_t label_dsc = init_label_dsc(LVGL_FG, font, LV_TEXT_ALIGN_CENTER);
    label_dsc.line_space = 2;
    label_dsc.letter_space = c == 5 || c == 9 ? 2 : 3;
    canvas_draw_text_90(widget->canvas, 0, 0, ((lv_canvas_t *)widget->canvas)->dsc.header.h,
                        &label_dsc, str, false);

    const int h = font->line_height;
    widget->w = c == 0 ? 0 : c <= 5 ? h : h * 2 + label_dsc.letter_space;
}

////////////////////////////////////////////////////////////////////////////////

void layer_widget_update(struct widget *widget, const struct layer_state *state) {
    lv_canvas_fill_bg(widget->canvas, LVGL_BG, LV_OPA_COVER);

    lv_draw_label_dsc_t label_dsc =
        init_label_dsc(LVGL_FG, &font_ter_u14b_mod, LV_TEXT_ALIGN_CENTER);
    const int h = ((lv_canvas_t *)widget->canvas)->dsc.header.h;
    if (state->label == NULL || strlen(state->label) == 0) {
        char layer_text[10] = {};
        sprintf(layer_text, "layer %i", state->index);
        canvas_draw_text_90(widget->canvas, 0, 0, h, &label_dsc, layer_text, true);
    } else {
        canvas_draw_text_90(widget->canvas, 0, 0, h, &label_dsc, state->label, true);
    }
}

////////////////////////////////////////////////////////////////////////////////

void locks_widget_update(struct widget *widget, const struct locks_state *state) {
    lv_canvas_fill_bg(widget->canvas, LVGL_BG, LV_OPA_COVER);

    char locks_str[4] = {0};
    uint8_t c = 0;
    if (state->num_lock != HIDDEN)
        locks_str[c++] = state->num_lock == ON ? 'N' : 'n';
    if (state->caps_lock != HIDDEN)
        locks_str[c++] = state->caps_lock == ON ? 'C' : 'c';
    if (state->scroll_lock != HIDDEN)
        locks_str[c++] = state->scroll_lock == ON ? 'S' : 's';

    lv_draw_label_dsc_t label_dsc = init_label_dsc(LVGL_FG, &font_indicators, LV_TEXT_ALIGN_CENTER);
    label_dsc.letter_space = 6;
    canvas_draw_text_90(widget->canvas, 0, 0, ((lv_canvas_t *)widget->canvas)->dsc.header.h,
                        &label_dsc, locks_str, false);

    widget->w = c > 0 ? LOCKS_WIDGET_W : 0;
}
