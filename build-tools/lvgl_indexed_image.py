import logging
import re
import subprocess
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from itertools import cycle, islice, zip_longest
from math import ceil, log2
from pathlib import Path
from textwrap import dedent
from typing import Iterable, Literal, Sequence, TypeVar

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "images", nargs="+", type=Path, help="filenames for images to convert"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help='filename for generated LVGL code, or "-" for stdout',
    )
    parser.add_argument(
        "--img-name",
        default="img_{name}",
        help="format for the image variable name (default: %(default)s)",
    )
    parser.add_argument(
        "--rotate",
        choices=[0, 90, 180, 270, -90, -180, -270],
        type=int,
        default=0,
        help="clockwise rotation in degrees",
    )
    parser.add_argument(
        "--invert", action="store_true", help="invert pixels' RGB values"
    )
    seq_type_group = parser.add_mutually_exclusive_group()
    seq_type_group.add_argument(
        "--declare-seq-struct",
        nargs="?",
        const="img_dsc_seq",
        help="name to declare a"
        " `struct NAME { const unsigned int count; const lv_img_dsc_t *imgs[]; }`"
        " for image sequences (default: %(const)s)",
        metavar="NAME",
    )
    seq_type_group.add_argument(
        "--use-seq-struct",
        help="name of an extisting"
        " `struct NAME { const unsigned int count; const lv_img_dsc_t *imgs[]; }`"
        " for image sequences",
        metavar="NAME",
    )
    parser.add_argument(
        "--seq-name",
        default="imgs_{name}",
        help="format for image sequences names (default: %(default)s)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    out = sys.stdout if args.output == "-" else open(args.output, "w")

    print(HEADER_TEMPLATE, file=out)

    numbered_sequences: dict[str, list[str]] = {}

    for path in args.images:
        pixels, size = read_rgba_bitmap(
            path, negate=args.invert, rotate90=args.rotate // 90
        )

        px_to_index = {px: i for i, px in enumerate(sorted(set(pixels)))}
        color_count = len(px_to_index)

        min_bit_count = max(1, ceil(log2(color_count)))
        actual_bit_count = max(1, 2 ** ceil(log2(min_bit_count)))
        if actual_bit_count not in (1, 2, 4, 8):
            raise ValueError(f"cannot handle {color_count} colors")

        indexed_pixels = bytearray(px_to_index[px] for px in pixels)
        palette = sorted(px_to_index, key=px_to_index.__getitem__)

        name = sanitize_variable_name(path.stem)
        formatted_name = sanitize_variable_name(args.img_name.format(name=path.stem))
        logger.info(
            "generating 'lv_img_dsc_t %s' from %r (%d colors: %s)",
            formatted_name,
            path.name,
            color_count,
            ", ".join(map(format_hex_rgba, px_to_index)),
        )

        code = format_indexed_template(
            formatted_name, actual_bit_count, palette, indexed_pixels, size
        )
        print(code, file=out)

        if m := re.match(r"(.+?)\d+$", name):
            basename = m.group(1)
            numbered_sequences.setdefault(basename, []).append(formatted_name)

    if args.declare_seq_struct:
        seq_type = args.declare_seq_struct
        guard = f"_{seq_type}_STRUCT_".upper()
        struct_def = f"""
            #ifndef {guard}
            #define {guard}
            struct {seq_type} {{
            const unsigned int count;
            const lv_img_dsc_t *imgs[];
            }};
            #endif  // {guard}
            """
        print(dedent(struct_def), file=out)
    elif args.use_seq_struct:
        seq_type = args.use_seq_struct
    else:
        seq_type = None

    if seq_type and numbered_sequences:
        for basename, names in numbered_sequences.items():
            basename = args.seq_name.format(name=basename)
            count = len(names)
            logger.info("generating '%s %s' (%d items)", seq_type, basename, count)
            print(f"const struct {seq_type} {basename} = {{{count}, {{", file=out)
            for name in sorted(names):
                print(f"  &{name},", file=out)
            print("}};", file=out)


## LVGL code generation ########################################################


HEADER_TEMPLATE = """
#pragma once
#include <lvgl.h>
#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif
"""
INDEXED_TEMPLATE = """
#ifndef LV_ATTRIBUTE_IMG_{NAME}
#define LV_ATTRIBUTE_IMG_{NAME}
#endif
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_{NAME} uint8_t {name}_map[] = {{
{palette}
{pixels}
}};
const lv_img_dsc_t {name} = {{
#if LVGL_VERSION_MAJOR >= 9
  .header.cf = {format_v9},
#else
  .header.cf = {format_v8},
  .header.always_zero = 0,
  .header.reserved = 0,
#endif
  .header.w = {w},
  .header.h = {h},
  .data_size = {data_size},
  .data = {name}_map,
}};
"""


def format_indexed_template(
    name: str,
    bit_count: Literal[1, 2, 4, 8],
    palette: Sequence[tuple[int, int, int, int]],
    indexed_pixels: bytearray,
    size: tuple[int, int],
):
    packed_pixels = pack_indexed_n_bit(bit_count, indexed_pixels, size[0])
    formatted_pixels = "\n".join(
        "  " + (" ".join(f"0x{v:02x}," for v in row))
        for row in chunk_by(int(ceil(size[0] / (8 / bit_count))), packed_pixels, 0)
    )

    color_count = 2**bit_count

    def palette_code():
        for i, (r, g, b, a) in islice(cycle(enumerate(palette)), color_count):
            yield f"  0x{r:02x}, 0x{g:02x}, 0x{b:02x}, 0x{a:02x}, /* color #{i} */"

    return INDEXED_TEMPLATE.format(
        format_v9=f"LV_COLOR_FORMAT_I{bit_count}",
        format_v8=f"LV_IMG_CF_INDEXED_{bit_count}BIT",
        name=name,
        NAME=name.upper(),
        palette="\n".join(palette_code()),
        pixels=formatted_pixels,
        w=size[0],
        h=size[1],
        data_size=len(packed_pixels) + color_count * 4,
    )


def pack_indexed_n_bit(bit_count: Literal[1, 2, 4, 8], pixels: Iterable[int], w: int):
    return bytearray(
        sum((v << 8 - bit_count * i) for i, v in enumerate(vs, 1))
        for row in chunk_by(w, pixels, 0)
        for vs in chunk_by(8 // bit_count, row, 0)
    )


def sanitize_variable_name(name: str):
    return re.sub(r"[^a-z0-9_]", "_", name, flags=re.IGNORECASE)


## image IO ####################################################################


def read_rgba_bitmap(
    path: Path, *, negate: bool = False, rotate90: int = 0
) -> tuple[list[tuple[int, int, int, int]], tuple[int, int]]:
    indentify_cmd = (
        "identify",
        "-ping",
        *("-format", "%w %h"),
        str(path),
    )
    w, h = map(int, subprocess.check_output(indentify_cmd, text=True).split())

    convert_cmd = (
        "convert",
        str(path),
        *(["-channel", "RGB", "-negate"] if negate else []),
        *("-rotate", str(90 * rotate90)),
        *("-depth", "8"),
        "rgba:-",
    )
    rgb_data = subprocess.check_output(convert_cmd, text=False)
    assert len(rgb_data) == w * h * 4
    rgba_pixels = [(r, g, b, a) for r, g, b, a in chunk_by(4, rgb_data, 0)]

    return rgba_pixels, (h, w) if rotate90 % 2 else (w, h)


T = TypeVar("T")


def chunk_by(n: int, iterable: Iterable[T], fillvalue: T):
    """Iterate by chunks of `n` values, padding last group with `fillvalue` if needed.
    `chunk_by(3, range(7), 9)` -> `(0, 1, 2), (3, 4, 5), (6, 9, 9)`"""
    return zip_longest(*([iter(iterable)] * n), fillvalue=fillvalue)


def format_hex_rgba(rgba: tuple[int, int, int, int]):
    r, g, b, a = rgba
    if a == 255:
        return f"#{r:02x}{g:02x}{b:02x}"
    else:
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"


if __name__ == "__main__":
    main()
