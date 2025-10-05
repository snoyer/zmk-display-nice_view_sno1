"""Minimal BDF parsing. Just enough to render/convert glyphs without additional dependencies."""

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import zip_longest
from math import ceil
from typing import TypeVar


@dataclass
class BdfGlyph:
    encoding: int
    bbox: tuple[int, int, int, int]
    bitmap: bytearray
    device_width: tuple[int, int]

    @property
    def pixels(self):
        return [
            "".join(f"{b:08b}" for b in row)[: self.bbox[0]]
            for row in chunk_by(int(ceil(self.bbox[0] / 8)), self.bitmap, 0)
        ]


@dataclass
class BdfFont:
    glyphs: dict[str, BdfGlyph]
    bbox: tuple[int, int, int, int]
    ascent: int
    descent: int


def parse_bdf_font(lines: Iterable[str]):
    def parse_4i(s: str):
        a, b, c, d = s.split(" ")
        return int(a), int(b), int(c), int(d)

    def parse_2i(s: str):
        x, y = s.split(" ")
        return int(x), int(y)

    def parse_glyph(glyph: dict[str, str]):
        return BdfGlyph(
            encoding=int(glyph["ENCODING"]),
            bbox=parse_4i(glyph["BBX"]),
            bitmap=bytearray(
                int("".join(b), 16) for b in chunk_by(2, glyph["BITMAP"], "0")
            ),
            device_width=parse_2i(glyph["DWIDTH"]),
        )

    for font, properties, chars in bdf_lines_to_dicts(lines):
        return BdfFont(
            glyphs={k: parse_glyph(v) for k, v in chars.items() if k},
            ascent=int(properties["FONT_ASCENT"]),
            descent=int(properties["FONT_DESCENT"]),
            bbox=parse_4i(font["FONTBOUNDINGBOX"]),
        )

    raise ValueError("no font in file")


def bdf_lines_to_dicts(lines: Iterable[str]):
    font: dict[str, str] = {}
    properties: dict[str, str] = {}
    chars: dict[str, dict[str, str]] = {}

    section = font
    for line in map(str.strip, lines):
        try:
            if line.startswith("STARTFONT"):
                section = font = {}
            elif line.startswith("ENDPROPERTIES"):
                section = font
            elif line.startswith("STARTPROPERTIES"):
                section = properties
            elif line.startswith("ENDFONT"):
                yield font, properties, chars

            elif line.startswith("STARTCHAR"):
                section = chars.setdefault(line.split(" ", 1)[1], {})
            elif line.startswith("ENDCHAR"):
                section = font
            elif line.startswith("BITMAP"):
                section["BITMAP"] = ""

            elif "BITMAP" in section:
                section["BITMAP"] += line
            else:
                k, v = line.split(" ", 1)
                section[k] = v
        except ValueError:
            raise ValueError(f"invalid BDF line: {line!r}")


def type_as_bitmap(text: str, font: BdfFont, letter_spacing: int = 1):
    glyphs_by_encoding = {glyph.encoding: glyph for glyph in font.glyphs.values()}
    text_glyphs = [glyphs_by_encoding[ord(c)] for c in text]

    w = sum(glyph.device_width[0] for glyph in text_glyphs)
    w += (len(text_glyphs) - 1) * letter_spacing
    h = max(glyph.bbox[1] for glyph in text_glyphs)
    baseline = min(glyph.bbox[3] for glyph in text_glyphs)

    bitmap = [[" "] * w for _ in range(h)]
    x = 0
    for glyph in text_glyphs:
        o = h - glyph.bbox[1] + baseline - glyph.bbox[3]
        for i, row in enumerate(glyph.pixels, o):
            bitmap[i][x : x + len(row)] = row
        x += glyph.device_width[0] + letter_spacing
    return ["".join(map(str, line)) for line in bitmap]


T = TypeVar("T")


def chunk_by(n: int, iterable: Iterable[T], fillvalue: T):
    """Iterate by chunks of `n` values, padding last group with `fillvalue` if needed.
    `chunk_by(3, range(7), 9)` -> `(0, 1, 2), (3, 4, 5), (6, 9, 9)`"""
    return zip_longest(*([iter(iterable)] * n), fillvalue=fillvalue)
