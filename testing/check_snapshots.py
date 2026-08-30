from __future__ import annotations

import json
import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from itertools import count, groupby
from os import isatty
from pathlib import Path
from tempfile import gettempdir
from typing import Any, cast

from PIL import Image, ImageDraw, ImageOps
from PIL.PngImagePlugin import PngInfo
from sequence_align.pairwise import needleman_wunsch_with_scores

SUCCESS = "✔"
FAILURE = "✘"
WARNING = "⚠"


def main():
    timestamp_extractor = TimestampExtractor()
    snapshot_extractor = SnapshotExtractor()

    all_snapshots: list[Snapshot] = []
    display_state = ""

    for line in sys.stdin if not isatty(0) else [""]:
        print(line, end="")

        timestamp_extractor(line)
        snapshot_extractor(line)

        for im in snapshot_extractor.pop_snapshot_images():
            snapshot = Snapshot(
                ImageOps.invert(im.rotate(90, expand=True)),
                time=timestamp_extractor.seconds,
            )
            if not all_snapshots or snapshot.image != all_snapshots[-1].image:
                snapshot.state = display_state
                all_snapshots.append(snapshot)

        if m := re.search(r"display state:\s*(.*)", line):
            display_state = str(m.group(1))

    success = True
    TMP_DIR = Path(gettempdir()) / "zmk-display-nice_view_sno1"
    TMP_SNAPSHOTS_DIR = TMP_DIR / "snapshots"
    TMP_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    REF_SNAPSHOTS_DIR = Path(__file__).parent / "expected"

    for key, frame_groups in find_frames_groups(all_snapshots):
        collated_im = collate_frame_groups(frame_groups, "LA")
        collated_im.save(
            TMP_SNAPSHOTS_DIR / f"snapshots{key}.png", pnginfo=pnginfo(collated_im.info)
        )

        ref_path = REF_SNAPSHOTS_DIR / f"snapshots{key}.png"
        if ref_path.is_file():
            old_collated_im = Image.open(ref_path).convert("LA")
            old_frame_groups = list(uncollate_frame_groups(old_collated_im))

            if len(frame_groups) == len(old_frame_groups):
                diffs = [
                    frame_group_diff(xx, yy)
                    for xx, yy in zip(old_frame_groups, frame_groups)
                ]
                diff_count = sum(px_count for _, px_count in diffs)
                if diff_count:
                    print(FAILURE, key, f"({diff_count} pixels difference)")
                    success = False
                else:
                    print(SUCCESS, key)

                collated_diff = collate_frame_groups(
                    [[(im, 0) for im in ims] for ims, _ in diffs], "RGBA"
                )
                apply_pixel_grid(collated_diff).save(
                    TMP_DIR / f"snapshots{key}.diff.png"
                )
            else:
                print(WARNING, key, "(different size)")

    return 0 if success else 1


def find_frames_groups(all_snapshots: list[Snapshot]):
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
            if snapshots := list(snapshots):
                t0 = snapshots[0].time
                snapshots_by_step.append(
                    [replace(s, time=s.time - t0) for s in snapshots]
                )

        animated_frame_groups = [
            [(snapshot.image, snapshot.time) for snapshot in snapshots]
            for snapshots in snapshots_by_step
        ]
        yield f"{key}-anim", animated_frame_groups

        image_groups = [frames[:1] for frames in animated_frame_groups]
        yield f"{key}", image_groups


def pnginfo(info: dict[str | tuple[int, int], Any]):
    pnginfo = PngInfo()
    for k, v in info.items():
        if isinstance(v, str):
            pnginfo.add_text(str(k), v)
        # TODO?
    return pnginfo


def frame_group_diff(
    old_images: Sequence[tuple[Image.Image, float]],
    new_images: Sequence[tuple[Image.Image, float]],
):
    diffs = list(
        image_sequence_diff([im for im, _ in old_images], [im for im, _ in new_images])
    )
    return [im for im, _ in diffs], sum(px_count for _, px_count in diffs)


def collate_frame_groups(
    frame_groups: list[list[tuple[Image.Image, float]]],
    mode: str,
    max_width: int = 900,
    margin: int = 16,
):
    small_padding = 8
    big_padding = 16
    v_padding = 16

    images_by_line: list[list[tuple[Image.Image, int]]] = [[]]
    x = 0
    for frames in frame_groups:
        for image, _time in frames:
            if x + image.width >= max_width - 2 * margin:
                images_by_line.append([])
                x = 0
            images_by_line[-1].append((image, x))
            x += image.width + small_padding
        x += big_padding - small_padding

    line_widths = [max(image.width + x for image, x in line) for line in images_by_line]
    line_heights = [max(image.height for image, _ in line) for line in images_by_line]

    w = max(line_widths)
    h = sum(line_heights) + v_padding * (len(line_heights) - 1)

    dst_im = Image.new(mode, (w + 2 * margin, h + 2 * margin))
    y = 0
    areas: list[tuple[int, int, int, int]] = []
    for line, h in zip(images_by_line, line_heights):
        for im, x in line:
            dst_im.paste(im, (x + margin, y + margin))
            areas.append((x + margin, y + margin, im.width, im.height))
        y += h + v_padding

    dst_im.info = {
        "areas": json.dumps(areas, separators=(",", ":")),
        "times": json.dumps(
            [[t for _im, t in frames] for frames in frame_groups],
            separators=(",", ":"),
        ),
    }
    return dst_im


def uncollate_frame_groups(
    collated_im: Image.Image,
) -> Iterator[list[tuple[Image.Image, float]]]:
    boxes = iter(
        (x, y, x + w, y + h) for x, y, w, h in json.loads(collated_im.info["areas"])
    )
    for times in json.loads(collated_im.info["times"]):
        yield [(collated_im.crop(next(boxes)), t) for t in times]


T0 = datetime.strptime("00:00:00", "%H:%M:%S")  # noqa: DTZ007


def parse_timestamp(ts: str):
    return datetime.strptime(ts[:-4], "%H:%M:%S.%f") - T0  # noqa: DTZ007


def image_sequence_diff(
    old_images: Sequence[Image.Image], new_images: Sequence[Image.Image]
):
    empty = Image.new("L", old_images[0].size, 0)

    def overlap_score(a: Image.Image | None, b: Image.Image | None):
        if a == b:
            return 4.0

        data_a = cast(Iterable[int], (a or empty).convert("L").getdata())
        data_b = cast(Iterable[int], (b or empty).convert("L").getdata())
        sum1 = sum(1 if px != 0 else 0 for px in data_a)
        sum2 = sum(1 if px != 0 else 0 for px in data_b)
        union = sum(
            1 if px_a != 0 and px_b != 0 else 0 for px_a, px_b in zip(data_a, data_b)
        )
        return (2 * union) / (sum1 + sum2) if sum1 and sum2 else 0

    aligned_seq1, aligned_seq2 = needleman_wunsch_with_scores(
        old_images,
        new_images,
        None,
        score_fn=overlap_score,
        indel_score=-1.0,
    )
    return (
        image_diff(b or empty, a or empty) for a, b in zip(aligned_seq1, aligned_seq2)
    )


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


@dataclass
class TimestampExtractor:
    time: timedelta = field(default_factory=timedelta)

    def __call__(self, line: str):
        if m := re.match(r"\[([0-9.,:]+)\]", line):
            self.time = parse_timestamp(m.group(1))

    @property
    def seconds(self):
        return self.time.seconds + self.time.microseconds / 1_000_000


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
