/*
 *
 * Copyright (c) 2025 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 */

#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(sno, CONFIG_ZMK_LOG_LEVEL);

#include <zephyr/bluetooth/conn.h>
#include <lvgl.h>

#include <zmk/battery.h>
#include <zmk/display.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/events/endpoint_changed.h>
#include <zmk/events/hid_indicators_changed.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/keymap.h>
#include <zmk/ble.h>
#include <zmk/usb.h>
#include <zmk/hid_indicators.h>

#include "widgets.h"
#include "splash-icons.h" // generated

#if IS_ENABLED(CONFIG_PRINT_LVGL_SNAPSHOTS)
#include "snapshot.h"
#endif

#if IS_ENABLED(CONFIG_DISPLAY_DEMO_MODE)
#include "testing.h"
#include <stdlib.h>
#endif

lv_obj_t *splash_screen;
lv_obj_t *main_screen;
struct widget_set widgets;

#define DISPLAY_WIDGET_LISTENER(listener, state_type, update_func, data_func)                      \
    static void listener##_update_cb(state_type state) { update_func(&widgets, state); }           \
    ZMK_DISPLAY_WIDGET_LISTENER(listener, state_type, listener##_update_cb, data_func)

////////////////////////////////////////////////////////////////////////////////

void setup_splash_screen(lv_obj_t *screen) {
    const int logo_offset = 8;
    const int logo_padding = 6;

    lv_obj_t *logo = lv_img_create(screen);
    lv_img_set_src(logo, &icon_zmk_logo);
    lv_obj_align(logo, LV_ALIGN_CENTER, logo_offset, 0);

    lv_obj_t *txt = lv_img_create(screen);
    lv_img_set_src(txt, &icon_zmk_txt);
    lv_obj_align(
        txt, LV_ALIGN_CENTER,
        logo_offset + icon_zmk_logo.header.w / 2 + icon_zmk_txt.header.w / 2 + logo_padding, 0);

    lv_obj_t *version = lv_img_create(screen);
    lv_img_set_src(version, &icon_app_version);
    lv_obj_align(
        version, LV_ALIGN_CENTER,
        logo_offset - icon_zmk_logo.header.w / 2 - icon_app_version.header.w / 2 - logo_padding, 0);

    lv_obj_t *hash = lv_img_create(screen);
    lv_img_set_src(hash, &icon_git_hash);
    lv_obj_align(hash, LV_ALIGN_LEFT_MID, 2, 0);
}

void hide_splash_screen_cb(struct k_work *work) {
    LOG_DBG("demo_stage = ");
    lv_scr_load(main_screen);
}
static K_WORK_DELAYABLE_DEFINE(hide_splash_screen_work, hide_splash_screen_cb);

////////////////////////////////////////////////////////////////////////////////

void update_layout_cb(struct k_work *work) {
    const bool layout_done = update_main_screen_layout(&widgets);
    if (!layout_done)
        k_work_reschedule(CONTAINER_OF(work, struct k_work_delayable, work), K_MSEC(33));
    LOG_DBG("layout_done = %d", layout_done);
}

#if IS_ENABLED(CONFIG_PRINT_LVGL_SNAPSHOTS)
static void display_draw_event_cb(lv_event_t *e) { print_snapshot(lv_scr_act()); }
#endif

static K_WORK_DELAYABLE_DEFINE(update_layout_work, update_layout_cb);

////////////////////////////////////////////////////////////////////////////////

static void update_layer_state(struct widget_set *widgets, struct layer_state state) {
    layer_widget_update(&widgets->layer_widget, &state);
}

static struct layer_state get_layer_listener_data(const zmk_event_t *event) {
    const zmk_keymap_layer_index_t index = zmk_keymap_highest_layer_active();
    return (struct layer_state){
        .index = index,
        .label = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(index)),
    };
}

DISPLAY_WIDGET_LISTENER(layer_listener, struct layer_state, update_layer_state,
                        get_layer_listener_data)
ZMK_SUBSCRIPTION(layer_listener, zmk_layer_state_changed);

////////////////////////////////////////////////////////////////////////////////

static void update_battery_state(struct widget_set *widgets, struct batteries_state state) {
    battery_widget_update(&widgets->batteries_widget, &state);
}

#if IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING)

struct batteries_state batteries_state;

static struct batteries_state get_battery_listener_data(const zmk_event_t *event) {
    const struct zmk_peripheral_battery_state_changed *peripheral_ev =
        as_zmk_peripheral_battery_state_changed(event);
    if (peripheral_ev != NULL) {
        const uint8_t source = peripheral_ev->source + 1;
        if (source < DISPLAYED_BATTERY_COUNT) {
            batteries_state.batteries[source] = (struct battery_state){
                .percentage = peripheral_ev->state_of_charge,
                // assume 100% means plugged in and charging
                // TODO fix when ZMK has proper API
                .power_state = peripheral_ev->state_of_charge >= 100   ? BAT_CHARGING
                               : peripheral_ev->state_of_charge >= 100 ? BAT_POWERED
                                                                       : BAT_DISCHARGING,
            };
        }
        return batteries_state;
    }

