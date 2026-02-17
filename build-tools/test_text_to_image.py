from pathlib import Path
import subprocess
import sys
from typing import Any
from pytest import mark

import text_to_image

DIR = Path(__file__).parent


@mark.parametrize(
    "args, expected",
    [
        (
            [DIR / "test-font.bdf", "--text=abc", "--output=pgm:-"],
            b"P5\n6 3\n255\n\x00\xff\x00\xff\x00\x00\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff",
        ),
        (
            [DIR / "test-font.bdf", "--text=abc", "--trim", "--output=pbm:-"],
            b"P4\n6 2\n\xac ",
        ),
    ],
)
def test_text_to_image(args: list[str], expected: bytes):
    stdout, _stderr, returncode = run_main(*args)
    print(stdout)
    assert returncode == 0
    assert stdout == expected


def test_trim_bitmap():
    padded_bitmap = [
        "0000000000",
        "0000000000",
        "0001110000",
        "0001010000",
        "0001110000",
        "0000000000",
    ]
    trimmed_bitmap = [
        "111",
        "101",
        "111",
    ]
    assert text_to_image.trim_bitmap(padded_bitmap) == trimmed_bitmap


def test_trim_bitmap_nop():
    trimmed_bitmap = [
        "111",
        "101",
        "111",
    ]
    assert text_to_image.trim_bitmap(trimmed_bitmap) == trimmed_bitmap


def run_main(*args: Any):
    proc = subprocess.Popen(
        [
            sys.executable,
            text_to_image.__file__,
            *map(str, args),
        ],
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
    return stdout, stderr, proc.returncode
