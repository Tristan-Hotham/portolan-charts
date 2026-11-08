"""Step 4: index.html from code/page_template.html and data/results.json, with the facts written in words checked.
10.5281/zenodo.24044645, https://doi.org/10.5281/zenodo.24044645 and https://blog.tristanhotham.com/2026/10/31/portolan-charts/ stay as placeholders for the publisher."""
import re, time
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# ---- facts stated in words (page, blog, paper, collage)
fp, fc = R["fit"]["pisana"], R["fit"]["catalan"]
assert [b["name"] for b in R["places"]["pisana"]["best_local"]] == ["Capo Peloro, Messina", "Almeria", "Sidon"]
assert all(b["local_km"] <= 5 for b in R["places"]["pisana"]["best_local"])          # "within a few kilometres"
assert R["places"]["catalan"]["worst"][0]["name"] == "Dunnet Head"
assert fp["bearing"]["neg_pct"] > 90 and fc["bearing"]["neg_pct"] > 90
assert abs(fp["basins"]["W Med"]["rot_deg"] - fp["basins"]["E Med"]["rot_deg"]) < 1     # "almost the same amount"
assert abs(fp["rot_deg"] - fc["rot_deg"]) < 2                                            # "about the same size"
assert R["counts"]["pisana"]["basins"]["Black Sea"] < 5
assert fc["free"]["median_km"] >= fc["median_km"]                                          # "no better"
assert R["compare"]["ratio_ptolemy_pisana"] >= 1.4

rows = ""
for ch in ("pisana", "catalan"):
    for b, x in R["fit"][ch]["basins"].items():
        if x["n"] < 5:
            continue
        own = f"{x['own_median_km']}" if "own_median_km" in x else ""
        rot = f"{x['rot_deg']:.1f}°" if "rot_deg" in x else ""
        sc = f"{x['rel_scale']:.2f}" if "rel_scale" in x else ""
        rows += (f"<tr><td>{CHARTS[ch]['name']}: {dict((v, k) for k, v in BSHORT.items())[b]}</td><td class=\"r\">{x['n']}</td>"
                 f"<td class=\"r\">{x['global_median_km']}</td><td class=\"r\">{own}</td><td class=\"r\">{rot}</td><td class=\"r\">{sc}</td></tr>")

t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
fs = open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read()
t = t.replace("{{TABLE_BASINS}}", rows).replace("{{FULLSCREEN}}", fs)
t = t.replace("{{BYLINE}}", BYLINE).replace("{{AI}}", AI).replace("{{VERSION}}", time.strftime("%Y%m%d"))
t = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
assert t.count("https://maps.tristanhotham.com/assets/site-nav.js") == 1 and t.index("assets/site-nav.js") < t.index("</body>")   # the site menu
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
js = open(os.path.join(ROOT, "js", "page.js"), encoding="utf-8").read()
assert "—" not in js and "–" not in js
print("index.html", len(t) // 1024, "KB")
