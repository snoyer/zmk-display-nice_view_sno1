#pragma once

#include "widgets.h"

struct demo_state {
    char *group;
    struct batteries_state batteries_state;
    struct output_state output_state;
    struct layer_state layer_state;
    struct locks_state locks_state;
};
struct demo_state get_demo_state(int step);
