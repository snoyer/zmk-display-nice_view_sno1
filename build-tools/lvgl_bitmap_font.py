from __future__ import annotations

import logging
import re
import sys
from argparse import ArgumentParser
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import chain, groupby, zip_longest
from pathlib import Path
from textwrap import dedent
from typing import Callable, TypeVar

from minibdf import parse_bdf_font

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "bitmap_fonts", nargs="+", type=Path, help="filenames for fonts to convert"
    )
    parser.add_argument(
        "--output",
        default="-",
        help='filename for generated LVGL code, or "-" for stdout',
    )
    parser.add_argument(
        "--ranges",
        nargs="*",
        help="character ranges to include, for example: 0x20-0x7e,0xa1-0xff",
    )
    parser.add_argument(
        "--name",
        default="{name}",
        help="format for the font variable name (default: %(default)s)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    output = sys.stdout if args.output == "-" else open(args.output, "w")

    utf8_ranges = list(chain.from_iterable(map(parse_char_ranges, args.ranges or [])))

    def keep_glyph(encoding: int):
        return not utf8_ranges or any(encoding in r for r in utf8_ranges)

    output.write("#pragma once\n")
    output.write('#include "lvgl.h"\n')

    for input_path in map(Path, args.bitmap_fonts):
        name = args.name.format(name=input_path.stem)
        name = re.sub(r"[^a-z0-9_]", "_", name, flags=re.I)

        font = parse_bdf_font(open(input_path))
        assert font.ascent is not None
        assert font.descent is not None

        selected_glyphs = [g for g in font.glyphs.values() if keep_glyph(g.encoding)]
        logger.info(
            "generating %r with %d out of %d glyphs from %r",
            name,
            len(selected_glyphs),
            len(font.glyphs),
            input_path.name,
        )

        lv_glyphs = (
            LvGlyph(
                glyph.encoding,
                pack_indexed_1_bit(map(int, "".join(glyph.pixels))),
                glyph.device_width[0] * 16,
                *glyph.bbox,
            )
            for glyph in sorted(selected_glyphs, key=lambda g: g.encoding)
        )
        lv_font = LvFont(
            lv_glyphs,
            ascent=font.ascent,
            descent=font.descent,
        )

        print("", file=output)
        print(f"/* {name} (from {input_path.name}) */", file=output)
        print("", file=output)
        for block in lv_font.code(name):
            print(block, file=output)
            print("", file=output)


def parse_char_ranges(ranges_str: str):
    for sub in re.split(r"[\s,]+", ranges_str):
        if m := re.fullmatch(r"0x([0-9a-f]+)(-0x([0-9a-f]+))?", sub, flags=re.I):
            start = int(m.group(1), 16)
            end = int(m.group(3), 16) if m.group(3) else start
            yield range(start, end + 1)
        else:
            raise ValueError(f"cannot parse range: {ranges_str!r}")


class LvFont:
    def __init__(self, glyphs: Iterable[LvGlyph], *, ascent: int, descent: int) -> None:
        self.glyphs = list(glyphs)
        self.cmaps = list(self.Compute_cmaps(self.glyphs))
        self.ascent = ascent
        self.descent = descent

    def code(self, name: str):
        yield "\n".join(self._glyph_code(name))
        yield "\n".join(self._cmap_code(name))
        yield dedent(
            f"""
        #if LVGL_VERSION_MAJOR == 8
        static lv_font_fmt_txt_glyph_cache_t {name}_cache;
        #endif
        #if LVGL_VERSION_MAJOR >= 8
        static const lv_font_fmt_txt_dsc_t {name}_font_dsc = {{
        #else
        static lv_font_fmt_txt_dsc_t {name}_font_dsc = {{
        #endif
          .glyph_bitmap = {name}_glyph_bitmap,
          .glyph_dsc = {name}_glyph_dsc,
          .cmaps = {name}_cmaps,
          .cmap_num = {len(self.cmaps)},
          .kern_dsc = NULL,
          .kern_scale = 0,
          .bpp = 1,
          .kern_classes = 0,
          .bitmap_format = 0,
        #if LVGL_VERSION_MAJOR == 8
          .cache = &{name}_cache
        #endif
        }};
        """
        ).strip()
        yield dedent(
            f"""
        #if LVGL_VERSION_MAJOR >= 8
        const lv_font_t {name} = {{
        #else
        lv_font_t {name} = {{
        #endif
          .get_glyph_dsc = lv_font_get_glyph_dsc_fmt_txt,
          .get_glyph_bitmap = lv_font_get_bitmap_fmt_txt,
          .line_height = {self.ascent + self.descent},
          .base_line = {self.descent},
        #if !(LVGL_VERSION_MAJOR == 6 && LVGL_VERSION_MINOR == 0)
          .subpx = LV_FONT_SUBPX_NONE,
        #endif
        #if LV_VERSION_CHECK(7, 4, 0) || LVGL_VERSION_MAJOR >= 8
          .underline_position = -1,
          .underline_thickness = 1,
        #endif
          .dsc = &{name}_font_dsc,
        #if LV_VERSION_CHECK(8, 2, 0) || LVGL_VERSION_MAJOR >= 9
          .fallback = NULL,
        #endif
          .user_data = NULL,
        }};
        """
        ).strip()

    def _glyph_code(self, name: str):
        yield f"static LV_ATTRIBUTE_LARGE_CONST const uint8_t {name}_glyph_bitmap[] = {{"
        offsets = [0]
        for g in self.glyphs:
            hex_bytes = ", ".join(f"0x{b:02x}" for b in g.bitmap_bytes)
            comment = f"u{g.utf8:04X} {chr(g.utf8)!r}"
            yield f"  /* {comment} */"
            yield f"  {hex_bytes},"
            offsets.append(offsets[-1] + len(g.bitmap_bytes))
        yield "};"
        yield f"static const lv_font_fmt_txt_glyph_dsc_t {name}_glyph_dsc[] = {{"

        glyphs_and_offsets = chain(
            [(LvGlyph(0, bytearray()), 0)], zip(self.glyphs, offsets)
        )
        for g, index in glyphs_and_offsets:
            comment = f"u{g.utf8:04X} {chr(g.utf8)!r}" if g.utf8 else "reserved"
            yield (
                "  {"
                f".bitmap_index={index:4d}, .adv_w={g.adv_w:3d},"
                f" .box_w={g.box_w:2d}, .box_h={g.box_h:2d},"
                f" .ofs_x={g.ofs_x:2d}, .ofs_y={g.ofs_y:2d}"
                "}"
                f" /* {comment} */,"
            )
        yield "};"

    def _cmap_code(self, name: str):
        unicode_lists: dict[int, str] = {}
        for i, m in enumerate(self.cmaps):
            if m.unicode_list:
                var = unicode_lists[i] = f"{name}_unicode_list_{i}"
                csv = ", ".join(
                    f"0x{(u + m.range_start):04X} -{m.range_start}"
                    for u in m.unicode_list
                )
                yield f"static const uint16_t {var}[] = {{ {csv} }};"

        yield f"static const lv_font_fmt_txt_cmap_t {name}_cmaps[] = {{"
        for i, m in enumerate(self.cmaps):
            glyph_id_ofs_list = "NULL"
            unicode_list = unicode_lists.get(i, "NULL")
            yield f"  {{.range_start = 0x{m.range_start:04X}, .range_length = {m.range_length}, .glyph_id_start = {m.glyph_id_start},"
            yield f"   .unicode_list = {unicode_list}, .glyph_id_ofs_list = {glyph_id_ofs_list}, .list_length = {m.list_length},"
            yield f"   .type = {m.type}}},"
        yield "};"

    @classmethod
    def Compute_cmaps(cls, glyphs: list[LvGlyph]):
        all_utf8s = [glyph.utf8 for glyph in glyphs]
        max_continuous_len = 256
        for is_continuous, utf8s in cls.find_continuity_ranges(all_utf8s):
            if is_continuous:
                yield LvCmap(
                    range_start=utf8s[0],
                    range_length=utf8s[-1] - utf8s[0] + 1,
                    glyph_id_start=all_utf8s.index(utf8s[0]) + 1,
                    type="LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY",
                )
            else:
                for i in range(0, len(utf8s), max_continuous_len):
                    sub_utf8s = utf8s[i : i + max_continuous_len]
                    yield LvCmap(
                        range_start=sub_utf8s[0],
                        range_length=sub_utf8s[-1] - sub_utf8s[0] + 1,
                        glyph_id_start=all_utf8s.index(sub_utf8s[0]) + 1,
                        unicode_list=[utf8 - sub_utf8s[0] for utf8 in sub_utf8s],
                        type="LV_FONT_FMT_TXT_CMAP_SPARSE_TINY",
                    )

    @classmethod
    def find_continuity_ranges(cls, xs: Iterable[int]):
        for continuous, groups in groupby(
            split_between(xs, lambda x, y: x + 1 != y), key=lambda ys: len(ys) > 1
        ):
            if continuous:
                for group in groups:
                    yield True, group
            else:
                yield False, list(chain.from_iterable(groups))


@dataclass
class LvGlyph:
    utf8: int
    bitmap_bytes: bytearray
    adv_w: int = 0
    box_w: int = 0
    box_h: int = 0
    ofs_x: int = 0
    ofs_y: int = 0


@dataclass
class LvCmap:
    range_start: int
    range_length: int
    glyph_id_start: int
    type: str
    unicode_list: list[int] | None = None

    @property
    def list_length(self):
        return len(self.unicode_list) if self.unicode_list else 0


def pack_indexed_1_bit(pixels: Iterable[int]):
    return bytearray(
        sum(((1 if v else 0) << 8 - i) for i, v in enumerate(vs, 1))
        for vs in chunk_by(8, pixels, 0)
    )


T = TypeVar("T")


def chunk_by(n: int, iterable: Iterable[T], fillvalue: T):
    """Iterate by chunks of `n` values, padding last group with `fillvalue` if needed.
    `chunk_by(3, range(7), 9)` -> `(0, 1, 2), (3, 4, 5), (6, 9, 9)`"""
    return zip_longest(*([iter(iterable)] * n), fillvalue=fillvalue)


def split_between(iterable: Iterable[T], between: Callable[[T, T], bool]):
    """Split iterable between items that match the given predicate.
    `split_between("abCDe", lambda a, b: a.isupper() != b.isupper())` -> `['a', 'b'], ['C', 'D'], ['e']`
    """
    it = iter(iterable)
    group: list[T] = []
    try:
        group.append(next(it))
        while True:
            item = next(it)
            if between(group[-1], item):
                yield group[:]
                group.clear()
            group.append(item)
    except StopIteration:
        yield group


if __name__ == "__main__":
    main()
