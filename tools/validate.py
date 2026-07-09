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

    # the glossary lives twice — README.md (the linkable canon) and the essay's
    # Appendix — so the two term sets must not drift
    gloss = re.findall(r'id="(w-[a-z0-9-]+)"', (ROOT / "README.md").read_text())
    essay = re.findall(r'id="(w-[a-z0-9-]+)"', (ROOT / "index.html").read_text())
    if set(gloss) != set(essay) or len(gloss) != len(set(gloss)):
        print(f"FAIL glossary parity: README {sorted(set(gloss) ^ set(essay))} out of step with index.html", file=sys.stderr)
        return 1
    print(f"glossary parity: {len(gloss)} terms, README.md == index.html appendix")
    return 0


if __name__ == "__main__":
    sys.exit(main())