    const struct zmk_battery_state_changed *ev = as_zmk_battery_state_changed(event);

    batteries_state.batteries[0] = (struct battery_state){
        .percentage = (ev != NULL) ? ev->state_of_charge : zmk_battery_state_of_charge(),
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
        // TODO fix when ZMK has proper API
        .power_state = zmk_usb_is_powered()   ? BAT_CHARGING
                       : zmk_usb_is_powered() ? BAT_POWERED
                                              : BAT_DISCHARGING,
#endif // IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    };
    return batteries_state;
}

DISPLAY_WIDGET_LISTENER(battery_listener, struct batteries_state, update_battery_state,
                        get_battery_listener_data)
ZMK_SUBSCRIPTION(battery_listener, zmk_battery_state_changed);
ZMK_SUBSCRIPTION(battery_listener, zmk_peripheral_battery_state_changed);
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
ZMK_SUBSCRIPTION(battery_listener, zmk_usb_conn_state_changed);
#endif // IS_ENABLED(CONFIG_USB_DEVICE_STACK)

#endif // IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING)

////////////////////////////////////////////////////////////////////////////////

static void update_output_state(struct widget_set *widgets, const struct output_state state) {
    output_widget_update(&widgets->output_widget, &state);
    profiles_widget_update(&widgets->profiles_widget, &state);
}

#if IS_ENABLED(CONFIG_ZMK_BLE)

static struct output_state get_output_listener_data(const zmk_event_t *event) {
    struct output_state state = {
        .selected_endpoint = zmk_endpoint_get_selected(),
        .preferred_endpoint = zmk_endpoint_get_preferred(),
        .active_profile_index = zmk_ble_active_profile_index(),
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
        .usb_state = zmk_usb_get_conn_state(),
#endif
    };
    for (int i = 0; i < MIN(CONFIG_TRACKED_PROFILE_COUNT, ZMK_BLE_PROFILE_COUNT); ++i) {
        state.profile_statuses[i] = zmk_ble_profile_is_connected(i) ? BLE_CONNECTED
                                    : zmk_ble_profile_is_open(i)    ? BLE_OPEN
                                                                    : BLE_BOUND;
    }
    return state;
}

DISPLAY_WIDGET_LISTENER(output_listener, struct output_state, update_output_state,
                        get_output_listener_data)
ZMK_SUBSCRIPTION(output_listener, zmk_endpoint_changed);
ZMK_SUBSCRIPTION(output_listener, zmk_ble_active_profile_changed);
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
ZMK_SUBSCRIPTION(output_listener, zmk_usb_conn_state_changed);
#endif

#endif // IS_ENABLED(CONFIG_ZMK_BLE)

////////////////////////////////////////////////////////////////////////////////

struct locks_state current_locks_state = {
    .num_lock = HIDDEN,
    .caps_lock = HIDDEN,
    .scroll_lock = HIDDEN,
};
static int64_t num_lock_timeout_time = 0;
static int64_t caps_lock_timeout_time = 0;
static int64_t scroll_lock_timeout_time = 0;

void update_locks_widget_cb(struct k_work *work) {
    locks_widget_update(&widgets.locks_widget, &current_locks_state);
    update_main_screen_layout_targets(&widgets);
    k_work_reschedule(&update_layout_work, K_MSEC(0));
}
static K_WORK_DELAYABLE_DEFINE(update_locks_widget_work, update_locks_widget_cb);

void hide_off_indicators_cb(struct k_work *work) {
    const int64_t t = k_uptime_get();
    if (current_locks_state.num_lock == OFF && t >= num_lock_timeout_time)
        current_locks_state.num_lock = HIDDEN;
    if (current_locks_state.caps_lock == OFF && t >= caps_lock_timeout_time)
        current_locks_state.caps_lock = HIDDEN;
    if (current_locks_state.scroll_lock == OFF && t >= scroll_lock_timeout_time)
        current_locks_state.scroll_lock = HIDDEN;

    k_work_reschedule(&update_locks_widget_work, K_MSEC(0));
}
static K_WORK_DELAYABLE_DEFINE(hide_timedout_indicators_work1, hide_off_indicators_cb);
static K_WORK_DELAYABLE_DEFINE(hide_timedout_indicators_work2, hide_off_indicators_cb);
static K_WORK_DELAYABLE_DEFINE(hide_timedout_indicators_work3, hide_off_indicators_cb);

static void update_hid_indicators_state(struct widget_set *widgets, struct locks_state state) {
    const int64_t t = k_uptime_get();

    if (state.num_lock == OFF && current_locks_state.num_lock != OFF) {
        num_lock_timeout_time = t + CONFIG_LOCK_ICONS_TIMEOUT;
        k_work_reschedule(&hide_timedout_indicators_work1, K_MSEC(CONFIG_LOCK_ICONS_TIMEOUT));
    }
    if (state.caps_lock == OFF && current_locks_state.caps_lock != OFF) {
        caps_lock_timeout_time = t + CONFIG_LOCK_ICONS_TIMEOUT;
        k_work_reschedule(&hide_timedout_indicators_work2, K_MSEC(CONFIG_LOCK_ICONS_TIMEOUT));
    }
    if (state.scroll_lock == OFF && current_locks_state.scroll_lock != OFF) {
        scroll_lock_timeout_time = t + CONFIG_LOCK_ICONS_TIMEOUT;
        k_work_reschedule(&hide_timedout_indicators_work3, K_MSEC(CONFIG_LOCK_ICONS_TIMEOUT));
    }

    current_locks_state = state;
    k_work_reschedule(&update_locks_widget_work, K_MSEC(0));
}

#if IS_ENABLED(CONFIG_ZMK_HID_INDICATORS)

static struct locks_state get_hid_indicators_listener_data(const zmk_event_t *event) {
    enum on_off_hidden update(bool new, enum on_off_hidden old) {
        return new ? ON : old == ON ? OFF : old;
    }
    const zmk_hid_indicators_t indicators = zmk_hid_indicators_get_current_profile();
    return (struct locks_state){
        .num_lock = update(indicators & BIT(0), current_locks_state.num_lock),
        .caps_lock = update(indicators & BIT(1), current_locks_state.caps_lock),
        .scroll_lock = update(indicators & BIT(2), current_locks_state.scroll_lock),
    };
}

DISPLAY_WIDGET_LISTENER(hid_indicators_listener, struct locks_state, update_hid_indicators_state,
                        get_hid_indicators_listener_data)
ZMK_SUBSCRIPTION(hid_indicators_listener, zmk_hid_indicators_changed);

#endif // IS_ENABLED(CONFIG_ZMK_HID_INDICATORS)

////////////////////////////////////////////////////////////////////////////////

#if IS_ENABLED(CONFIG_DISPLAY_DEMO_MODE)

static int demo_step = 0;
void update_demo_state_cb(struct k_work *work) {
    const struct demo_state demo_state = get_demo_state(demo_step++);
    LOG_DBG("demo_stage = %s", demo_state.group);
    update_battery_state(&widgets, demo_state.batteries_state);
    update_output_state(&widgets, demo_state.output_state);
    update_layer_state(&widgets, demo_state.layer_state);

    num_lock_timeout_time = caps_lock_timeout_time = scroll_lock_timeout_time =
        k_uptime_get() + 1000; // push back icons timeout so they don't get automatically hidden
    update_hid_indicators_state(&widgets, demo_state.locks_state);

    k_work_reschedule(&update_locks_widget_work, K_MSEC(0));
    k_work_reschedule(&update_layout_work, K_MSEC(0));
}
K_WORK_DEFINE(update_demo_state_work, update_demo_state_cb);

void demo_state_timerfunc(struct k_timer *_timer) { k_work_submit(&update_demo_state_work); }
K_TIMER_DEFINE(demo_state_timer, demo_state_timerfunc, NULL);

#endif // IS_ENABLED(CONFIG_DISPLAY_DEMO_MODE)

////////////////////////////////////////////////////////////////////////////////

lv_obj_t *zmk_display_status_screen() {
    main_screen = lv_obj_create(NULL);
    setup_widgets(&widgets, main_screen);

    splash_screen = lv_obj_create(NULL);
    setup_splash_screen(splash_screen);
    k_work_schedule(&hide_splash_screen_work, K_MSEC(CONFIG_SPLASH_SCREEN_TIMEOUT));

    layer_listener_init();
#if IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING)
    battery_listener_init();
#endif
#if IS_ENABLED(CONFIG_ZMK_BLE)
    output_listener_init();
#endif
#if IS_ENABLED(CONFIG_ZMK_HID_INDICATORS)
    hid_indicators_listener_init();
    k_work_reschedule(&hide_timedout_indicators_work1, K_MSEC(CONFIG_LOCK_ICONS_TIMEOUT));
#endif

    // needed to get proper background color on snapshots
    static lv_style_t style;
    lv_style_init(&style);
    lv_style_set_bg_color(&style, LVGL_BG);
    lv_style_set_bg_opa(&style, LV_OPA_COVER);
    lv_obj_add_style(splash_screen, &style, LV_PART_MAIN);
    lv_obj_add_style(main_screen, &style, LV_PART_MAIN);

#if IS_ENABLED(CONFIG_PRINT_LVGL_SNAPSHOTS)
    lv_display_add_event_cb(lv_display_get_default(), display_draw_event_cb, LV_EVENT_REFR_READY,
                            NULL);
#endif

#if IS_ENABLED(CONFIG_DISPLAY_DEMO_MODE)
    srand(123);
    LOG_INF("CONFIG_TRACKED_PROFILE_COUNT = %d", CONFIG_TRACKED_PROFILE_COUNT);
    k_timer_start(&demo_state_timer, K_MSEC(CONFIG_SPLASH_SCREEN_TIMEOUT - 500), K_MSEC(1000));
#endif

    return splash_screen;
}
