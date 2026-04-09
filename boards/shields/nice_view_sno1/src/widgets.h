#pragma once

#include <zmk/endpoints.h>
#include <zmk/usb.h>

#include <lvgl.h>

#include "drawing-util.h"

#if defined(CONFIG_ZMK_SPLIT) || IS_ENABLED(CONFIG_DISPLAY_DEMO_MODE)
#define DISPLAYED_BATTERY_COUNT 2
#else
#define DISPLAYED_BATTERY_COUNT 1
#endif

struct widget {
    lv_obj_t *obj;
    int x;
    int target_x;
    int w;
};

////////////////////////////////////////////////////////////////////////////////

enum battery_power_state { BAT_DISCHARGING, BAT_CHARGING, BAT_POWERED };
struct battery_state {
    int8_t percentage;
    enum battery_power_state power_state;
};
struct batteries_state {
    struct battery_state batteries[DISPLAYED_BATTERY_COUNT];
};

#define BATTERY_WIDGET_W 21
#define BATTERY_WIDGET_H 68
void battery_widget_update(struct widget *widget, const struct batteries_state *state);

////////////////////////////////////////////////////////////////////////////////

enum ble_profile_state { BLE_OPEN, BLE_CONNECTED, BLE_BOUND };
struct output_state {
    struct zmk_endpoint_instance selected_endpoint;
    struct zmk_endpoint_instance preferred_endpoint;
    int active_profile_index;
    enum ble_profile_state profile_statuses[CONFIG_TRACKED_PROFILE_COUNT];
    enum zmk_usb_conn_state usb_state;
};

#define OUTPUT_WIDGET_W 64
#define OUTPUT_WIDGET_H 68
void output_widget_update(struct widget *widget, const struct output_state *state);

////////////////////////////////////////////////////////////////////////////////

#define PROFILES_WIDGET_W 26
#define PROFILES_WIDGET_H 68
void profiles_widget_update(struct widget *widget, const struct output_state *state);

////////////////////////////////////////////////////////////////////////////////

struct layer_state {
    uint8_t index;
    const char *label;
};

#define LAYER_WIDGET_W 14
#define LAYER_WIDGET_H 68
void layer_widget_update(struct widget *widget, const struct layer_state *state);

////////////////////////////////////////////////////////////////////////////////

enum on_off_hidden { OFF, ON, HIDDEN };

struct locks_state {
    enum on_off_hidden num_lock;
    enum on_off_hidden caps_lock;
    enum on_off_hidden scroll_lock;
};

#define LOCKS_WIDGET_W 18
#define LOCKS_WIDGET_H 66
void locks_widget_update(struct widget *widget, const struct locks_state *state);

////////////////////////////////////////////////////////////////////////////////

#define CANVAS_WIDGET_INIT(parent, widget, W, H)                                                   \
    {                                                                                              \
        widget.obj = lv_canvas_create(parent);                                                     \
        lv_canvas_set_buffer(widget.obj, widget##_buf, W, H, WIDGET_BUF_FMT);                      \
        widget.w = W;                                                                              \
        widget.x = 0;                                                                              \
    }
#define OBJ_WIDGET_INIT(parent, widget, W, H)                                                      \
    {                                                                                              \
        widget.obj = lv_obj_create(parent);                                                        \
        lv_obj_set_size(widget.obj, W, H);                                                         \
        widget.w = W;                                                                              \
        widget.x = 0;                                                                              \
    }

struct widget_set {
    struct widget batteries_widget;
    lv_color_t batteries_widget_buf[WIDGET_BUF_SIZE(BATTERY_WIDGET_W, BATTERY_WIDGET_H)];

    struct widget output_widget;

    struct widget profiles_widget;
    lv_color_t profiles_widget_buf[WIDGET_BUF_SIZE(PROFILES_WIDGET_W, PROFILES_WIDGET_H)];

    struct widget layer_widget;
    lv_color_t layer_widget_buf[WIDGET_BUF_SIZE(LAYER_WIDGET_W, LAYER_WIDGET_H)];

    struct widget locks_widget;
    lv_color_t locks_widget_buf[WIDGET_BUF_SIZE(LOCKS_WIDGET_W, LOCKS_WIDGET_H)];
};

void setup_widgets(struct widget_set *widgets, lv_obj_t *screen);
void update_main_screen_layout_targets(struct widget_set *widgets);
bool update_main_screen_layout(struct widget_set *widgets, int max_move);
