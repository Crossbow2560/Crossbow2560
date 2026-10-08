"""Convert the portrait image to ASCII and embed it in README.md.

The art is written between the ASCII-START and ASCII-END markers.
"""

import html
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

# ---- Settings (edit these) -------------------------------------------------
IMAGE_PATH = "assets/portrait.jpg"
README_PATH = "README.md"
WIDTH = 90  # output columns, roughly 80 to 100 works well
# Ordered from darkest to brightest pixel. Light-on-dark: dense characters
# mark bright areas. Reverse the string for dark-on-light themes.
RAMP = " .:-=+*#%@"
# Terminal characters are about twice as tall as wide.
CHAR_ASPECT = 0.5
# Crop box as fractions of the image: (left, top, right, bottom).
CROP = (0.22, 0.07, 0.84, 0.70)
# Blur radius in source pixels. Smooths stone and fabric texture so the face
# shapes survive the downscale. Set to 0 to disable.
BLUR = 3
# Tone tuning. GAMMA < 1 brightens midtones (useful for a dark subject on a
# light-on-dark ramp), > 1 darkens them. CONTRAST > 1 stretches around mid gray.
GAMMA = 0.7
CONTRAST = 1.3
AUTOCONTRAST_CUTOFF = 2  # percent of extreme pixels ignored
# Soft elliptical focus: pixels outside fade to the blank end of the ramp,
# which hides the background. Fractions of the cropped area:
# (left, top, right, bottom) of the ellipse. Set to None to disable.
FOCUS = (0.12, 0.0, 0.88, 0.80)
FOCUS_FEATHER = 0.05  # blur radius as a fraction of the crop width
# ----------------------------------------------------------------------------

START = "<!-- ASCII-START -->"
END = "<!-- ASCII-END -->"


def apply_focus(img: Image.Image) -> Image.Image:
    cw, ch = img.size
    left, top, right, bottom = FOCUS
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse((cw * left, ch * top, cw * right, ch * bottom), fill=255)
    # Keep the shoulders: everything below the ellipse's widest point stays visible.
    ImageDraw.Draw(mask).rectangle((cw * 0.02, ch * 0.72, cw * 0.98, ch), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(cw * FOCUS_FEATHER))
    return Image.composite(img, Image.new("L", img.size, 0), mask)


def image_to_ascii(path: str, width: int, ramp: str) -> str:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("L")
    w, h = img.size
    left, top, right, bottom = CROP
    img = img.crop((round(left * w), round(top * h), round(right * w), round(bottom * h)))
    if BLUR:
        img = img.filter(ImageFilter.GaussianBlur(BLUR))
    img = ImageOps.autocontrast(img, cutoff=AUTOCONTRAST_CUTOFF)
    img = img.point(lambda v: round(255 * (v / 255) ** GAMMA))
    if FOCUS:
        img = apply_focus(img)
    img = ImageEnhance.Contrast(img).enhance(CONTRAST)
    height = max(1, round(img.height / img.width * width * CHAR_ASPECT))
    img = img.resize((width, height), Image.LANCZOS)

    last = len(ramp) - 1
    pixels = img.tobytes()
    rows = []
    for y in range(height):
        row = pixels[y * width:(y + 1) * width]
        rows.append("".join(ramp[round(p / 255 * last)] for p in row).rstrip())
    return "\n".join(rows)


def update_readme(readme: str, art: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(readme):
        raise SystemExit(f"Markers {START} and {END} not found in README")
    block = f"{START}\n{html.escape(art)}\n{END}"
    return pattern.sub(lambda _: block, readme, count=1)


def main() -> None:
    art = image_to_ascii(IMAGE_PATH, WIDTH, RAMP)
    readme = Path(README_PATH)
    readme.write_text(update_readme(readme.read_text(encoding="utf-8"), art), encoding="utf-8")


if __name__ == "__main__":
    main()
