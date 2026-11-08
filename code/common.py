"""Shared paths, constants and helpers for the portolan-charts study ("How accurate were portolan charts?").

Raw inputs (read in place, never modified; from step 02 onward only data/ and img/ are needed):
  RAW/Carte_Pisane_Portolan.jpg
      The Carta Pisana (c. 1275), Bibliotheque nationale de France, Cartes et plans GE B-1118 (RES). Wikimedia Commons
      scan, 3,481 x 1,848 px, public domain (PD-Art).
  RAW/Carte_Pisane_Jomard.png
      E. F. Jomard's lithographed facsimile of the Carta Pisana (Les monuments de la geographie, 1842 to 1862), Wikimedia
      Commons, 5,352 x 3,061 px, public domain. Used only to help read the faded names; every position is carried back to
      the original scan (see 02_fit.py).
  RAW/Catalan_Atlas_sheet_{1..8}_half.jpg
      The Catalan Atlas (1375), BnF Espagnol 30, Wikimedia Commons per-sheet scans reduced to half size (about 3,230 x
      7,900 px each), public domain (PD-Art). Sheets 1 to 4 are the cosmography and calendar; sheets 5 to 8 are the chart,
      west to east, north up.
  GEO/ne_10m_admin_0_countries.geojson (coast check), ne_50m_land.geojson (grid and coast lines)   Natural Earth, public domain.

Inputs written by hand (data/):
  readings_pisana_scan.csv     points read directly on the Pisana scan (pixel x, y on RAW/Carte_Pisane_Portolan.jpg)
  readings_pisana_jomard.csv   names read on Jomard's facsimile (pixel x, y on RAW/Carte_Pisane_Jomard.png)
  pisana_rhumb_nodes.csv       the centres of the two wind-rose circles' 16 nodes, on the facsimile and on the scan
  readings_catalan.csv         points read on the Catalan Atlas chart sheets (sheet, pixel x, y on the half-size scan)
Each reading has my identification, its modern latitude and longitude (typed by me from my own knowledge of the coasts,
checked against Natural Earth coastlines in 02_fit.py) and a confidence flag: 1 the name is clear and the place certain,
2 probable, 3 the place is certain but its exact point on the chart (or the reading of the name) is doubtful.
"""
import json, gzip, os, re, unicodedata, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PC_RAW", "/home/claude/newdata/raw_new6/portolan")
GEO = os.environ.get("PC_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("PC_FONTS", "/home/claude/ref/fonts")
INK = os.environ.get("PC_INK", "/home/claude/studies/ink-map")
INKFONTS = os.path.join(INK, "fonts", "ttf")
PTOLEMY = os.environ.get("PC_PTOLEMY", "/home/claude/studies/ptolemy/data/results.json")
HEREFORD = os.environ.get("PC_HEREFORD", "/home/claude/studies/mappa-mundi/data/results.json")
IDRISI = os.environ.get("PC_IDRISI", "/home/claude/studies/idrisi/data/results.json")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
WORK = os.path.join(os.environ.get("PCTMP", "/home/claude/work/new6/portolan-charts"), "work")
for d in (DATA, IMG, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "portolan-charts"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
PTOLEMY_PAGE = "https://maps.tristanhotham.com/ptolemy/"
HEREFORD_PAGE = "https://maps.tristanhotham.com/mappa-mundi/"
IDRISI_PAGE = "https://maps.tristanhotham.com/idrisi/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
PISANA_URL = "https://commons.wikimedia.org/wiki/File:Carte_Pisane.jpg"
JOMARD_URL = "https://commons.wikimedia.org/wiki/Category:Carta_Pisana"
CATALAN_URL = "https://commons.wikimedia.org/wiki/Category:Catalan_Atlas"
PISANA_BNF = "https://gallica.bnf.fr/ark:/12148/btv1b52503226n"
CATALAN_BNF = "https://gallica.bnf.fr/ark:/12148/btv1b55002481n"

# the two charts
CHARTS = {"pisana": {"name": "Carta Pisana", "date": "c. 1275", "short": "Pisana"},
          "catalan": {"name": "Catalan Atlas", "date": "1375", "short": "Catalan"}}
PISANA_W, PISANA_H = 3481, 1848
CAT_SHEETS = [5, 6, 7, 8]

# sea basins, in display order, with ink colours
BASINS = [("Western Mediterranean", "#A3261B"), ("Eastern Mediterranean", "#3D6E9E"), ("Black Sea", "#2E7F86"), ("Atlantic coasts", "#8C6A43")]
BCOL = dict(BASINS)
BNAMES = [b for b, _ in BASINS]
BSHORT = {"Western Mediterranean": "W Med", "Eastern Mediterranean": "E Med", "Black Sea": "Black Sea", "Atlantic coasts": "Atlantic"}


def basin(lat, lon):
    """Sea basin of a coastal point. Atlantic: outside Gibraltar or on the Biscay, Channel, North Sea and Baltic coasts
    and the Atlantic islands. Black Sea: the Black Sea, the Bosporus and the Sea of Azov (north of 40.95 N east of 28.5 E, and north of
    40.5 N east of 36.5 E for the Pontic coast east of Samsun). Mediterranean split at the line from
    Cape Bon to Sicily and up the Strait of Messina (16 degrees east), with the whole Adriatic in the east (east of
    13.4 E north of 41.5 N, and east of 12 E north of 43 N)."""
    if lon < -5.5 or (lat > 43.2 and lon < -1.0) or (lat > 46.5 and lon < 10) or (lat > 50 and lon < 30):
        return "Atlantic coasts"
    if (lat > 40.95 and lon > 28.5) or (lat > 40.5 and lon > 36.5):
        return "Black Sea"
    if lon >= 16.0 or (lat > 41.5 and lon > 13.4) or (lat > 43.0 and lon > 12.0):
        return "Eastern Mediterranean"
    return "Western Mediterranean"


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and v != v:
        return None
    if isinstance(v, list):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "abs": return f"{abs(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "absf1": return f"{abs(float(v)):.1f}"
    raise ValueError(f)


def gc_km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


# Mercator and plate carree on the unit sphere, in degrees of the equator (so 1 unit = 111.2 km at the equator)
def merc(lat, lon):
    import numpy as np
    return np.asarray(lon, float), np.degrees(np.log(np.tan(np.pi / 4 + np.radians(np.asarray(lat, float)) / 2)))


def merc_inv(x, y):
    import numpy as np
    return np.degrees(2 * np.arctan(np.exp(np.radians(np.asarray(y, float)))) - np.pi / 2), np.asarray(x, float)


def plate(lat, lon):
    import numpy as np
    return np.asarray(lon, float), np.asarray(lat, float)


def plate_inv(x, y):
    import numpy as np
    return np.asarray(y, float), np.asarray(x, float)


# Web tiles: each chart image is laid on Web Mercator pixel space at zoom TZ, at full resolution, centred.
TZ = {"pisana": 4, "catalan": 6}


def tile_geom(chart, w, h):
    tw = 256 * 2 ** TZ[chart]
    return tw, (tw - w) // 2, (tw - h) // 2


def px2ll(chart, x, y, w, h):
    """Pixel on a chart image to the pseudo longitude and latitude used to show the image in MapLibre."""
    tw, x0, y0 = tile_geom(chart, w, h)
    X, Y = x0 + x, y0 + y
    lon = X / tw * 360 - 180
    n = math.pi - 2 * math.pi * Y / tw
    return round(lon, 6), round(math.degrees(math.atan(math.sinh(n))), 6)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()
