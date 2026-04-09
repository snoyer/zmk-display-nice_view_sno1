import subprocess
import sys
from colorsys import hsv_to_rgb
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any

import lvgl_indexed_image
from lvgl_indexed_image import format_indexed_template

DIR = Path(__file__).parent


def test_main_basic():
    stdout, stderr, returncode = run_main(
        DIR / "test-img-hello-2colors.png",
        DIR / "test-img-hello-3colors.png",
    )
    Path("/tmp/test-imgs-basic.h").write_text(stdout)

    assert returncode == 0
    assert stdout == (DIR / "test-imgs-basic.h").read_text()
    assert (
        "generating 'lv_img_dsc_t img_test_img_hello_2colors'"
        " from 'test-img-hello-2colors.png'"
        " (2 colors: #000000, #ffffff)" in stderr
    )
    assert (
        "generating 'lv_img_dsc_t img_test_img_hello_3colors'"
        " from 'test-img-hello-3colors.png'"
        " (3 colors: #00000000, #222034, #9badb7)" in stderr
    )


def test_main_invert_rotate():
    stdout, stderr, returncode = run_main(
        DIR / "test-img-hello-2colors.png",
        DIR / "test-img-hello-3colors.png",
        "--invert",
        "--rotate=90",
    )
    Path("/tmp/test-imgs-invert_rotate.h").write_text(stdout)

    assert returncode == 0
    assert stdout == (DIR / "test-imgs-invert_rotate.h").read_text()
    assert (
        "generating 'lv_img_dsc_t img_test_img_hello_2colors'"
        " from 'test-img-hello-2colors.png'"
        " (2 colors: #000000, #ffffff)" in stderr
    )
    assert (
        "generating 'lv_img_dsc_t img_test_img_hello_3colors'"
        " from 'test-img-hello-3colors.png'"
        " (3 colors: #645248, #dddfcb, #ffffff00)" in stderr
    )


def test_main_sequences_declare_struct():
    with TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stdout, stderr, returncode = run_main(
            make_test_pgm(tmp / "a1.ppm", 0x000000, 0x000000, 0x000000),
            make_test_pgm(tmp / "a2.ppm", 0x000000, 0xFF0000, 0x000000),
            make_test_pgm(tmp / "a3.ppm", 0x000000, 0xFF0000, 0xFF0000),
            make_test_pgm(tmp / "a4.ppm", 0x000000, 0xFF0000, 0x000000),
            make_test_pgm(tmp / "a5.ppm", 0x000000, 0x000000, 0x000000),
            make_test_pgm(tmp / "b0.ppm", 0xFF0000, 0x00FF00, 0x0000FF),
            make_test_pgm(tmp / "b1.ppm", 0x00FF00, 0x0000FF, 0xFF0000),
            "--img-name=frame_{name}",
            "--declare-seq-struct",
            "--seq-name=frames_{name}",
        )
    Path("/tmp/test-imgs-declare_struct.h").write_text(stdout)

    assert returncode == 0
    assert stdout == (DIR / "test-imgs-declare_struct.h").read_text()
    assert "generating 'img_dsc_seq frames_a' (5 items)" in stderr
    assert "generating 'img_dsc_seq frames_b' (2 items)" in stderr


def test_main_sequences_use_struct():
    with TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stdout, stderr, returncode = run_main(
            make_test_pgm(tmp / "a1.ppm", 0x000000, 0x000000, 0x000000),
            make_test_pgm(tmp / "a2.ppm", 0x000000, 0xFF0000, 0x000000),
            "--use-seq-struct=img_list_t",
        )
    Path("/tmp/test-imgs-use_struct.h").write_text(stdout)

    assert returncode == 0
    assert stdout == (DIR / "test-imgs-use_struct.h").read_text()
    assert "generating 'img_list_t imgs_a' (2 items)" in stderr


def test_main_too_many_colors():
    def ppm(w: int, h: int):
        yield f"P3 {w} {h} 255"
        n = w * h
        for i in range(n):
            r, g, b = (int(round(v * 255)) for v in hsv_to_rgb(i / n, 1, 1))
            yield f"{r} {g} {b}"
        yield ""

    with TemporaryDirectory() as tmp_dir:
        pgm = Path(tmp_dir) / "test3.ppm"
        pgm.write_text("\n".join(ppm(20, 13)))

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
    expected = dedent("""
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
    """)
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
    expected = dedent("""
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
    """)
    actual = format_indexed_template(
        "test", 2, palette, bytearray(indexed_pixels), size
    )

    assert actual == expected


def make_test_pgm(ppm_fn: Path | str, *colors: int):
    w, h = len(colors), 1

    def ppm_lines():
        yield f"P3 {w} {h} 255"
        for px in colors:
            r, g, b = (px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF
            yield f"{r} {g} {b}"
        yield ""

    Path(ppm_fn).write_text("\n".join(ppm_lines()))
    return str(ppm_fn)
