"""Render the portrait image as coloured ASCII-art SVG text rows.

Used by build_card.py.

If the image has transparency (a background-removed PNG), transparent pixels
are left blank so only the subject is drawn.
"""

from html import escape

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# ---- Settings (edit these) -------------------------------------------------
IMAGE_PATH = "assets/portrait.jpg"  # use a transparent PNG for a clean cutout
WIDTH = 70  # output columns
# Ordered from lightest to densest. Density follows brightness, so bright
# areas get dense characters (suits dark GitHub themes).
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
INVERT = False  # True: dense characters for dark areas instead
CHAR_W = 5  # SVG units per column
CHAR_H = 8.5  # SVG units per row, about 1.7x the width for monospace text
FONT_SIZE = 8.5
# Crop box as fractions of the image: (left, top, right, bottom).
CROP = (0.30, 0.07, 0.74, 0.56)
BLUR = 1.2  # smooths texture before downscaling, 0 to disable
GAMMA = 1.0  # < 1 brightens midtones, > 1 darkens them
CONTRAST = 1.4
AUTOCONTRAST_CUTOFF = 1  # percent of extreme pixels ignored
# Colour is lifted toward mid gray so dark pixels stay visible on dark themes
# and bright ones on light themes. 0 keeps the original colour.
COLOR_LIFT = 0.25
ALPHA_CUTOFF = 40  # pixels with alpha below this are left blank
# ----------------------------------------------------------------------------


def tone(rgba: Image.Image) -> Image.Image:
    gray = rgba.convert("RGB").convert("L")
    if BLUR:
        gray = gray.filter(ImageFilter.GaussianBlur(BLUR))
    gray = ImageOps.autocontrast(gray, cutoff=AUTOCONTRAST_CUTOFF)
    gray = gray.point(lambda v: round(255 * (v / 255) ** GAMMA))
    return ImageEnhance.Contrast(gray).enhance(CONTRAST)


def portrait_fragment(path: str = IMAGE_PATH) -> tuple[str, int, int]:
    """Return (svg <text> rows, width, height) for the ASCII portrait."""
    # Blur and tone on the full-size crop, then sample per cell, so detail is
    # not lost to resizing first.
    full = ImageOps.exif_transpose(Image.open(path)).convert("RGBA")
    w, h = full.size
    left, top, right, bottom = CROP
    full = full.crop((round(left * w), round(top * h), round(right * w), round(bottom * h)))
    rows = max(1, round(full.height / full.width * WIDTH * CHAR_W / CHAR_H))
    size = (WIDTH, rows)

    gray = tone(full).resize(size, Image.LANCZOS)
    color = full.convert("RGB").resize(size, Image.LANCZOS)
    alpha = full.getchannel("A").resize(size, Image.LANCZOS)

    ramp = RAMP[::-1] if INVERT else RAMP
    last = len(ramp) - 1
    lines = []
    for y in range(rows):
        xs, spans = [], []
        for x in range(WIDTH):
            if alpha.getpixel((x, y)) < ALPHA_CUTOFF:
                continue
            ch = ramp[round(gray.getpixel((x, y)) / 255 * last)]
            if ch == " ":
                continue
            r, g, b = (round(c + (128 - c) * COLOR_LIFT) for c in color.getpixel((x, y)))
            xs.append(f"{x * CHAR_W:g}")
            spans.append(f'<tspan fill="#{r:02x}{g:02x}{b:02x}">{escape(ch)}</tspan>')
        if spans:
            baseline = (y + 1) * CHAR_H
            lines.append(f'<text x="{" ".join(xs)}" y="{baseline:g}">{"".join(spans)}</text>')
    return "\n".join(lines), round(WIDTH * CHAR_W), round(rows * CHAR_H + 2)
