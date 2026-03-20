from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from itertools import count, groupby
from math import ceil
from os import isatty
from pathlib import Path
from tempfile import gettempdir
from typing import Sequence, cast

from PIL import Image, ImageDraw, ImageOps

SUCCESS = "✔"
FAILURE = "✘"
WARNING = "⚠"


def main():
    timestamp_extractor = TimestampExtractor()
    snapshot_extractor = SnapshotExtractor()
    varible_extractor = VariableExtractor()

    all_snapshots: list[Snapshot] = []

    for line in sys.stdin if not isatty(0) else [""]:
        if im := snapshot_extractor(line):
            snapshot = Snapshot(
                im,
                caption=varible_extractor.variables.get("demo_stage", "1"),
                is_transition=not bool(
                    int(varible_extractor.variables.get("layout_done", "1"))
                ),
                time=timestamp_extractor.seconds,
            )
            all_snapshots.append(snapshot)
        timestamp_extractor(line)
        varible_extractor(line)
        print(line, end="")

    columns = int(varible_extractor.variables.get("CONFIG_TRACKED_PROFILE_COUNT", 5))
    padding = 16

    success = True

    TMP = Path(gettempdir())

    for key, snapshots_by_caption in groupby(
        sorted(all_snapshots, key=lambda s: s.caption),
        key=lambda s: s.caption,
    ):
        if key and not key.startswith("["):
            key = f"[{key}]"

        snapshots = [
            next(same_snapshots)
            for _, same_snapshots in groupby(
                snapshots_by_caption, key=lambda s: (s.is_transition, s.image.tobytes())
            )
        ]
        nontransition_images = [s.image for s in snapshots if not s.is_transition]
        collated_im = collate_images(
            nontransition_images, "LA", columns=columns, padding=padding
        )

        collated_im.save(TMP / f"snapshots{key}.png")

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

        apply_pixel_grid(collated_im).save(TMP / f"snapshots{key}.diff.png")

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
        return (self.timestamp - self.T0).seconds


@dataclass
class VariableExtractor:
    variables: dict[str, str] = field(default_factory=dict)

    def __call__(self, line: str):
        if m := re.search(r"([\S=]+) *= *(.+)", line):
            self.variables[m.group(1)] = m.group(2)


@dataclass
class SnapshotExtractor:
    snapshot_lines: list[str] | None = None
    snapshot_resolution: tuple[int, int] | None = None

    def __call__(self, line: str):
        line = line.strip("\r\n")
        if m := re.search(r": (\d+)x(\d+) lvgl snapshot", line):
            snapshot = self._save_snapshot()
            self.snapshot_resolution = int(m.group(1)), int(m.group(2))
            self.snapshot_lines = []
            return snapshot
        elif self.snapshot_lines is not None:
            if line and line[0] in SEXTANTS:
                self.snapshot_lines.append(line)
                return
            else:
                snapshot = self._save_snapshot()
                self.snapshot_resolution = None
                self.snapshot_lines = None
                return snapshot

    def _save_snapshot(self):
        if self.snapshot_lines:
            im = image_from_sextants(self.snapshot_lines, self.snapshot_resolution)
            if self.snapshot_resolution and self.snapshot_resolution != im.size:
                im = im.crop((0, 0, *self.snapshot_resolution))
            im = im.rotate(90, expand=True)
            im = ImageOps.invert(im)

            self.snapshot_lines.clear()
            return im


@dataclass
class Snapshot:
    image: Image.Image
    caption: str = ""
    is_transition: bool = False
    time: float = 0.0


def bitmap_from_sextants(
    lines: Sequence[str], expected_size: tuple[int, int] | None = None
):
    a, b = 0, 255

    src_h, src_w = len(lines) * 3, max(map(len, lines)) * 2
    w, h = expected_size if expected_size else (src_w, src_h)

    pixels = bytearray([0] * (w * h))
    for line, y in zip(lines, count(0, step=3)):
        for c, x in zip(line, count(0, step=2)):
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
                    pixels[x2 + y2 * w] = a if i & mask else b
    return pixels, (w, h)


def image_from_sextants(
    lines: Sequence[str], expected_size: tuple[int, int] | None = None
):
    pixels, (w, h) = bitmap_from_sextants(lines, expected_size)
    im = Image.new("1", (w, h))
    for i, v in enumerate(pixels):
        im.putpixel((i % w, i // w), v)
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
