import re
from argparse import ArgumentParser
from itertools import cycle, islice, product
from random import Random
from typing import Counter, Literal


def demo_states(CONFIG_TRACKED_PROFILE_COUNT: int):
    g = "splash"
    yield state(g, "ble", "ble", 1, 1, {0: 1, 1: -1}, ("80+", "-1"), "NCs", "layer 1")

    g = "demo"
    yield state(g, "ble", "ble", 1, 1, {0: 1, 1: -1}, ("80+", "-1"), "NCs", "layer 1")
    yield state(
        g, "usb", "usb", 1, 2, {0: 1, 1: -1}, ("100*", "50"), "nc", "hello world"
    )
    yield state(g, "ble", "ble", 0, 3, {0: 1, 1: -1}, ("80", "60+"), "", "foo bar")

    g = "preferred-vs-selected"
    yield state(g, "ble", "ble", 1, 1, {0: 1}, ("80+", "-1"), "", "ble? ble")
    yield state(g, "ble", "usb", 1, 1, {0: -1}, ("80+", "-1"), "", "ble? usb")
    yield state(g, "ble", "none", 0, 1, {0: -1}, ("80", "-1"), "", "ble? none")
    yield state(g, "usb", "ble", 0, 1, {0: 1}, ("80", "-1"), "", "usb? ble")
    yield state(g, "usb", "usb", 1, 1, {0: 1}, ("80+", "-1"), "", "usb? usb")
    yield state(g, "usb", "none", 0, 1, {0: -1}, ("80", "-1"), "", "usb? none")
    yield state(g, "none", "ble", 0, 1, {0: 1}, ("80", "-1"), "", "none? ble")
    yield state(g, "none", "usb", 1, 1, {0: 1}, ("80+", "-1"), "", "none? usb")
    yield state(g, "none", "none", 1, 1, {0: 1}, ("+80", "-1"), "", "none? none")

    rnd = Random(123)

    N = CONFIG_TRACKED_PROFILE_COUNT

    def profiles_all(i: int, n: int = N):
        return {i: 1 for i in range(i + 1)}

    def profiles_rnd(i: int, n: int = N):
        s = {j: rnd.choice([+1, -1, 0]) for j in range(n)}
        s[i] = (i % 3) - 1
        return s

    endpoints = [
        *(("ble", "ble", (i % 2) == 0, i + 1, profiles_all(i)) for i in range(N)),
        *(("ble", "ble", (i % 2) == 0, i + 1, profiles_rnd(i)) for i in range(N)),
        *(("usb", "usb", (i % 2) == 1, i + 1, profiles_rnd(i)) for i in range(N)),
    ]
    batteries = (
        (f"{rnd.randint(1, 100)}{a}", f"{(i % N) * (100 / (N - 1))}{b}")
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
    preferred: Literal["usb", "ble", "none"] | str,
    selected: Literal["usb", "ble", "none"] | str,
    usb: bool | Literal[0, 1],
    active_ble: int,
    profiles: dict[int, int],
    bat: tuple[str, ...] = ("80*", "80*"),
    locks: str = "",
    layer: str = "layer 0",
):
    def parse_bat(s: str):
        return f"{{ {int(re.sub(r'^(-?\d+).*', r'\1', s))},{
            (
                'BAT_POWERED'
                if '*' in s
                else 'BAT_CHARGING'
                if '+' in s
                else 'BAT_DISCHARGING'
            )
        } }}"

    def parse_lock(c: str):
        return "ON" if c.upper() in locks else "OFF" if c.lower() in locks else "HIDDEN"

    selected_transport = ZMK_TRANSPORTS[selected]
    preferred_transport = ZMK_TRANSPORTS[preferred]
    usb_state = "ZMK_USB_CONN_HID" if usb else "ZMK_USB_CONN_NONE"
    statuses_c = ", ".join(
        f"[{k}] = {'BLE_CONNECTED' if v > 0 else 'BLE_BOUND'}"
        for k, v in profiles.items()
        if v != 0
    )
    return f"""
    {{
    .group = "{group}",
    .batteries_state = {{{{ {", ".join(map(parse_bat, bat))} }}}},
    .output_state = {{.selected_endpoint = {{.transport = {selected_transport} }},
                      .preferred_endpoint = {{.transport = {preferred_transport} }},
                      .active_profile_index = {active_ble - 1},
                      .profile_statuses = {{ {statuses_c} }},
                      .usb_state = {usb_state} }},
    .layer_state = {{.label = "{layer}" }},
    .locks_state = {{ {", ".join(map(parse_lock, "ncs"))} }}
    }}"""


ZMK_TRANSPORTS = {
    "ble": "ZMK_TRANSPORT_BLE",
    "usb": "ZMK_TRANSPORT_USB",
    "none": "ZMK_TRANSPORT_NONE",
}

argparser = ArgumentParser()
argparser.add_argument("--CONFIG_TRACKED_PROFILE_COUNT", type=int)
args = argparser.parse_args()


def fixed_demo_states():
    counter = Counter()
    for state in demo_states(args.CONFIG_TRACKED_PROFILE_COUNT):
        if m := re.search(r'.group = "(.+)"', state):
            g = m.group(1)
            yield re.sub(r'.group = "(.+)"', rf'.group = "{g}#{counter[g]}"', state)
            counter[g] += 1
        else:
            yield state


print("struct demo_state test_states[] = {")
print(",".join(fixed_demo_states()))
print("};")
