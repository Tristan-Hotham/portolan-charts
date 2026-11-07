"""Step 1: the chart images.

  * Carta Pisana: the Commons scan as it is (north up).
  * Catalan Atlas: the four chart sheets (5 to 8, west to east) are laid side by side, each cropped to its own parchment
    (found from the warm colour of the vellum against the grey scanner background) and abutted, tops level. The folds
    between the sheets hide or squeeze a strip of the drawing; 02_fit.py shifts sheets 7 and 8 by the gap measured at the
    wind rose on the 6/7 fold (see there).
  * Outputs: img/tiles_<chart>/{z}/{x}/{y}.webp (the image laid on Web Mercator pixel space, full resolution at the top
    zoom), img/<chart>_1600.jpg and _3200.jpg (whole chart, for the fallback view and the figures), data/images.json.
"""
import shutil
import numpy as np
from PIL import Image
from common import *

Image.MAX_IMAGE_PIXELS = None
info = {}


def parchment_box(a):
    w = a[..., 0].astype(int) - a[..., 2].astype(int)              # vellum is warm, the scanner background is neutral grey
    cols = np.median(w[a.shape[0] // 4: 3 * a.shape[0] // 4], axis=0)
    cx = np.where(cols > 12)[0]
    return int(cx[0]), int(cx[-1]) + 1


def tiles(chart, im):
    W, H = im.size
    T = f"{IMG}/tiles_{chart}"
    if os.path.exists(T):
        shutil.rmtree(T)
    tz = TZ[chart]
    tw, X0, Y0 = tile_geom(chart, W, H)
    n = 0
    for z in range(tz, 0, -1):
        sc = 2 ** (tz - z)
        W_, H_ = (W + sc - 1) // sc, (H + sc - 1) // sc
        lvl = im if sc == 1 else im.resize((W_, H_), Image.LANCZOS)
        ox, oy = X0 / sc, Y0 / sc
        for tx in range(int(ox // 256), int((ox + W_ - 1) // 256) + 1):
            os.makedirs(f"{T}/{z}/{tx}", exist_ok=True)
            for ty in range(int(oy // 256), int((oy + H_ - 1) // 256) + 1):
                tile = Image.new("RGB", (256, 256), (238, 230, 210))
                px, py = int(round(tx * 256 - ox)), int(round(ty * 256 - oy))
                cx0, cy0, cx1, cy1 = max(0, px), max(0, py), min(W_, px + 256), min(H_, py + 256)
                tile.paste(lvl.crop((cx0, cy0, cx1, cy1)), (cx0 - px, cy0 - py))
                tile.save(f"{T}/{z}/{tx}/{ty}.webp", "WEBP", quality=58 if z == tz else 66, method=6)
                n += 1
    mb = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(T) for f in fs) / 1e6
    print(chart, "tiles", n, "MB", round(mb, 1))
    for w in (1600, 3200):
        im.resize((w, round(H * w / W)), Image.LANCZOS).save(f"{IMG}/{chart}_{w}.jpg", quality=80 if w == 1600 else 74, optimize=True, progressive=True)
    lo0, la0 = px2ll(chart, 0, 0, W, H)
    lo1, la1 = px2ll(chart, W, H, W, H)
    return {"w": W, "h": H, "tz": tz, "tworld": tw, "x0": X0, "y0": Y0, "bounds": [[lo0, la1], [lo1, la0]], "tiles_mb": round(mb, 1)}


# ---------- Carta Pisana
pis = Image.open(f"{RAW}/Carte_Pisane_Portolan.jpg").convert("RGB")
assert pis.size == (PISANA_W, PISANA_H), pis.size
info["pisana"] = tiles("pisana", pis)

# ---------- Catalan Atlas: sheets 5 to 8 abutted
sheets, boxes = [], {}
for s in CAT_SHEETS:
    im = Image.open(f"{RAW}/Catalan_Atlas_sheet_{s}_half.jpg").convert("RGB")
    x0, x1 = parchment_box(np.asarray(im))
    boxes[s] = {"x0": x0, "x1": x1, "w": im.size[0], "h": im.size[1]}
    sheets.append(im.crop((x0, 0, x1, im.size[1])))
H = max(i.size[1] for i in sheets)
W = sum(i.size[0] for i in sheets)
cat = Image.new("RGB", (W, H), (226, 226, 220))
off = 0
for s, im in zip(CAT_SHEETS, sheets):
    cat.paste(im, (off, 0))
    boxes[s]["mosaic_x"] = off - boxes[s]["x0"]          # sheet pixel x + mosaic_x = mosaic pixel x
    off += im.size[0]
print("catalan mosaic", cat.size, {s: (b["x0"], b["x1"]) for s, b in boxes.items()})
info["catalan"] = tiles("catalan", cat)
info["catalan"]["sheets"] = boxes
jsave(info, f"{DATA}/images.json", indent=1)
