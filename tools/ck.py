#!/usr/bin/env python3
"""Civic Kernel unified CLI inspector and verification tool.

Usage:
  python3 tools/ck.py verify [<transcript-dir>]
  python3 tools/ck.py check-persona <persona-or-circumstances.json>
  python3 tools/ck.py triage [--check|--write]
  python3 tools/ck.py status
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def cmd_verify(args):
    target = Path(args.transcript_dir).resolve() if args.transcript_dir else ROOT / "proto" / "out"
    if not target.exists():
        print(f"Error: transcript directory not found: {target}", file=sys.stderr)
        return 1
    sys.path.insert(0, str(ROOT / "proto"))
    import verify
    return verify.main(target)


def cmd_check_persona(args):
    pfile = Path(args.file).resolve()
    if not pfile.exists():
        print(f"Error: file not found: {pfile}", file=sys.stderr)
        return 1
    uk_dir = ROOT / "entitlements" / "uk"
    sys.path.insert(0, str(ROOT / "entitlements"))
    import judge
    
    spa = json.loads((uk_dir / "spa.json").read_text())
    ents = {}
    for p in sorted(uk_dir.glob("*.json")):
        doc = json.loads(p.read_text())
        if doc.get("v") == "civic-kernel/entitlement-rules/v0":
            ents[doc["id"]] = doc
            
    persona = json.loads(pfile.read_text())
    res = {eid: judge.evaluate(ent, spa, persona["answers"], persona["as_of"])
           for eid, ent in ents.items()}
    if args.json:
        print(json.dumps(res, indent=2))
        return 0
    failures = 0
    for eid, expect in persona.get("expect", {}).items():
        if eid not in res:
            print(f"  FAIL {persona.get('name', pfile.name)}: expects unknown entitlement {eid}")
            failures += 1
            continue
        got = res[eid]
        for key, want in expect.items():
            if got.get(key) != want:
                print(f"  FAIL {persona.get('name', pfile.name)} / {eid}: {key} = {got.get(key)!r}, expected {want!r}")
                failures += 1
    if failures:
        return 1
    summary = ", ".join(k + "=" + str(v.get("verdict")) for k, v in res.items())
    print(f"  ok   {persona.get('name', pfile.name)}: every expectation holds ({summary})")
    return 0


def cmd_triage(args):
    sys.path.insert(0, str(ROOT / "tools"))
    import triage
    sys.argv = ["triage.py"] + (["--check"] if args.check else []) + (["--write"] if args.write else [])
    return triage.main()


def cmd_status(args):
    scenarios = list((ROOT / "scenarios").glob("*.json"))
    scenarios = [s for s in scenarios if not s.name.endswith("scenario.schema.json")]
    entitlements = list((ROOT / "entitlements" / "uk").glob("*.json"))
    entitlements = [e for e in entitlements if not e.name.endswith("spa.json")]
    personas = list((ROOT / "entitlements" / "personas").glob("*.json"))
    
    print("Civic Kernel Repository Status:")
    print(f"  - Scenarios:    {len(scenarios)} stress-tests")
    print(f"  - Entitlements: {len(entitlements)} UK rulesets")
    print(f"  - Personas:     {len(personas)} test households")
    print(f"  - Waist:        2 schemas (log-entry, manifest)")
    return 0


def cmd_test(args):
    cmds = [
        ["python3", "tools/validate.py"],
        ["python3", "tools/validate-corpus.py"],
        ["python3", "tools/triage.py", "--check"],
        ["node", "tools/verify-parity.mjs"],
        ["node", "tools/cast-parity.mjs"],
        ["node", "tools/collect-parity.mjs"],
        ["node", "tools/witness-parity.mjs"],
        ["node", "tools/owed-parity.mjs"],
        ["node", "tools/agm-flow.mjs"],
        ["proto/test.sh"],
        ["proto/waist-boundary.sh"],
    ]
    for cmd in cmds:
        print(f"==> Running {' '.join(cmd)}...")
        res = subprocess.run(cmd, cwd=str(ROOT))
        if res.returncode != 0:
            print(f"FAIL: {' '.join(cmd)} exited with code {res.returncode}", file=sys.stderr)
            return res.returncode
    print("\nALL SUITES PASSED: Full parity, validation, and boundary verification successful.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Civic Kernel CLI Inspector")
    subparsers = parser.add_subparsers(dest="command")

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify a protocol election transcript")
    p_verify.add_argument("transcript_dir", nargs="?", default=str(ROOT / "proto" / "out"), help="Path to transcript directory")

    # check-persona
    p_persona = subparsers.add_parser("check-persona", help="Evaluate a persona or circumstances file against entitlement rules")
    p_persona.add_argument("file", help="Path to persona or circumstances JSON file")
    p_persona.add_argument("--json", action="store_true", help="Print output JSON trace")

    # triage
    p_triage = subparsers.add_parser("triage", help="Run triage pass over harms corpus")
    p_triage.add_argument("--check", action="store_true", help="Validate triage cases only")
    p_triage.add_argument("--write", action="store_true", help="Update docs/triage.md")

    # status
    subparsers.add_parser("status", help="Show corpus and test statistics")

    # test
    subparsers.add_parser("test", help="Run full test suite (validation, parity, and proto tests)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    if args.command == "verify":
        return cmd_verify(args)
    elif args.command == "check-persona":
        return cmd_check_persona(args)
    elif args.command == "triage":
        return cmd_triage(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "test":
        return cmd_test(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
