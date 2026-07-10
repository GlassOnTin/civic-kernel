#!/usr/bin/env python3
"""Validate every scenario in scenarios/*.json and rebuild the data blob in scenarios.html.

Requires: pip install jsonschema

Checks, per scenario:
  1. the scenario record against scenarios/scenario.schema.json
  2. the embedded manifest against schema/manifest.schema.json      (the waist test)
  3. every embedded log-entry artifact against schema/log-entry.schema.json
  4. artifact timestamps are chronological and communities match the manifest

Exit 0 = all pass and scenarios.html blob rebuilt; exit 1 = failures listed on stderr.
"""
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCENARIO_SCHEMA = json.loads((ROOT / "scenarios" / "scenario.schema.json").read_text())
MANIFEST_SCHEMA = json.loads((ROOT / "schema" / "manifest.schema.json").read_text())
LOG_SCHEMA = json.loads((ROOT / "schema" / "log-entry.schema.json").read_text())

v_scenario = Draft202012Validator(SCENARIO_SCHEMA)
v_manifest = Draft202012Validator(MANIFEST_SCHEMA)
v_log = Draft202012Validator(LOG_SCHEMA)


def check(path: Path) -> list[str]:
    errs = []
    try:
        s = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"unparseable JSON: {e}"]

    errs += [f"scenario: {e.message} at {'/'.join(map(str, e.path))}" for e in v_scenario.iter_errors(s)]
    if not isinstance(s, dict):
        return errs
    errs += [f"manifest: {e.message} at {'/'.join(map(str, e.path))}" for e in v_manifest.iter_errors(s.get("manifest", {}))]

    community = s.get("manifest", {}).get("community", {}).get("id")
    prev_ts = None
    for i, step in enumerate(s.get("walkthrough", [])):
        a = step.get("artifact")
        if not a:
            continue
        errs += [f"walkthrough[{i}].artifact: {e.message} at {'/'.join(map(str, e.path))}" for e in v_log.iter_errors(a)]
        ts = a.get("timestamp", "")
        if prev_ts and ts < prev_ts:
            errs.append(f"walkthrough[{i}].artifact: timestamp {ts} earlier than previous {prev_ts}")
        prev_ts = ts or prev_ts

    n_artifacts = sum(1 for st in s.get("walkthrough", []) if st.get("artifact"))
    if n_artifacts < 3:
        errs.append(f"only {n_artifacts} embedded log entries; need >= 3")
    if community and any(
        st.get("artifact", {}).get("community") not in (community, s.get("manifest", {}).get("transparency_log", {}).get("log_id"))
        for st in s.get("walkthrough", []) if st.get("artifact")
    ):
        errs.append("an artifact's community differs from the manifest's community id / log id")
    return errs


