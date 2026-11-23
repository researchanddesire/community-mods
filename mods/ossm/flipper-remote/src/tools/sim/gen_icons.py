# Turns flipper_app/images/*.png into a host header (XBM rows, LSB first).
import os, sys
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
with open(out, "w") as f:
    f.write("#pragma once\n#include <gui/gui.h>\n")
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".png"): continue
        name = fn[:-4]
        im = Image.open(os.path.join(src, fn)).convert("1")
        w, h = im.size
        stride = (w + 7) // 8
        data = []
        for y in range(h):
            row = [0] * stride
            for x in range(w):
                if im.getpixel((x, y)) == 0: row[x // 8] |= 1 << (x % 8)
            data += row
        f.write(f"static const uint8_t _d_{name}[] = {{{','.join(map(str, data))}}};\n")
        f.write(f"static const Icon I_{name} = {{{w}, {h}, _d_{name}}};\n")
