from __future__ import annotations

import re
import shutil
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import datetime
from itertools import count, groupby
from math import ceil
from os import isatty
from pathlib import Path
from tempfile import gettempdir
from typing import Counter, Sequence, cast

from PIL import Image, ImageDraw, ImageOps

SUCCESS = "✔"
FAILURE = "✘"
WARNING = "⚠"


def main():
    timestamp_extractor = TimestampExtractor()
    snapshot_extractor = SnapshotExtractor()
    varible_extractor = VariableExtractor()

    all_snapshots: list[Snapshot] = []
    display_state = ""

    for line in sys.stdin if not isatty(0) else [""]:
        print(line, end="")

        timestamp_extractor(line)
        varible_extractor(line)
        snapshot_extractor(line)

        for im in snapshot_extractor.pop_snapshot_images():
            snapshot = Snapshot(
                ImageOps.invert(im.rotate(90, expand=True)),
                is_transition=not bool(
                    int(varible_extractor.variables.get("layout_done", "1"))
                ),
                time=timestamp_extractor.seconds,
            )
            snapshot.state = display_state
            if not all_snapshots or snapshot != all_snapshots[-1]:
                print(snapshot)
                all_snapshots.append(snapshot)

        if m := re.search(r"prev display state:\s*(.*)", line):
            if all_snapshots:
                all_snapshots[-1].state = str(m.group(1))
        elif m := re.search(r"display state:\s*(.*)", line):
            display_state = str(m.group(1))

    columns = int(varible_extractor.variables.get("CONFIG_TRACKED_PROFILE_COUNT", 5))
    padding = 16

    success = True

    TMP_DIR = Path(gettempdir())
    ALL_SNAPSHOTS_DIR = TMP_DIR / "all-snapshots"

    if ALL_SNAPSHOTS_DIR.is_dir():
        shutil.rmtree(ALL_SNAPSHOTS_DIR)
    ALL_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(all_snapshots):
        fn = (
            ALL_SNAPSHOTS_DIR
            / f"{i:04d}-{s.group}#{s.step}{'~' if s.is_transition else ''}.png"
        )
        s.image.save(fn)

    counter = Counter()
    for group, snapshots_by_group in groupby(all_snapshots, key=lambda s: s.group):
        if not group:
            continue

        key = f"{group}({counter[group]})" if group in counter else group
        counter[group] += 1

        if key and not key.startswith("["):
            key = f"[{key}]"

        snapshots_by_step: list[list[Snapshot]] = []
        for _step, snapshots in groupby(snapshots_by_group, key=lambda s: s.step):
            snapshots = list(snapshots)
            while snapshots and snapshots[0].is_transition:
                snapshots.pop(0)
            while snapshots and snapshots[-1].is_transition:
                snapshots.pop(-1)
            if snapshots:
                t0 = snapshots[0].time
                snapshots_by_step.append(
                    [replace(s, time=s.time - t0) for s in snapshots]
                )

        nontransition_images = [snapshots[0].image for snapshots in snapshots_by_step]
        collated_im = collate_images(
            nontransition_images, "LA", columns=columns, padding=padding
        )

        collated_im.save(TMP_DIR / f"snapshots{key}.png")

        ref_path = Path(__file__).parent / "expected" / f"snapshots{key}.png"
        if ref_path.is_file():
            old_im = Image.open(ref_path).convert("LA")
            if old_im.size == collated_im.size:
                collated_im, diff_count = image_diff(collated_im, old_im)
                if diff_count:
                    print(FAILURE, key, f"({diff_count} pixels difference)")
                    success = False
                else:
                    print(SUCCESS, key)
            else:
                print(WARNING, key, "(different size)")
        else:
            print(WARNING, key, "(no reference)")

        apply_pixel_grid(collated_im).save(TMP_DIR / f"snapshots{key}.diff.png")

    return 0 if success else 1