def main() -> int:
    files = sorted((ROOT / "scenarios").glob("*.json"))
    files = [f for f in files if f.name != "scenario.schema.json"]
    if not files:
        print("no scenario files found", file=sys.stderr)
        return 1

    scenarios, failed = [], 0
    for f in files:
        errs = check(f)
        if errs:
            failed += 1
            print(f"FAIL {f.name}", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
        else:
            print(f"ok   {f.name}")
            scenarios.append(json.loads(f.read_text()))

    if failed:
        print(f"\n{failed}/{len(files)} scenario(s) failed; scenarios.html not rebuilt", file=sys.stderr)
        return 1

    page = ROOT / "scenarios.html"
    html = page.read_text()
    blob = json.dumps(scenarios, ensure_ascii=False, indent=1).replace("</", "<\\/")
    new = re.sub(
        r'(<script id="scenario-data" type="application/json">).*?(</script>)',
        lambda m: m.group(1) + "\n" + blob + "\n" + m.group(2),
        html, count=1, flags=re.S,
    )
    if new == html and blob not in html:
        print("scenario-data block not found in scenarios.html", file=sys.stderr)
        return 1
    page.write_text(new)
    print(f"\n{len(scenarios)} scenario(s) valid; scenarios.html rebuilt")

    # doc_ref previews: the essay's Plainly lines and threat register, injected
    # as generated data so the page cannot drift from the essay
    essay_html = (ROOT / "index.html").read_text()
    plains = {}
    for m in re.finditer(r'<p class="plain"><span class="plain-label">Plainly</span>(.*?)</p>', essay_html, re.S):
        ids = re.findall(r'id="(s[0-9-]+|words)"', essay_html[: m.start()])
        if ids and ids[-1] not in plains:
            plains[ids[-1]] = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    threats = {}
    for m in re.finditer(r'<td class="tid">(T\d+)</td>\s*<td><span class="threat-name">(.*?)</span>(.*?)</td>', essay_html, re.S):
        txt = re.sub(r"<[^>]+>", "", m.group(2) + m.group(3)).strip()
        for ent, ch in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
            txt = txt.replace(ent, ch)
        threats[m.group(1)] = txt
    if len(threats) != 14:
        print(f"FAIL preview data: expected 14 threats from the essay, got {len(threats)}", file=sys.stderr)
        return 1
    pblob = json.dumps({"sections": plains, "threats": threats}, ensure_ascii=False, indent=1).replace("</", "<\\/")
    html = page.read_text()
    new = re.sub(
        r'(<script id="preview-data" type="application/json">).*?(</script>)',
        lambda m: m.group(1) + "\n" + pblob + "\n" + m.group(2),
        html, count=1, flags=re.S,
    )
    if new == html and '"threats"' not in html:
        print("WARNING: preview-data block not found in scenarios.html", file=sys.stderr)
    else:
        page.write_text(new)
        print(f"preview-data injected: {len(plains)} sections, {len(threats)} threats")

    # the glossary lives twice — README.md (the linkable canon) and the essay's
    # Appendix — so the two term sets must not drift
    gloss = re.findall(r'id="(w-[a-z0-9-]+)"', (ROOT / "README.md").read_text())
    essay = re.findall(r'id="(w-[a-z0-9-]+)"', (ROOT / "index.html").read_text())
    if set(gloss) != set(essay) or len(gloss) != len(set(gloss)):
        print(f"FAIL glossary parity: README {sorted(set(gloss) ^ set(essay))} out of step with index.html", file=sys.stderr)
        return 1
    print(f"glossary parity: {len(gloss)} terms, README.md == index.html appendix")

    # KERNEL.md's §-links carry the essay's Plainly lines as hover titles —
    # same anti-drift discipline as the glossary
    total = 0
    for name in ("KERNEL.md", "proto/README.md", "docs/functional-model.md", "docs/uk-trajectory.md", "docs/eu-trajectory.md", "docs/cn-trajectory.md", "docs/de-trajectory.md", "docs/us-trajectory.md"):
        doc = (ROOT / name).read_text()
        klinks = re.findall(r'\[§[\d.]+\]\([^)"]*#(s[0-9-]+) "([^"]*)"\)', doc)
        bad = sorted({sid for sid, title in klinks if plains.get(sid) != title})
        if not klinks or bad:
            print(f"FAIL {name} §-link previews out of step with the essay's Plainly lines: {bad or 'no links found'}", file=sys.stderr)
            return 1
        total += len(klinks)
    print(f"section previews: {total} §-links across the markdown docs match the essay's Plainly lines")

    # Part-links inside docs/ preview the model's own Plainly summaries
    model = (ROOT / "docs" / "functional-model.md").read_text()
    mparts = {}
    for m in re.finditer(r"^## (\d+) ·.*?<summary><b>Plainly</b> <i>(.*?)</i></summary>", model, re.M | re.S):
        mparts[m.group(1)] = m.group(2).strip()
    pl = 0
    for name in ("docs/functional-model.md", "docs/uk-trajectory.md"):
        doc = (ROOT / name).read_text()
        links = re.findall(r'\[Part (\d+)\]\([^)"]* "([^"]*)"\)', doc)
        bad = sorted({n for n, title in links if mparts.get(n) != title})
        if bad:
            print(f"FAIL {name} Part-link previews out of step with the model's Plainly lines: {bad}", file=sys.stderr)
            return 1
        pl += len(links)
    print(f"part previews: {pl} Part-links match the model's own Plainly lines")

    # the verifier footer's cross-document previews mirror each document's own opener
    ver = (ROOT / "verifier.html").read_text()
    def norm(s):
        return " ".join(re.sub(r"<[^>]+>", "", s).split())
    sources = {
        "https://github.com/GlassOnTin/civic-kernel": norm(re.search(r"\*\*(Rules for running a vote.*?)\*\*", (ROOT / "README.md").read_text(), re.S).group(1)),
        "index.html": norm(re.search(r'<p class="standfirst">(.*?)</p>', essay_html, re.S).group(1)),
        "scenarios.html": norm(re.search(r'<p class="lede">(.*?)</p>', (ROOT / "scenarios.html").read_text(), re.S).group(1)),
        "proto/README.md": norm(re.search(r"# proto/[^\n]*\n\n([^.]*\.)", (ROOT / "proto" / "README.md").read_text()).group(1)),
        "cast.html": norm(re.search(r'<p class="sub">([^.]*\.)', (ROOT / "cast.html").read_text(), re.S).group(1)),
    }
    xbad = []
    xrefs = re.findall(r'<a class="xref" href="([^"]+)" data-tip="([^"]*)"', ver)
    for href, tip in xrefs:
        if sources.get(href) != tip:
            xbad.append(href)
    if len(xrefs) != 5 or xbad:
        print(f"FAIL verifier footer previews out of step with their source documents: {xbad or 'expected 5 xrefs, found ' + str(len(xrefs))}", file=sys.stderr)
        return 1
    print("verifier previews: 5 cross-document tips match their sources' own openers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
