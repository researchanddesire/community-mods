#!/bin/sh
# Usage: FZ=/path/to/flipperzero-firmware tools/sim/build_and_render.sh
set -e
cd "$(dirname "$0")"
: "${FZ:?set FZ to a flipperzero-firmware checkout (for lib/u8g2)}"
mkdir -p build out
python3 gen_icons.py ../../flipper_app/images build/ossm_remote_icons.h
U8=$(ls "$FZ"/lib/u8g2/*.c | grep -v u8g2_glue.c)
cc -O1 -w -Iinclude -Ibuild -I"$FZ/lib/u8g2" -ffunction-sections -fdata-sections -Wl,--gc-sections -o build/render \
  render.c host_canvas.c ../../flipper_app/ossm_ui.c $U8 -lm
./build/render
python3 - <<'PY'
import glob, os
from PIL import Image
frames = []
for fn in sorted(glob.glob("out/*.pbm")):
    im = Image.open(fn).convert("1")
    # Flipper look: black pixels on the orange backlit LCD, 4x upscale
    rgb = Image.new("RGB", im.size)
    px = [(0x1d, 0x10, 0x00) if p == 0 else (0xff, 0x8c, 0x29) for p in im.getdata()]
    # PBM: 1 = black; PIL loads as 0 = black
    rgb.putdata(px)
    big = rgb.resize((512, 256), Image.NEAREST)
    pad = Image.new("RGB", (544, 288), (0x22, 0x22, 0x22))
    pad.paste(big, (16, 16))
    pad.save(fn[:-4] + ".png")
    frames.append(pad)
    os.remove(fn)
cols = 3
rows = (len(frames) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 544, rows * 288), (0x22, 0x22, 0x22))
for i, f in enumerate(frames):
    sheet.paste(f, ((i % cols) * 544, (i // cols) * 288))
sheet.save("out/contact_sheet.png")
print(len(frames), "screens rendered")
PY
