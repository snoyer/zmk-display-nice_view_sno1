from argparse import ArgumentParser
import re
from itertools import cycle, islice, product
from random import Random


def demo_states(CONFIG_TRACKED_PROFILE_COUNT: int):
    g = "demo"
    yield state(g, "bt0", "usb", {0: 1, 1: -1}, ("80+", "-1"), "NCs", "layer 1")
    yield state(g, "usb", "bt1", {0: 1, 1: -1}, ("100*", "50"), "nc", "hello world")
    yield state(g, "bt2", "!usb", {0: 1, 1: -1}, ("80", "60+"), "", "foo bar")

    rnd = Random(123)

    N = CONFIG_TRACKED_PROFILE_COUNT

    def profiles_all(i: int, n: int = N):
        return {i: 1 for i in range(i + 1)}

    def profiles_rnd(i: int, n: int = N):
        s = {j: rnd.choice([+1, -1, 0]) for j in range(n)}
        s[i] = (i % 3) - 1
        return s

    endpoints = [
        *((f"bt{i}", "!usb" if i % 2 else "usb", profiles_all(i)) for i in range(N)),
        *((f"bt{i}", "!usb" if i % 2 else "usb", profiles_rnd(i)) for i in range(N)),
        *(("usb" if i % 2 else "!usb", f"bt{i}", profiles_rnd(i)) for i in range(N)),
    ]
    batteries = (
        (f"{rnd.randint(1,100)}{a}", f"{(i%N)*(100/(N-1))}{b}")
        for i, (a, b) in enumerate(cycle(product(" *+", " *+")))
    )
    locks = ["".join(x) for x in product("Nn ", "Cc ", "Ss ")]
    layers = "layer 0", "qwerty", "numpad", "foo", "bar", "baz", "lorem", "ipsum"

    for e, bat, locks, layer in islice(
        zip(cycle(endpoints), cycle(batteries), cycle(locks), cycle(layers)), N * 3
    ):
        yield state("test", *e, bat, locks, layer)


def state(
    group: str,
    endpoint1: str,
    endpoint2: str,
    profiles: dict[int, int],
    bat: tuple[str, ...] = ("80*", "80*"),
    locks: str = "",
    layer: str = "layer 0",
):
    def parse_bat(s: str):
        return f'{{ {int(re.sub(r"^(-?\d+).*", r"\1", s))},{(
            "BAT_POWERED"
            if "*" in s
            else "BAT_CHARGING" if "+" in s else "BAT_DISCHARGING"
        )} }}'

    def parse_lock(c: str):
        return "ON" if c.upper() in locks else "OFF" if c.lower() in locks else "HIDDEN"

    transport = "ZMK_TRANSPORT_BLE" if "bt" in endpoint1 else "ZMK_TRANSPORT_USB"
    bt_endpoint = endpoint1 if "bt" in endpoint1 else endpoint2
    usb_endpoint = endpoint1 if "usb" in endpoint1 else endpoint2
    usb = "ZMK_USB_CONN_NONE" if "!" in usb_endpoint else "ZMK_USB_CONN_HID"
    statuses_c = ", ".join(
        f'[{k}] = {"BLE_CONNECTED" if v > 0 else "BLE_BOUND"}'
        for k, v in profiles.items()
        if v != 0
    )
    return f"""
    {{
    .group = "{group}",
    .batteries_state = {{{{ {", ".join(map(parse_bat, bat))} }}}},
    .output_state = {{.selected_endpoint = {{.transport = {transport} }},
                      .active_profile_index = {int(re.sub(r"\D", "", bt_endpoint))},
                      .profile_statuses = {{ {statuses_c} }},
                      .usb_state = {usb} }},
    .layer_state = {{.label = "{layer}" }},
    .locks_state = {{ {", ".join(map(parse_lock, "ncs"))} }}
    }}"""


argparser = ArgumentParser()
argparser.add_argument("--CONFIG_TRACKED_PROFILE_COUNT", type=int)
args = argparser.parse_args()

print("struct demo_state test_states[] = {")
print(",".join(demo_states(args.CONFIG_TRACKED_PROFILE_COUNT)))
print("};")
