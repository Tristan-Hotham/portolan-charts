"""Step 6: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Portolan_Charts.pdf and .tex beside the f_*.png figures. The DOI stays as a 10.5281/zenodo.24044645 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Portolan_Charts"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
for ch in ("pisana", "catalan"):
    B = R["fit"][ch]["basins"]
    assert R["fit"][ch]["proj"]["local_sim"]["median_km"] > R["fit"][ch]["proj"]["equirect_sim"]["median_km"]   # "a local azimuthal frame fits worse"
    assert R["fit"][ch]["aff_median_km"] <= R["fit"][ch]["median_km"]
assert {w["name"] for w in R["places"]["catalan"]["worst"][:2]} == {"Dunnet Head", "Malin Head"}                # "worst places in Scotland and Ireland"
assert R["transfer"]["local_facsimile_km"] > R["transfer"]["local_scan_km"]


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


NAMES = {v: k for k, v in BSHORT.items()}
rows = ""
for ch in ("pisana", "catalan"):
    for b, x in R["fit"][ch]["basins"].items():
        rows += (f"{CHARTS[ch]['name']} & {NAMES[b]} & {x['n']} & {x['global_median_km']} & {x.get('own_median_km', '')} & "
                 f"{'' if 'rot_deg' not in x else format(x['rot_deg'], '.1f')} & {'' if 'rel_scale' not in x else format(x['rel_scale'], '.2f')} & "
                 f"{R['fit'][ch]['local_basins'].get(b, '')}\\\\\n")
TB = ("\\begin{table}[tbp]\\centering\\small\\caption{Errors by basin (medians, km): under the whole-chart similarity fit, under the basin's own fit "
      "(with its rotation in degrees and its scale relative to the whole chart), and the local error from the eight nearest neighbours.}\\label{tab:basins}"
      "\\begin{tabular}{llrrrrrr}\\toprule Chart & Basin & n & Whole & Own & Turn & Scale & Local\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
PRJ = [("mercator", "Mercator"), ("equirect", "Equirectangular, 38\\textdegree{} N"), ("local", "Azimuthal equidistant")]
rows = ""
for ch in ("pisana", "catalan"):
    for k, n in PRJ:
        s, a = R["fit"][ch]["proj"][f"{k}_sim"], R["fit"][ch]["proj"][f"{k}_aff"]
        rows += f"{CHARTS[ch]['name']} & {n} & {s['median_km']} & {s['p90_km']} & {s['rot_deg']:.1f} & {a['median_km']} & {a['p90_km']}\\\\\n"
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{Fits in three projections: median and 90th percentile error (km) and rotation (degrees) of the similarity fit, "
      "and median and 90th percentile error of the affine fit.}\\label{tab:proj}"
      "\\begin{tabular}{llrrrrr}\\toprule Chart & Projection & Median & P90 & Turn & Affine median & Affine P90\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{TABLE_BASINS}}", TB).replace("{{TABLE_PROJ}}", TP)
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
assert "{{" not in t.replace("\\{\\{DOI\\}\\}", "") and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
# the two figures made from the scans are photographs: embed them as JPEG to keep the PDF small
from PIL import Image
for nm in ("f_charts", "f_reading"):
    png, jpg = os.path.join(OUT, nm + ".png"), os.path.join(OUT, nm + ".jpg")
    if os.path.exists(png):
        Image.open(png).convert("RGB").save(jpg, quality=88, optimize=True); os.remove(png)
    assert os.path.exists(jpg), jpg
    t = t.replace("{" + nm + ".png}", "{" + nm + ".jpg}")
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
