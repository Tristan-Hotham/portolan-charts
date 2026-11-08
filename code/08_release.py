"""Step 8: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24044645, https://doi.org/10.5281/zenodo.24044645 and https://blog.tristanhotham.com/2026/10/31/portolan-charts/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from PIL import Image
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks (and rebuilds index.html)
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Portolan_Charts"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
fp, fc = R["fit"]["pisana"], R["fit"]["catalan"]

# facts written in words in the blog
assert fp["atl_vs_med"] > 3                                                                  # "long arrows" vs "short"
assert fc["basins"]["Atlantic"]["own_median_km"] < fp["basins"]["Atlantic"]["own_median_km"]   # "draws the Atlantic coasts better"
assert fp["proj"]["equirect_sim"]["median_km"] <= fp["proj"]["mercator_sim"]["median_km"]
assert fc["proj"]["equirect_sim"]["median_km"] <= fc["proj"]["mercator_sim"]["median_km"]
assert R["places"]["pisana"]["best_local"][2]["local_km"] == max(b["local_km"] for b in R["places"]["pisana"]["best_local"])
assert R["places"]["pisana"]["best_local"][0]["local_km"] <= 3                                # "Messina within a few kilometres"
assert max(fp["basins"]["W Med"]["own_median_km"], fp["basins"]["E Med"]["own_median_km"]) < 50   # "less than a day's sail"
assert R["compare"]["hereford_median_km"] > R["compare"]["idrisi_affine_median_km"] > R["compare"]["ptolemy_helmert_median_km"] > max(fc["median_km"], fp["median_km"])
assert fp["bearing"]["median_abs_deg"] > 9 and fc["bearing"]["median_abs_deg"] > 9

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP, set(re.findall(r"\{\{([^|}]+)\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
C = R["counts"]
meta = {"title": "How accurate were portolan charts?",
        "slug": "portolan-charts",
        "excerpt": f"I read {C['all']} places on the Carta Pisana and the Catalan Atlas and measured them against the real coast. Both charts are turned about {R['rot_mean']:.0f} degrees off north, the Mediterranean is drawn to within a few dozen kilometres, and beyond Gibraltar they fall apart.",
        "seo_description": f"The Carta Pisana and the Catalan Atlas measured against the real coast: a tilt of about {R['rot_mean']:.0f} degrees, a superb Mediterranean and a shrunken Atlantic.",
        "tags": ["maps", "history", "portolan charts", "history of cartography", "medieval maps", "Carta Pisana", "Catalan Atlas", "data visualisation"],
        "header_alt": f"Title card on parchment reading 'How accurate were portolan charts?' in black and red lettering, beside the ragged Carta Pisana with a red grid of the true meridians and parallels bent across it and coloured dots for the places read, and the line {C['all']} places on two medieval sea charts, both turned about {R['rot_mean']:.0f} degrees off true north."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/portolan-charts_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for dd in ("code", "data", "js"):
        for fn in sorted(os.listdir(os.path.join(ROOT, dd))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, dd, fn), f"portolan-charts/{dd}/{fn}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"portolan-charts/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "portolan-charts/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("\\textit{", "").replace("}", "").replace("\\textdegree{", "°")
assert "\\" not in ab, ab
zmeta = {"title": "How Accurate Were Portolan Charts? The Carta Pisana and the Catalan Atlas Measured Against the Real Coast",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive page: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: <a href=\"https://blog.tristanhotham.com/2026/10/31/portolan-charts/\">https://blog.tristanhotham.com/2026/10/31/portolan-charts/</a>.</p><p>Sources: Carta Pisana (Bibliothèque nationale de France, Cartes et plans GE B-1118) and Catalan Atlas (BnF, Espagnol 30), public domain scans on Wikimedia Commons; E. F. Jomard's facsimile of the Carta Pisana (public domain); Natural Earth (public domain). All control points read by the author; readings and derived data CC BY 4.0.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["portolan charts", "Carta Pisana", "Catalan Atlas", "cartometry", "map accuracy", "magnetic declination", "history of cartography", "medieval maps", "thin-plate spline"],
         "license": "cc-by-4.0", "language": "eng",
         "notes": "Text, figures, readings and derived data CC BY 4.0; code MIT; the chart scans are public domain.",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23882603", "relation": "references", "resource_type": "publication-workingpaper"},
                                 {"identifier": "10.5281/zenodo.23882607", "relation": "references", "resource_type": "publication-workingpaper"},
                                 {"identifier": "10.5281/zenodo.23878612", "relation": "references", "resource_type": "publication-workingpaper"},
                                 {"identifier": PISANA_URL, "relation": "isDerivedFrom", "resource_type": "image"},
                                 {"identifier": CATALAN_URL, "relation": "isDerivedFrom", "resource_type": "image"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in sj, bad
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
