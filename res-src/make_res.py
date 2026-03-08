from contextlib import contextmanager
import subprocess
from itertools import chain, takewhile
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable, Iterator, Sequence

from bdffont import BdfFont, BdfGlyph
from PIL import Image, ImageDraw


README = """
Files in this directory are generated from the sources in [`/res-src`](../../../../res-src).

`ter-u12b-mod.bdf` and `ter-u14b-mod.bdf` are modified version of `ter-u12b.bdf` and `ter-u14b.bdf`
from https://terminus-font.sourceforge.net/.

- original `ter-u14b.bdf`: ![](ter-u14b.png)
- modified `ter-u14b-mod.bdf`: ![](ter-u14b-mod.png)
- original `ter-u12b.bdf`: ![](ter-u12b.png)
- modified `ter-u12b-mod.bdf`: ![](ter-u12b-mod.png)
""".lstrip()

RES_SRC = Path(__file__).parent
RES = RES_SRC / "../boards/shields/nice_view_sno1/res"


def main():
    RES.mkdir(parents=True, exist_ok=True)
    make_res(RES_SRC, RES)


def make_res(RES_SRC: Path, RES: Path):

    for out_fn, (slice, layer) in {
        "endpoint-usb-ok": ("usb", "usb/usb"),
        "endpoint-usb-na": ("usb", ("usb/usb", "usb/bar")),
        "endpoint-wl-ok": ("wl", "wl/wl"),
        "endpoint-wl-na": ("wl", ("wl/wl", "wl/bar")),
        "endpoint-wl-open": ("wl", ("wl/wl", "wl/open")),
        "endpoint-bt-ok": ("bt", "bt/bt"),
        "endpoint-bt-na": ("bt", ("bt/bt", "bt/bar")),
        "endpoint-bt-open": ("bt", ("bt/bt", "bt/open")),
        "endpoint-none": ("out-none", "out-none"),
        "battery": ("battery", "battery/battery"),
        "battery-dither-mask": ("battery", "battery/dither-mask"),
        "battery-bolt": ("battery-bolt", "battery/bolt"),
        "zmk": ("zmk", ("zmk", "bg")),
        **{f"n{i}": (f"n{i}", "big-digits") for i in range(10)},
    }.items():
        aseprite_export(RES_SRC / "icons.ase", RES / f"{out_fn}.png", slice, layer)

    ####

    profiles_chars = ["ABCDEFGHIJ", "abcdefghij"]
    for out_fn, (slice, layer, chars, size) in {
        "profiles-xs.bdf": ("profiles-xs", "profiles-xs", profiles_chars, 12),
        "profiles-s.bdf": ("profiles-s", "profiles-s", profiles_chars, 14),
        "indicators.bdf": ("locks", ("locks/icons", "locks/dither"), ["NCS", "ncs"], 18),
    }.items():
        with NamedTemporaryFile(suffix=".png") as tmp:
            aseprite_export(RES_SRC / "icons.ase", tmp.name, slice, layer)
            bdf_font_from_char_sheet(tmp.name, chars, size, size, 1).save(RES / out_fn)

    ####

    save_modified_font(
        RES / "ter-u14b-mod.bdf",
        RES_SRC / "ter-u14b.bdf",
        sfd_patch=RES_SRC / "ter-u14b.patch.sfd",
    )
    save_modified_font(RES / "ter-u12b-mod.bdf", RES_SRC / "ter-u12b.bdf")

    fns = [
        RES_SRC / "ter-u14b.bdf",
        RES / "ter-u14b-mod.bdf",
        RES_SRC / "ter-u12b.bdf",
        RES / "ter-u12b-mod.bdf",
    ]
    ims = [
        font_preview(BdfFont.load(fn), "A very bad quack might jinx zippy fowls")
        for fn in fns
    ]
    ims = [apply_pixel_grid(im) for im in ims]

    w = max(im.size[0] for im in ims)
    for fn, im in zip(fns, ims):
        im2 = Image.new("RGBA", (w, im.size[1]))
        im2.paste(im)
        im2.save(RES / f"{fn.stem}.png")

    Path(RES / "readme.md").write_text(README)


def save_modified_font(
    modified: Path, original: Path, *, sfd_patch: Path | None = None
):
    font = BdfFont.load(original)

    if sfd_patch:
        with fontforge_to_bdf(sfd_patch) as tmp_bdf_patch:
            patch_font(font, BdfFont.load(tmp_bdf_patch))

    make_font_narrow(font)

    if font.properties.family_name:
        font.properties.family_name += " (modified)"
        font.generate_name_as_xlfd()
    font.save(modified)


def patch_font(font: BdfFont, font2: BdfFont):
    patch_glyphs = {glyph.encoding: glyph for glyph in font2.glyphs}

    def f(glyph: BdfGlyph):
        try:
            return patch_glyphs[glyph.encoding]
        except KeyError:
            return glyph

    font.glyphs = [f(glyph) for glyph in font.glyphs]


