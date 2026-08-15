#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(sno, CONFIG_ZMK_LOG_LEVEL);

#include <stdio.h>

#include "widgets.h"
#include "widget-icons.h" // generated
#include "symbol-fonts.h" // generated
#include "text-fonts.h"   // generated

void setup_widgets(struct widget_set *widgets, lv_obj_t *screen) {
    CANVAS_WIDGET_INIT(screen, widgets->batteries_widget, BATTERY_WIDGET_W, BATTERY_WIDGET_H)

    OBJ_WIDGET_INIT(screen, widgets->output_widget, OUTPUT_WIDGET_W, OUTPUT_WIDGET_H)
    output_widget_setup(&widgets->output_widget);

    CANVAS_WIDGET_INIT(screen, widgets->profiles_widget, PROFILES_WIDGET_W, PROFILES_WIDGET_H)
    CANVAS_WIDGET_INIT(screen, widgets->layer_widget, LAYER_WIDGET_W, LAYER_WIDGET_H)
    CANVAS_WIDGET_INIT(screen, widgets->locks_widget, LOCKS_WIDGET_W, LOCKS_WIDGET_H)

    update_main_screen_layout_targets(widgets);
    update_main_screen_layout(widgets, 0);
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

bool update_main_screen_layout(struct widget_set *widgets, int max_move) {
    bool update_pos(struct widget * widget) {
        if (max_move < 1)
            widget->x = widget->target_x;
        else
            widget->x += CLAMP(widget->target_x - widget->x, -max_move, +max_move);
        return widget->x == widget->target_x;
    }

    const bool a = update_pos(&widgets->batteries_widget);
    const bool b = update_pos(&widgets->output_widget);
    const bool c = update_pos(&widgets->profiles_widget);
    const bool d = update_pos(&widgets->layer_widget);
    const bool e = update_pos(&widgets->locks_widget);
    const bool all_done = a && b && c && d && e;

    const lv_align_t align = LV_ALIGN_RIGHT_MID;
    lv_obj_align(widgets->batteries_widget.obj, align, widgets->batteries_widget.x, 0);
    lv_obj_align(widgets->output_widget.obj, align, widgets->output_widget.x, 0);
    lv_obj_align(widgets->profiles_widget.obj, align, widgets->profiles_widget.x, 0);
    lv_obj_align(widgets->layer_widget.obj, align, widgets->layer_widget.x, 0);
    lv_obj_align(widgets->locks_widget.obj, align, widgets->locks_widget.x, 0);

    return all_done;
}

////////////////////////////////////////////////////////////////////////////////

void battery_widget_update(struct widget *widget, const struct batteries_state *state) {
    lv_canvas_fill_bg(widget->obj, LVGL_BG, LV_OPA_COVER);

    lv_layer_t layer;
    lv_canvas_init_layer(widget->obj, &layer);

    lv_draw_rect_dsc_t rect_dsc_fg = init_rect_dsc(LVGL_FG);

    const int h = icon_battery.header.h;
    const int w = icon_battery.header.w;
    const int charge_h_max = h - 6;

    void draw_battery(const struct battery_state *bat, const int x, const int y) {
        const int charge_h = (bat->percentage / 100.) * charge_h_max;
        draw_rect(&layer, x + 4, y + 3, w - 8, charge_h, &rect_dsc_fg);

        draw_dithered_img(&layer, x, y, &icon_battery, bat->percentage <= 0);
        if (bat->power_state == BAT_CHARGING || bat->power_state == BAT_POWERED)
            draw_img(&layer, x, y, &icon_battery_dither_mask);
        if (bat->power_state == BAT_CHARGING) {
            const int x2 = x + (w - icon_battery_bolt.header.w) / 2;
            const int y2 = y + (h - icon_battery_bolt.header.h) / 2;
            draw_img(&layer, x2, y2, &icon_battery_bolt);
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

    lv_canvas_finish_layer(widget->obj, &layer);
}

////////////////////////////////////////////////////////////////////////////////

void output_widget_setup(struct widget *widget) {
    const int y_usb = -13;
    const int y_ble = +13;

    lv_obj_t *usb_grp = lv_obj_create(widget->obj);
    lv_obj_add_flag(usb_grp, LV_OBJ_FLAG_USER_1);
    lv_obj_set_size(usb_grp, lv_pct(100), lv_pct(100));
    lv_obj_t *usb_animimg = lv_animimg_create(usb_grp);
    lv_obj_align(usb_animimg, LV_ALIGN_CENTER, 0, y_usb);

    lv_obj_t *ble_grp = lv_obj_create(widget->obj);
    lv_obj_set_size(ble_grp, lv_pct(100), lv_pct(100));
    lv_obj_t *ble_animimg = lv_animimg_create(ble_grp);
    lv_obj_align(ble_animimg, LV_ALIGN_CENTER, 0, y_ble);
    lv_obj_t *ble_img = lv_img_create(ble_grp);
    lv_obj_align(ble_img, LV_ALIGN_BOTTOM_RIGHT, 0, 2);

    lv_obj_t *none_img = lv_img_create(widget->obj);
    lv_obj_align(none_img, LV_ALIGN_CENTER, 0, 0);
}
void output_widget_update(struct widget *widget, const struct output_state *state) {
    const bool usb_grp_at_bottom =
        lv_obj_has_flag(lv_obj_get_child(widget->obj, 0), LV_OBJ_FLAG_USER_1);
    lv_obj_t *usb_grp = lv_obj_get_child(widget->obj, usb_grp_at_bottom ? 0 : 1);
    lv_obj_t *ble_grp = lv_obj_get_child(widget->obj, usb_grp_at_bottom ? 1 : 0);
    lv_obj_t *none_img = lv_obj_get_child(widget->obj, 2);
    lv_obj_t *usb_animimg = lv_obj_get_child(usb_grp, 0);
    lv_obj_t *ble_animimg = lv_obj_get_child(ble_grp, 0);
    lv_obj_t *ble_img = lv_obj_get_child(ble_grp, 1);

    void set_animation(lv_obj_t * animimg, const struct img_dsc_seq *imgs, int frame_duration,
                       bool loop) {
        lv_animimg_set_src(animimg, (const void **)imgs->imgs, imgs->count);
        lv_animimg_set_duration(animimg, imgs->count * frame_duration);
        lv_animimg_set_repeat_count(animimg, loop && imgs->count > 1 ? LV_ANIM_REPEAT_INFINITE : 0);
    }

    {
        const bool active = state->selected_endpoint.transport == ZMK_TRANSPORT_USB;
        const struct img_dsc_seq *a =
            state->usb_state == ZMK_USB_CONN_HID ? &icons_endpoint_usb_ok : &icons_endpoint_usb_na;
        set_animation(usb_animimg, a, 750, false);
        lv_animimg_start(usb_animimg);
        apply_greyout_dither_style(usb_animimg, active);
    }

    {
        const bool active = state->selected_endpoint.transport == ZMK_TRANSPORT_BLE;
        const enum ble_profile_state status = state->profile_statuses[state->active_profile_index];
#if IS_ENABLED(CONFIG_USE_BT_ICON)
        const struct img_dsc_seq *a = status == BLE_CONNECTED ? &icons_endpoint_bt_ok
                                      : status == BLE_BOUND   ? &icons_endpoint_bt_na
                                                              : &icons_endpoint_bt_open;
#else
        const struct img_dsc_seq *a = status == BLE_CONNECTED ? &icons_endpoint_wl_ok
                                      : status == BLE_BOUND   ? &icons_endpoint_wl_na
                                                              : &icons_endpoint_wl_open;
#endif
        const int profile_num = state->active_profile_index + 1;
        const lv_img_dsc_t *num_icon =
            profile_num < 10 ? icons_n.imgs[profile_num % icons_n.count] : NULL;

        const bool same_srcs = lv_animimg_get_src(ble_animimg) == (const void **)a->imgs &&
                               lv_img_get_src(ble_img) == num_icon;

        const bool loop = status == BLE_OPEN;
        const int frame_duration = status == BLE_OPEN ? 750 : 150;
        set_animation(ble_animimg, a, frame_duration, loop);
        if (!same_srcs)
            lv_animimg_start(ble_animimg);

        apply_greyout_dither_style(ble_animimg, active);
        lv_img_set_src(ble_img, num_icon);
        apply_greyout_dither_style(ble_img, active);
    }

    {
        const bool shown = state->preferred_endpoint.transport == ZMK_TRANSPORT_NONE;
        const bool active = state->selected_endpoint.transport == ZMK_TRANSPORT_NONE;
        lv_img_set_src(none_img, shown ? &icon_endpoint_none : NULL);
        apply_greyout_dither_style(none_img, active);
    }

    if ((state->preferred_endpoint.transport == ZMK_TRANSPORT_BLE) ^ usb_grp_at_bottom)
        lv_obj_swap(usb_grp, ble_grp);
}

////////////////////////////////////////////////////////////////////////////////

void profiles_widget_update(struct widget *widget, const struct output_state *state) {
    lv_canvas_fill_bg(widget->obj, LVGL_BG, LV_OPA_COVER);

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
    canvas_draw_text_90(widget->obj, 0, 0, lv_canvas_get_draw_buf(widget->obj)->header.h,
                        &label_dsc, str, false);

    const int h = font->line_height;
    widget->w = c == 0 ? 0 : c <= 5 ? h : h * 2 + label_dsc.letter_space;
}

////////////////////////////////////////////////////////////////////////////////

void layer_widget_update(struct widget *widget, const struct layer_state *state) {
    lv_canvas_fill_bg(widget->obj, LVGL_BG, LV_OPA_COVER);

    lv_draw_label_dsc_t label_dsc =
        init_label_dsc(LVGL_FG, &font_ter_u14b_mod, LV_TEXT_ALIGN_CENTER);
    const int h = lv_canvas_get_draw_buf(widget->obj)->header.h;
    if (state->label == NULL || strlen(state->label) == 0) {
        char layer_text[10] = {};
        sprintf(layer_text, "layer %i", state->index);
        canvas_draw_text_90(widget->obj, 0, 0, h, &label_dsc, layer_text, true);
    } else {
        canvas_draw_text_90(widget->obj, 0, 0, h, &label_dsc, state->label, true);
    }
}

////////////////////////////////////////////////////////////////////////////////

void locks_widget_update(struct widget *widget, const struct locks_state *state) {
    lv_canvas_fill_bg(widget->obj, LVGL_BG, LV_OPA_COVER);

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
    canvas_draw_text_90(widget->obj, 0, 0, lv_canvas_get_draw_buf(widget->obj)->header.h,
                        &label_dsc, locks_str, false);

    widget->w = c > 0 ? LOCKS_WIDGET_W : 0;
}
