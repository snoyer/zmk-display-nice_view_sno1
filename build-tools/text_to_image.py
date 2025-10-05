import logging
import subprocess
import sys
from argparse import ArgumentParser
from itertools import chain

from minibdf import parse_bdf_font, type_as_bitmap


def main():
    parser = ArgumentParser()
    parser.add_argument("font", help="BDF font to use")
    parser.add_argument("--text", default="a very bad quack might jinx zippy fowls")
    parser.add_argument("-o", "--output", default="-")
    parser.add_argument("-s", "--spacing", type=int, default=0)
    parser.add_argument("-t", "--trim", action="store_true")

    args = parser.parse_args()

    font = parse_bdf_font(open(args.font))
    bitmap = type_as_bitmap(args.text, font, letter_spacing=args.spacing)
    if args.trim:
        bitmap = trim_bitmap(bitmap)

    w = max(map(len, bitmap))
    h = len(bitmap)

    px_off = 255, 255, 255
    px_on = 0, 0, 0
    rgb_bytes = chain.from_iterable(
        px_on if px == "1" else px_off for row in bitmap for px in row
    )
    sys.stdout.buffer.write(
        subprocess.check_output(
            ["convert", "-size", f"{w}x{h}", "-depth", "8", "rgb:-", args.output],
            input=bytearray(rgb_bytes),
        )
    )


def trim_bitmap(bitmap: list[str]):
    while "1" not in bitmap[0]:
        bitmap.pop(0)
    while "1" not in bitmap[-1]:
        bitmap.pop(-1)

    j0 = min(row.find("1") for row in bitmap)
    j1 = max(row.rfind("1") for row in bitmap) + 1

    return [row[j0:j1] for row in bitmap]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
