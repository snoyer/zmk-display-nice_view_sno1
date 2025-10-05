import subprocess
import sys
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import lvgl_bitmap_font
from lvgl_bitmap_font import LvFont, parse_char_ranges
from pytest import mark, raises

DIR = Path(__file__).parent


def test_main1():
    stdout, stderr, returncode = run_main(
        DIR / "test-font.bdf",
        "--name=font_{name}",
        "--ranges=0x63-0x67,0x69-0x6a,0x6d,0x6f,0x71,0x75-0x79",  # c-g, i-j, m,o,w, u-y
    )
    Path("/tmp/test-font.h").write_text(stdout)

    assert returncode == 0
    assert (DIR / "test-font.h").read_text() == stdout
    assert (
        "generating 'font_test_font' with 15 out of 26 glyphs from 'test-font.bdf'"
        in stderr
    )


def test_main_no_font_in_file():
    with TemporaryDirectory() as tmp_dir:
        bdf = Path(tmp_dir) / "empty.bdf"
        bdf.write_bytes(b"")

        _stdout, stderr, returncode = run_main(bdf)
        assert returncode != 0
        assert "no font in file" in stderr


def test_main_invalid_bdf():
    with TemporaryDirectory() as tmp_dir:
        bdf = Path(tmp_dir) / "invalid.bdf"
        bdf.write_bytes(b"blah")

        _stdout, stderr, returncode = run_main(bdf)
        assert returncode != 0
        assert "invalid BDF line: 'blah'" in stderr


def run_main(*args: Any):
    proc = subprocess.Popen(
        [
            sys.executable,
            lvgl_bitmap_font.__file__,
            *map(str, args),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
    return stdout, stderr, proc.returncode


@mark.parametrize(
    "expected",
    [
        [(False, [1, 3, 5, 7, 9])],
        [(True, [4, 5, 6, 7])],
        [(True, [2, 3]), (True, [8, 9]), (False, [12, 14]), (True, [19, 20])],
        [(False, [1, 3, 5, 7, 9]), (True, [11, 12]), (False, [14, 16, 18])],
    ],
)
def test_continuity_ranges(expected: list[tuple[bool, list[int]]]):
    input = list(chain.from_iterable(xs for _, xs in expected))
    assert list(LvFont.find_continuity_ranges(input)) == expected


@mark.parametrize(
    "input, expected",
    [
        ("0x12-0x20", [range(0x12, 0x21)]),
        ("0x12-0x20,0x44-0x60", [range(0x12, 0x21), range(0x44, 0x61)]),
        ("0x01", [range(0x01, 0x02)]),
        ("0x01,0x02-0x08", [range(0x01, 0x02), range(0x02, 0x09)]),
    ],
)
def test_parse_char_ranges(input: str, expected: list[range]):
    assert list(parse_char_ranges(input)) == expected


def test_parse_char_ranges_error():
    with raises(ValueError):
        list(parse_char_ranges("foo-bar"))