def make_font_narrow(font: BdfFont, max_left_gap: int = 0, max_right_gap: int = 1):
    for glyph in font.glyphs:
        if glyph.encoding >= 0x218F:
            continue

        column_sums = list(map(sum, zip(*glyph.bitmap)))
        if not any(column_sums):
            continue

        left_gap = len(list(takewhile(lambda s: s == 0, column_sums)))
        right_gap = len(list(takewhile(lambda s: s == 0, reversed(column_sums))))

        if left_gap > max_left_gap or right_gap > max_right_gap:
            dl = left_gap - max_left_gap
            dr = right_gap - max_right_gap
            glyph.bitmap = [row[dl : len(row) - dr] for row in glyph.bitmap]
            glyph.width -= dl + dr
            glyph.device_width_x -= dl + dr


def bdf_font_from_char_sheet(
    img_path: Path | str,
    chars: Sequence[Sequence[str]],
    w: int,
    h: int,
    gap: int,
    descent: int = 0,
):
    font = BdfFont(point_size=h, resolution=(75, 75), bounding_box=(w, h, 0, -descent))
    font.properties.font_ascent = h
    font.properties.font_descent = 0
    font.properties.pixel_size = font.point_size
    font.properties.point_size = font.point_size * 10
    font.properties.resolution_x = font.resolution_x
    font.properties.resolution_y = font.resolution_y
    font.generate_name_as_xlfd()

    im = Image.open(img_path).convert("1")
    for j, char_row in enumerate(chars):
        for i, char in enumerate(char_row):

            def px(x: int, y: int):
                return 1 if im.getpixel((x + i * (w + gap), y + j * (h + gap))) else 0

            font.glyphs.append(
                BdfGlyph(
                    char,
                    ord(char),
                    device_width=(w, 0),
                    bounding_box=(w, h, 0, -descent),
                    bitmap=[[px(x, y) for x in range(w)] for y in range(h)],
                )
            )

    return font


@contextmanager
def fontforge_to_bdf(sfd_path: Path):
    with NamedTemporaryFile(suffix=".bdf") as tmp_bdf:
        subprocess.check_call(
            [
                "fontforge",
                "-lang=ff",
                "-c",
                f'Open($1); Generate("{tmp_bdf.name}");',
                str(sfd_path),
            ]
        )
        tmp_path = Path(tmp_bdf.name)
        for fn in tmp_path.parent.glob(f"{tmp_path.stem}*{tmp_path.suffix}"):
            yield fn
            return
    raise ValueError(f"could not convert {sfd_path}")


def aseprite_export(
    input: Path | str,
    output: Path | str,
    slice: str | None = None,
    layer: str | Iterable[str] | None = None,
    aseprite: str | Path = "aseprite",
):
    output = Path(output)

    def aseprite_command(png_out: Path | str) -> Iterator[Any]:
        yield aseprite
        yield from ("-b", input)
        if layer:
            for single_layer in [layer] if isinstance(layer, str) else layer:
                yield from ("--layer", single_layer)
        if slice:
            yield from ("--slice", slice)
        yield from ("--save-as", png_out)

    subprocess.check_call(list(map(str, aseprite_command(output))))

    return output


def font_preview(font: BdfFont, text: str, letter_spacing: int = 0):

    glyphs_by_encoding = {glyph.encoding: glyph for glyph in font.glyphs}
    default_glyph = font.glyphs[0]  # TODO
    text_glyphs = [glyphs_by_encoding.get(ord(c), default_glyph) for c in text]

    w = sum(glyph.device_width[0] for glyph in text_glyphs)
    w += (len(text_glyphs) - 1) * letter_spacing
    h = max(glyph.bounding_box[1] for glyph in text_glyphs)
    baseline = min(glyph.bounding_box[3] for glyph in text_glyphs)

    bitmap = [[0] * w for _ in range(h)]
    x = 0
    for glyph in text_glyphs:
        o = h - glyph.bounding_box[1] + baseline - glyph.bounding_box[3]
        for i, row in enumerate(glyph.bitmap, o):
            bitmap[i][x : x + len(row)] = row
        x += glyph.device_width[0] + letter_spacing

    im = Image.frombytes(
        "RGB",
        (w, h),
        bytes(
            chain.from_iterable(
                (255, 255, 255) if i else (0, 0, 0) for i in chain.from_iterable(bitmap)
            )
        ),
    )
    return im


def apply_pixel_grid(im: Image.Image, scale: int = 5):
    w, h = im.size
    im = im.resize((w * scale, h * scale), Image.Resampling.NEAREST).convert("RGB")

    draw = ImageDraw.Draw(im, "RGBA")
    c1 = 127, 127, 127, 20
    c2 = 127, 127, 127, 50
    for x in range(0, w * scale + 1, scale):
        draw.polygon([(x - 1, 0), (x - 1, h * scale)], c1)
        draw.polygon([(x, 0), (x, h * scale)], c2)
    for y in range(0, h * scale + 1, scale):
        draw.polygon([(0, y - 1), (w * scale, y - 1)], c1)
        draw.polygon([(0, y), (w * scale, y)], c2)
    return im.convert("L")


if __name__ == "__main__":
    main()
