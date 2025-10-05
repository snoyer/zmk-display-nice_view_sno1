#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(sno, CONFIG_ZMK_LOG_LEVEL);

#include <lvgl.h>
#include <zmk/endpoints.h>

#include <stdlib.h>

#include "testing.h"
#include "testing_states.h"

struct demo_state get_demo_state(int step) {
    switch (step) {
    case 0 ... sizeof(test_states) / sizeof(struct demo_state) - 1:
        return test_states[step];

    default:
        struct demo_state state = {
            .group = "random",
            .output_state = {.usb_state = rand() % 2 ? ZMK_USB_CONN_HID : ZMK_USB_CONN_POWERED,
                             .active_profile_index = rand() % CONFIG_TRACKED_PROFILE_COUNT,
                             .selected_endpoint.transport = rand() % 2},
            .locks_state = {rand() % 3, rand() % 3, rand() % 3},
        };
        for (int j = 0; j < CONFIG_TRACKED_PROFILE_COUNT; ++j)
            state.output_state.profile_statuses[j] = rand() % 3;
        for (int i = 0; i < DISPLAYED_BATTERY_COUNT; ++i) {
            state.batteries_state.batteries[i].power_state = rand() % 3;
            state.batteries_state.batteries[i].percentage = rand() % 100;
        }
        return state;
    }
}
