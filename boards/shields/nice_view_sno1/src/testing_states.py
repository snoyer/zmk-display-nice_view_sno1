import re
from collections import Counter
from collections.abc import Iterable
from itertools import cycle, islice, product
from typing import Literal


def demo_states():
    N = 10

    g = "splash"
    yield state(g, "none", "none", 1, 10, (), ("-1", "-1"), "", "")

    g = "demo"
    yield state(g, "ble", "ble", 1, 1, {1, -2}, ("80+", "-1"), "NCs", "layer 1")
    yield state(g, "usb", "usb", 1, 2, {1, -2}, ("100*", "50"), "nc", "hello world")
    yield state(g, "ble", "ble", 0, 3, {1, -2}, ("80", "60+"), "", "foo bar")

    g = "preferred-vs-selected"
    yield state(g, "ble", "ble", 1, 1, {1}, ("80+", "-1"), "", "ble? ble")
    yield state(g, "ble", "usb", 1, 1, {-1}, ("80+", "-1"), "", "ble? usb")
    yield state(g, "ble", "none", 0, 1, {-1}, ("80", "-1"), "", "ble? none")
    yield state(g, "usb", "ble", 0, 1, {1}, ("80", "-1"), "", "usb? ble")
    yield state(g, "usb", "usb", 1, 1, {1}, ("80+", "-1"), "", "usb? usb")
    yield state(g, "usb", "none", 0, 1, {-1}, ("80", "-1"), "", "usb? none")
    yield state(g, "none", "ble", 0, 1, {1}, ("80", "-1"), "", "none? ble")
    yield state(g, "none", "usb", 1, 1, {1}, ("80+", "-1"), "", "none? usb")
    yield state(g, "none", "none", 1, 1, {1}, ("+80", "-1"), "", "none? none")

    g = "profile-numbers"
    profile_combinations = [
        {1},
        {2, 5},
        {3, 6, 8},
        {4, 7, 8, 9},
        {5, 6, 7, 8, 9},
        {6, 7, 8, 9, 1, 2},
        {7, 8, 9, 1, 2, 3, 4},
        {8, 9, 1, 2, 3, 4, 5, 6},
        {9, 1, 2, 3, 4, 5, 6, 7, 8},
        {10},
    ]
    layers = ["lorem", "ipsum", "dolor", "sit", "amet"]
    for i, profiles, layer in zip(range(N), cycle(profile_combinations), cycle(layers)):
        yield state(g, "ble", "ble", 0, i + 1, profiles, ("-1", "-1"), "", layer)
    for i, profiles, layer in zip(range(N), cycle(profile_combinations), cycle(layers)):
        profiles = {-v for v in profiles}
        yield state(g, "usb", "usb", 1, i + 1, profiles, ("-1", "-1"), "", layer)

    g = "batteries-and-locks"
    batteries = (
        (f"{100 - (i % N) * (100 / (N - 1))}{a}", f"{(i % N) * (100 / (N - 1))}{b}")
        for i, (a, b) in enumerate(cycle(product(" *+", " *+")))
    )
    locks = [
        *("NCS", "ncs", ""),
        *("N", "C", "S", "n", "c", "s"),
        *("NcS", "NCs", "NCs", "NcS", "nCS"),
        *("NC", "CS", "Nc", "nC", "Cs", "Cn"),
    ]
    for bat, lock, layer in islice(zip(cycle(batteries), locks, cycle(layers)), 2 * N):
        yield state(g, "usb", "usb", 1, 10, {-10}, bat, lock, layer)


def state(
    group: str,
    preferred: Literal["usb", "ble", "none"] | str,
    selected: Literal["usb", "ble", "none"] | str,
    usb: bool | Literal[0, 1],
    active_ble: int,
    profiles: Iterable[int],
    bat: tuple[str, ...] = ("80*", "80*"),
    locks: str = "",
    layer: str = "layer 0",
):
    def parse_bat(s: str):
        v = (
            "BAT_POWERED"
            if "*" in s
            else "BAT_CHARGING"
            if "+" in s
            else "BAT_DISCHARGING"
        )
        return f"{{ {int(re.sub(r'^(-?\d+).*', r'\1', s))},{v} }}"

    def parse_lock(c: str):
        return "ON" if c.upper() in locks else "OFF" if c.lower() in locks else "HIDDEN"

    selected_transport = ZMK_TRANSPORTS[selected]
    preferred_transport = ZMK_TRANSPORTS[preferred]
    usb_state = "ZMK_USB_CONN_HID" if usb else "ZMK_USB_CONN_NONE"
    statuses_c = ", ".join(
        f"[{abs(v) - 1}] = {'BLE_CONNECTED' if v > 0 else 'BLE_BOUND'}"
        for v in set(profiles)
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


def fixed_demo_states():
    counter = Counter()
    for state in demo_states():
        if m := re.search(r'.group = "(.+)"', state):
            g = m.group(1)
            yield re.sub(r'.group = "(.+)"', rf'.group = "{g}#{counter[g]}"', state)
            counter[g] += 1
        else:
            yield state


print("struct demo_state test_states[] = {")
print(",".join(fixed_demo_states()))
print("};")
