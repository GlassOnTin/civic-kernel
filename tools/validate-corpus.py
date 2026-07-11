#!/usr/bin/env python3
"""Validate the comparative law corpus and inject it into the browsable site.

Requires: pip install jsonschema

  - corpus/*/divisions/*.json  each validate as a log-entry (schema/log-entry.schema.json)
  - corpus/*/rights-map.json   each: invariant ids are exactly 1..30 (the UDHR spine, the same
                               integer space a manifest's rights_guard.invariants draws from),
                               and every status is one of backed | structural | none.

The 30-invariant spine is the fixed comparison axis: swap the backing (HRA, Grundgesetz, …) and
each legal system becomes one column, so different systems are captured under one schema and made
comparable. On success the corpus-data block in scenarios.html is rebuilt. Exit 0 = all pass.
"""
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
LOG = Draft202012Validator(json.loads((ROOT / "schema" / "log-entry.schema.json").read_text()))
STATUSES = {"backed", "structural", "none"}
ENTRENCHMENTS = {"none", "statute", "doctrine", "constitutional-text", "treaty", "eternity-clause"}
TIMINGS = {"pre-enactment", "pre-enforcement", "post-enforcement"}


def main() -> int:
    errs = 0

    divisions = sorted((ROOT / "corpus").glob("*/divisions/*.json"))
    for f in divisions:
        e = json.loads(f.read_text())
        problems = [f"{x.message} at {'/'.join(map(str, x.path))}" for x in LOG.iter_errors(e)]
        if problems:
            errs += 1
            print(f"FAIL division {f.parent.parent.name}/{f.name}", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
        else:
            print(f"ok   division {f.parent.parent.name}/{f.name}  ({e['body'].get('title', '?')})")

    jurisdictions = []
    for f in sorted((ROOT / "corpus").glob("*/rights-map.json")):
        rmap = json.loads(f.read_text())
        code = rmap.get("meta", {}).get("code", f.parent.name)
        ids = [r["invariant"] for r in rmap["invariants"]]
        bad = [r["invariant"] for r in rmap["invariants"] if r.get("status") not in STATUSES]
        scope = rmap["meta"].get("scope")
        if ids != list(range(1, 31)):
            errs += 1
            print(f"FAIL rights-map {code}: invariant ids must be 1..30 exactly, got {ids}", file=sys.stderr)
        elif bad:
            errs += 1
            print(f"FAIL rights-map {code}: invalid status on invariants {bad}", file=sys.stderr)
        elif scope not in ("unconditional", "conditional"):
            errs += 1
            print(f"FAIL rights-map {code}: meta.scope must be 'unconditional' or 'conditional', got {scope!r}", file=sys.stderr)
        elif rmap["meta"].get("remedy") != "none" and (
            rmap["meta"].get("entrenchment") not in ENTRENCHMENTS or rmap["meta"].get("timing") not in TIMINGS
        ):
            errs += 1
            print(f"FAIL rights-map {code}: where a remedy exists, meta.entrenchment must be one of {sorted(ENTRENCHMENTS)} and meta.timing one of {sorted(TIMINGS)}", file=sys.stderr)
        elif rmap["meta"].get("remedy") == "none" and ("entrenchment" in rmap["meta"] or "timing" in rmap["meta"]):
            errs += 1
            print(f"FAIL rights-map {code}: entrenchment/timing are vacuous where remedy is 'none' — omit the value fields (the _note fields may explain the absence)", file=sys.stderr)
        elif rmap["meta"].get("verdict") not in ("holds", "strains", "breaks") or len(rmap["meta"].get("verdict_plain", "")) < 40 or len(rmap["meta"].get("protection", "")) < 3:
            errs += 1
            print(f"FAIL rights-map {code}: meta.verdict must be holds/strains/breaks with verdict_plain (40+ chars) and protection", file=sys.stderr)
        elif (ROOT / "scenarios" / f"majority-vs-minority-{code}.json").exists() and (
            rmap["meta"]["verdict"],
            rmap["meta"]["protection"],
            rmap["meta"].get("protection_plain"),
            rmap["meta"].get("entrenchment"),
            rmap["meta"].get("timing"),
        ) != (lambda s: (
            s["verdict"],
            s["protection"],
            s["protection_plain"],
            s["manifest"]["rights_guard"].get("entrenchment"),
            s["manifest"]["rights_guard"].get("timing"),
        ))(json.loads((ROOT / "scenarios" / f"majority-vs-minority-{code}.json").read_text())):
            errs += 1
            print(f"FAIL rights-map {code}: meta.verdict/protection/entrenchment/timing contradict the measured scenario majority-vs-minority-{code}.json", file=sys.stderr)
        else:
            cov = rmap["meta"]["coverage"]
            axes = f"remedy '{rmap['meta']['remedy']}' · scope '{scope}' · entrenchment '{rmap['meta'].get('entrenchment', '—')}' · timing '{rmap['meta'].get('timing', '—')}'"
            print(f"ok   rights-map {code}  backed {cov['backed']} · structural {cov['structural']} · none {cov['none']} · {axes}")
            jurisdictions.append(rmap)

    if errs:
        print(f"\n{errs} corpus artifact(s) failed", file=sys.stderr)
        return 1

    page = ROOT / "scenarios.html"
    if page.exists():
        blob = json.dumps(
            {"jurisdictions": jurisdictions, "divisions": [json.loads(f.read_text()) for f in divisions]},
            ensure_ascii=False, indent=1,
        ).replace("</", "<\\/")
        html = page.read_text()
        new = re.sub(
            r'(<script id="corpus-data" type="application/json">).*?(</script>)',
            lambda m: m.group(1) + "\n" + blob + "\n" + m.group(2),
            html, count=1, flags=re.S,
        )
        if new != html:
            page.write_text(new)
            print("injected corpus-data into scenarios.html")
        elif '"jurisdictions"' not in html:
            print("WARNING: corpus-data block not found in scenarios.html", file=sys.stderr)

    print(f"\n{len(jurisdictions)} jurisdiction(s) + {len(divisions)} division(s) valid against the waist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