def image_diff(new_im: Image.Image, old_im: Image.Image):
    diff = new_im.convert("RGBA")
    w, _h = diff.size
    diff_count = 0

    old_data = cast(Iterable[int], old_im.convert("L").getdata())
    new_data = cast(Iterable[int], new_im.convert("L").getdata())
    for i, (old_px, new_px) in enumerate(zip(old_data, new_data)):
        if old_px != new_px:
            color = (155, 155, 255, 255) if new_px > old_px else (100, 0, 0, 255)
            diff.putpixel((i % w, i // w), color)
            diff_count += 1

    return diff, diff_count


def collate_images(
    images: list[Image.Image], mode: str, columns: int, padding: int = 0
):
    w = max(im.size[0] for im in images)
    h = max(im.size[1] for im in images)

    nx = min(columns, len(images))
    ny = int(ceil(len(images) / nx))

    dst_im = Image.new(mode, (nx * (w + padding), ny * (h + padding)))
    for i, im in enumerate(images):
        x = padding // 2 + (w + padding) * (i % nx)
        y = padding // 2 + (h + padding) * (i // nx)
        ox = (w - im.size[0]) // 2
        oy = (h - im.size[1]) // 2
        dst_im.paste(im, (x + ox, y + oy))
    return dst_im


def parse_timestamp(ts: str):
    return datetime.strptime(ts[:-4], "%H:%M:%S.%f")


@dataclass
class TimestampExtractor:
    timestamp: datetime = parse_timestamp("00:00:00.000,000")
    T0 = parse_timestamp("00:00:00.000,000")

    def __call__(self, line: str):
        if m := re.match(r"\[([0-9.,:]+)\]", line):
            self.timestamp = parse_timestamp(m.group(1))

    @property
    def seconds(self):
        d = self.timestamp - self.T0
        return d.seconds + d.microseconds / 1_000_000


@dataclass
class VariableExtractor:
    variables: dict[str, str] = field(default_factory=dict)

    def __call__(self, line: str):
        for k, v in re.findall(r"([\S=]+)\s*=\s*(.+)", line):
            self.variables[k] = v.strip()


@dataclass
class SnapshotExtractor:
    snapshot_images: list[Image.Image] = field(default_factory=list)
    _tmp_image: Image.Image | None = None
    _tmp_lines_remaining: int = 0

    def __call__(self, line: str):
        line = line.strip("\r\n")
        if m := re.search(r": (\d+)x(\d+) lvgl snapshot", line):
            self._save_snapshot()
            self._tmp_image = Image.new("L", (int(m.group(1)), int(m.group(2))))
            self._tmp_lines_remaining = self._tmp_image.size[1]
        elif self._tmp_image:
            _w, h = self._tmp_image.size
            if self._tmp_lines_remaining > 0:
                im = image_from_sextants([line])
                self._tmp_image.paste(im, (0, h - self._tmp_lines_remaining))
                self._tmp_lines_remaining -= 3
            else:
                self._save_snapshot()

    def pop_snapshot_images(self):
        ims = self.snapshot_images[:]
        self.snapshot_images.clear()
        return ims

    def _save_snapshot(self):
        if im := self._tmp_image:
            self.snapshot_images.append(im)
        self._tmp_image = None


@dataclass
class Snapshot:
    image: Image.Image
    group: str = ""
    step: int = 0
    is_transition: bool = False
    time: float = 0.0

    @property
    def state(self):
        return f"{self.group}#{self.step}"

    @state.setter
    def state(self, state: str):
        if m := re.match(r"([^#]+)(#(\d+))?", state):
            self.group = m.group(1)
            self.step = int(m.group(3)) if m.group(2) else 0


def image_from_sextants(
    lines: Sequence[str], expected_size: tuple[int, int] | None = None
):
    fg, bg = 0, 255

    src_h, src_w = len(lines) * 3, max(map(len, lines)) * 2
    w, h = expected_size if expected_size else (src_w, src_h)

    im = Image.new("1", (w, h), bg)
    for line, y in zip(lines, count(0, step=3)):
        for c, x in zip(line.rstrip(), count(0, step=2)):
            i = SEXTANTS.index(c)
            for x2, y2, mask in [
                (x + 0, y + 0, 0b100000),
                (x + 1, y + 0, 0b010000),
                (x + 0, y + 1, 0b001000),
                (x + 1, y + 1, 0b000100),
                (x + 0, y + 2, 0b000010),
                (x + 1, y + 2, 0b000001),
            ]:
                if x2 < w and y2 < h:
                    im.putpixel((x2, y2), fg if i & mask else bg)
    return im


SEXTANTS = (
    *(" ", "🬞", "🬏", "🬭", "🬇", "🬦", "🬖", "🬵"),
    *("🬃", "🬢", "🬓", "🬱", "🬋", "🬩", "🬚", "🬹"),
    *("🬁", "🬠", "🬑", "🬯", "🬉", "▐", "🬘", "🬷"),
    *("🬅", "🬤", "🬔", "🬳", "🬍", "🬫", "🬜", "🬻"),
    *("🬀", "🬟", "🬐", "🬮", "🬈", "🬧", "🬗", "🬶"),
    *("🬄", "🬣", "▌", "🬲", "🬌", "🬪", "🬛", "🬺"),
    *("🬂", "🬡", "🬒", "🬰", "🬊", "🬨", "🬙", "🬸"),
    *("🬆", "🬥", "🬕", "🬴", "🬎", "🬬", "🬝", "█"),
)


def apply_pixel_grid(im: Image.Image, scale: int = 6):
    w, h = im.size

    im = im.resize((w * scale, h * scale), Image.Resampling.NEAREST)
    mask = im.split()[-1]
    im = im.convert("RGB")

    draw = ImageDraw.Draw(im, "RGBA")
    c1 = 127, 127, 127, 20
    c2 = 127, 127, 127, 50
    for x in range(0, w * scale + 1, scale):
        draw.polygon([(x - 1, 0), (x - 1, h * scale)], c1)
        draw.polygon([(x, 0), (x, h * scale)], c2)
    for y in range(0, h * scale + 1, scale):
        draw.polygon([(0, y - 1), (w * scale, y - 1)], c1)
        draw.polygon([(0, y), (w * scale, y)], c2)

    im.putalpha(mask)
    return im


if __name__ == "__main__":
    sys.exit(main())
