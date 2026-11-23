#!/usr/bin/env python3
"""Generate the 1-bit PNG icons in flipper_app/images.

Pixel art lives here as text ('#' = lit pixel) so the icons stay easy to
tweak. Run from the repo root:  python3 tools/make_icons.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "flipper_app", "images")

ART = {
    # Open source hardware gear: hole in the middle, slot open at the bottom.
    "gear_15": """
......###......
..##..###..##..
..###########..
...#########...
.####.....####.
.###.......###.
####.......####
####.......####
.###.......###.
.####.....####.
...###...###...
..####...####..
..##.......##..
""",
    "gear_11": """
....###....
.##.###.##.
.#########.
..##...##..
###.....###
###.....###
..##...##..
.###...###.
.##.....##.
""",
    # 10x10 app icon: OSSM silhouette (motor block + rod)
    "ossm_10px": """
..........
.####.....
.#..#.....
.#..######
.#..#....#
.#..######
.#..#.....
.####.....
..#..#....
..........
""",
    # 7x7 parameter glyphs
    "ic_speed": """
...###.
..#...#
.#...#.
.#..#.#
.#.#..#
..#...#
.......
""",
    "ic_depth": """
...#...
...#...
...#...
.#.#.#.
..###..
...#...
#######
""",
    "ic_stroke": """
.#...#.
##...##
#######
##...##
.#...#.
.......
.......
""",
    "ic_sens": """
.......
.#...#.
#.#.#.#
#..#..#
.......
.......
.......
""",
    "ic_pattern": """
.......
#..#..#
##.##.#
#.#.#.#
#...#..
.......
.......
""",
    # 9x8 heart for the beat indicator
    "heart": """
.##...##.
####.####
#########
#########
.#######.
..#####..
...###...
....#....
""",
    # 15x10 Flipper-to-bridge plug glyph for the "no bridge" screen
    "plug": """
.....######....
.....#....#....
######....#####
.....#....#....
.....######....
....#......#...
....#.####.#...
....#......#...
....########...
...............
""",
}


def from_art(name, art):
    rows = [r for r in art.strip("\n").split("\n")]
    w = max(len(r) for r in rows)
    img = Image.new("1", (w, len(rows)), 1)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == "#":
                img.putpixel((x, y), 0)
    img.save(os.path.join(OUT, name + ".png"))


def mode_stroke():
    """24x24: sine wave through a rounded frame -- Stroke Engine."""
    img = Image.new("1", (24, 24), 1)
    d = ImageDraw.Draw(img)
    pts = []
    for x in range(2, 22):
        y = 12 - 7 * math.sin((x - 2) / 19 * 2 * math.pi)
        pts.append((x, round(y)))
    d.line(pts, fill=0, width=2)
    d.line([(1, 21), (22, 21)], fill=0)
    for x in range(1, 23, 3):
        d.point((x, 22), fill=0)
    img.save(os.path.join(OUT, "mode_stroke.png"))


def mode_simple():
    """24x24: machine body with a rod and arrows -- Simple Penetration."""
    img = Image.new("1", (24, 24), 1)
    d = ImageDraw.Draw(img)
    d.rectangle([1, 5, 9, 18], outline=0)
    d.rectangle([3, 7, 7, 16], fill=0)
    d.rectangle([10, 10, 20, 13], fill=0)
    d.ellipse([18, 8, 23, 15], fill=0)
    # double arrow under the rod
    d.line([(11, 21), (21, 21)], fill=0)
    d.line([(11, 21), (13, 19)], fill=0)
    d.line([(11, 21), (13, 23)], fill=0)
    d.line([(21, 21), (19, 19)], fill=0)
    d.line([(21, 21), (19, 23)], fill=0)
    img.save(os.path.join(OUT, "mode_simple.png"))


def stop_sign():
    """40x40 octagon; the app writes STOP over it in XOR."""
    img = Image.new("1", (40, 40), 1)
    d = ImageDraw.Draw(img)
    c, r = 19.5, 19.5
    pts = [
        (c + r * math.cos(math.radians(22.5 + 45 * i)),
         c + r * math.sin(math.radians(22.5 + 45 * i)))
        for i in range(8)
    ]
    d.polygon(pts, fill=0)
    r2 = 16.5
    pts2 = [
        (c + r2 * math.cos(math.radians(22.5 + 45 * i)),
         c + r2 * math.sin(math.radians(22.5 + 45 * i)))
        for i in range(8)
    ]
    d.polygon(pts2, outline=1)
    img.save(os.path.join(OUT, "stop_40.png"))


def knob():
    """16x16 knob turned to zero, for the preflight hint."""
    img = Image.new("1", (16, 16), 1)
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, 14, 14], outline=0)
    d.ellipse([3, 3, 12, 12], fill=0)
    d.line([(7, 7), (4, 11)], fill=1, width=2)
    img.save(os.path.join(OUT, "knob_16.png"))


def logo():
    """Wordmark for the splash screen."""
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    text = "OSSM"
    bbox = font.getbbox(text)
    w, h = bbox[2] - bbox[0] + 2, bbox[3] - bbox[1] + 2
    img = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(img)
    d.text((1 - bbox[0], 1 - bbox[1]), text, font=font, fill=0)
    img = img.point(lambda p: 0 if p < 140 else 255).convert("1")
    img.save(os.path.join(OUT, "logo.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, art in ART.items():
        from_art(name, art)
    mode_stroke()
    mode_simple()
    stop_sign()
    knob()
    logo()
    for f in sorted(os.listdir(OUT)):
        im = Image.open(os.path.join(OUT, f))
        print(f, im.size)

