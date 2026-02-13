from colorsys import hsv_to_rgb
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any

import lvgl_indexed_image
from lvgl_indexed_image import format_indexed_template

DIR = Path(__file__).parent


def test_main_basic():
    stdout, stderr, returncode = run_main(
        DIR / "test-img1.png",
        DIR / "test-img2.png",
        "--name=img_{name}",
    )
    Path("/tmp/test-imgs1.h").write_text(stdout)

    assert returncode == 0
    assert stdout == (DIR / "test-imgs1.h").read_text()
    assert (
        "generating 'img_test_img1' from 'test-img1.png' (2 colors: #000000, #ffffff)"
        in stderr
    )
    assert (
        "generating 'img_test_img2' from 'test-img2.png' (3 colors: #00000000, #222034, #9badb7)"
        in stderr
    )


def test_main_invert_rotate():
    stdout, stderr, returncode = run_main(
        DIR / "test-img1.png",
        DIR / "test-img2.png",
        "--name=img_{name}",
        "--invert",
        "--rotate=90",
    )
    Path("/tmp/test-imgs2.h").write_text(stdout)
    print(stderr)
    assert returncode == 0
    assert stdout == (DIR / "test-imgs2.h").read_text()
    assert (
        "generating 'img_test_img1' from 'test-img1.png' (2 colors: #000000, #ffffff)"
        in stderr
    )
    assert (
        "generating 'img_test_img2' from 'test-img2.png' (3 colors: #645248, #dddfcb, #ffffff00)"
        in stderr
    )


def test_main_too_many_colors():
    def ppm(w: int, h: int):
        yield f"P3 {w} {h} 255"
        n = w * h
        for i in range(n):
            r, g, b = (int(round(v * 255)) for v in hsv_to_rgb(i / n, 1, 1))
            yield f"{r} {g} {b}"
        yield ''

    with TemporaryDirectory() as tmp_dir:
        pgm = Path(tmp_dir) / "test3.ppm"
        pgm.write_text("\n".join(ppm(20,13)))

        _stdout, stderr, returncode = run_main(pgm)

        print(stderr)
        assert returncode != 0
        assert "cannot handle 260 colors" in stderr


def run_main(*args: Any):
    proc = subprocess.Popen(
        [
            sys.executable,
            lvgl_indexed_image.__file__,
            *map(str, args),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
    return stdout, stderr, proc.returncode


def test_format_indexed_template_1bit():
    indexed_pixels = [
        *(1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1),
        *(0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0),
        *(0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0),
        *(0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0),
    ]

    size = 19, 4
    palette = [(0x12, 0x34, 0x56, 0x78), (0x87, 0x65, 0x43, 0x21)]
    expected = dedent(
        """
    #ifndef LV_ATTRIBUTE_IMG_TEST
    #define LV_ATTRIBUTE_IMG_TEST
    #endif
    const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_TEST uint8_t test_map[] = {
      0x12, 0x34, 0x56, 0x78, /* color #0 */
      0x87, 0x65, 0x43, 0x21, /* color #1 */
      0xaa, 0xe8, 0x20,
      0x55, 0x54, 0x40,
      0x2a, 0xaa, 0x80,
      0x17, 0x55, 0x00,
    };
    const lv_img_dsc_t test = {
    #if LVGL_VERSION_MAJOR >= 9
      .header.cf = LV_COLOR_FORMAT_I1,
    #else
      .header.cf = LV_IMG_CF_INDEXED_1BIT,
      .header.always_zero = 0,
      .header.reserved = 0,
    #endif
      .header.w = 19,
      .header.h = 4,
      .data_size = 20,
      .data = test_map,
    };
    """
    )
    actual = format_indexed_template(
        "test", 1, palette, bytearray(indexed_pixels), size
    )
    assert actual == expected


def test_format_indexed_template_2bit():
    indexed_pixels = [
        *(1, 0, 2, 0, 2, 0, 1, 0, 3, 2, 3, 0, 1, 0, 0, 0, 0, 0, 1),
        *(0, 1, 0, 2, 0, 1, 0, 1, 0, 3, 0, 1, 0, 1, 0, 0, 0, 1, 0),
        *(0, 0, 1, 0, 1, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2),
        *(0, 0, 0, 1, 0, 2, 3, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2, 3),
    ]

    size = 19, 4
    palette = [(0x12, 0x34, 0x56, 0x78), (0x87, 0x65, 0x43, 0x21)]
    expected = dedent(
        """
    #ifndef LV_ATTRIBUTE_IMG_TEST
    #define LV_ATTRIBUTE_IMG_TEST
    #endif
    const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_TEST uint8_t test_map[] = {
      0x12, 0x34, 0x56, 0x78, /* color #0 */
      0x87, 0x65, 0x43, 0x21, /* color #1 */
      0x12, 0x34, 0x56, 0x78, /* color #0 */
      0x87, 0x65, 0x43, 0x21, /* color #1 */
      0x48, 0x84, 0xec, 0x40, 0x04,
      0x12, 0x11, 0x31, 0x10, 0x10,
      0x04, 0x48, 0x44, 0x44, 0x48,
      0x01, 0x2e, 0x11, 0x11, 0x2c,
    };
    const lv_img_dsc_t test = {
    #if LVGL_VERSION_MAJOR >= 9
      .header.cf = LV_COLOR_FORMAT_I2,
    #else
      .header.cf = LV_IMG_CF_INDEXED_2BIT,
      .header.always_zero = 0,
      .header.reserved = 0,
    #endif
      .header.w = 19,
      .header.h = 4,
      .data_size = 36,
      .data = test_map,
    };
    """
    )
    actual = format_indexed_template(
        "test", 2, palette, bytearray(indexed_pixels), size
    )

    assert actual == expected
