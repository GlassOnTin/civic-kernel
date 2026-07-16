#!/usr/bin/env python3
"""Regenerate tropes.html's trope-web from the corpus — a field guide to how
public power goes wrong, built from the data so it cannot drift.

Two finite vocabularies of failure, and the cases under each:
  - the STRUCTURAL SHAPES (triage signatures, tools/triage.py) over the triaged cases;
  - the kernel's own fourteen THREATS (§2), tagged on every scenario.

Run: python3 tools/tropes.py   (fills the <!--TROPES-START-->..<!--TROPES-END--> region)
"""
import json, re, glob, pathlib, sys, html, itertools, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from triage import SIGNATURES  # the shape vocabulary, single source of truth


def esc(s):
    return html.escape(str(s))


# scenarios: id -> {title, verdict, threats}
scen = {}
for f in glob.glob(str(ROOT / "scenarios" / "*.json")):
    if f.endswith("scenario.schema.json"):
        continue
    d = json.loads(pathlib.Path(f).read_text())
    scen[d["id"]] = {"title": d["title"], "verdict": d["verdict"], "threats": d.get("threats", [])}

# triage cases: signatures + which map to a built scenario
cases = json.loads((ROOT / "triage" / "cases.json").read_text())["cases"]

# threat names, parsed from the KERNEL.md threat table (drift-free)
threat_name = {}
for m in re.finditer(r'^\| (T\d+) \| (.+?) \|', (ROOT / "KERNEL.md").read_text(), re.M):
    threat_name[m.group(1)] = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', m.group(2)).strip()


def badge(v):
    return f'<span class="b {esc(v)}">{esc(v)}</span>' if v else ''


def case_link(sid):
    s = scen.get(sid)
    return f'<a href="scenarios.html#{esc(sid)}">{esc(s["title"])}</a> {badge(s["verdict"])}' if s else esc(sid)


out = []

# ---- The shapes ----
out.append('<h2>The shapes</h2>')
out.append('<p class="lede2">Six structural forms the institutional-failure cases keep taking — the cross-cutting tropes the triage engine sorts by. Most wrongs wear more than one.</p>')
sig_cases = collections.defaultdict(list)
for c in cases:
    for s in c.get("signature", []):
        sig_cases[s].append(c)
for sig, desc in SIGNATURES.items():
    cs = sig_cases.get(sig, [])
    enc = [c for c in cs if c.get("status") == "encoded" and c.get("scenario")]
    cand = [c for c in cs if c.get("status") == "candidate"]
    out.append('<section class="trope">')
    out.append(f'<h3>{esc(sig)} <span style="color:var(--muted)">· {len(enc)}</span></h3>')
    out.append(f'<p>{esc(desc)}.</p>')
    if enc:
        out.append('<ul class="cases">')
        for c in enc:
            out.append(f'<li>{case_link(c["scenario"])}</li>')
        out.append('</ul>')
    if cand:
        out.append('<p class="cand">Awaiting a scenario: ' + ", ".join(esc(c["id"]) for c in cand) + '.</p>')
    out.append('</section>')

# intersections — where two shapes co-occur across >=2 built cases (the web made literal)
pair = collections.defaultdict(list)
for c in cases:
    if c.get("status") != "encoded" or not c.get("scenario"):
        continue
    for a, b in itertools.combinations(sorted(c.get("signature", [])), 2):
        pair[(a, b)].append(c)
inter = sorted([(p, cs) for p, cs in pair.items() if len(cs) >= 2], key=lambda x: -len(x[1]))
if inter:
    out.append('<section class="trope inter">')
    out.append('<h3>Where the shapes meet</h3>')
    out.append('<p>The intersections — where two forms co-occur, the web made literal:</p>')
    out.append('<ul class="cases">')
    for (a, b), cs in inter:
        out.append(f'<li><b>{esc(a)} × {esc(b)}</b> — ' + ", ".join(case_link(c["scenario"]) for c in cs) + '</li>')
    out.append('</ul>')
    out.append('</section>')

# ---- The threats ----
out.append('<h2>The threats</h2>')
out.append("<p class=\"lede2\">The kernel's own vocabulary: fourteen enumerated ways power fails, named before the design was drawn (§2). Every stress-test carries the threats it exercises.</p>")
threat_scen = collections.defaultdict(list)
for sid, s in scen.items():
    for t in s["threats"]:
        threat_scen[t].append(sid)
for t in sorted(threat_scen, key=lambda x: int(x[1:])):
    out.append('<section class="trope">')
    out.append(f'<h3>{esc(t)} — {esc(threat_name.get(t, ""))} <span style="color:var(--muted)">· {len(threat_scen[t])}</span></h3>')
    out.append('<ul class="cases">')
    for sid in sorted(threat_scen[t]):
        out.append(f'<li>{case_link(sid)}</li>')
    out.append('</ul>')
    out.append('</section>')

# live count line at the top, so the page never hardcodes a total that drifts
out.insert(0, f'<p class="stat">{len(scen)} scenarios &middot; {len(SIGNATURES)} shapes &middot; {len(threat_scen)} threats in play &middot; nothing cherry-picked</p>')

fragment = "\n".join(out)

page = ROOT / "tropes.html"
new, n = re.subn(r'(<!--TROPES-START-->).*?(<!--TROPES-END-->)',
                 lambda m: m.group(1) + "\n" + fragment + "\n" + m.group(2),
                 page.read_text(), count=1, flags=re.S)
assert n == 1, "TROPES markers not found in tropes.html"
page.write_text(new)
print(f"tropes.html regenerated: {len([s for s in SIGNATURES])} shapes, "
      f"{len(threat_scen)} threats in play, {len(scen)} scenarios, {len(inter)} shape-intersections")
