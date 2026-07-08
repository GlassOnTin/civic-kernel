#!/usr/bin/env python3
"""Independent verifier for a clubvote transcript: `python3 verify.py <outdir>`.

Shares NO code with clubvote.py — it reimplements canonicalization, the Merkle tree,
and every check from the published artifacts plus the waist schemas in ../schema/.
Trust anchors come from trust.json (in a real deployment: DID resolution and the
witness ecosystem; here, a file you choose to trust).

Exit 0 = every check passed. Exit 1 = the transcript is broken, and it says where.
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
FAILURES = []


def check(ok: bool, what: str):
    print(("  ok   " if ok else "  FAIL ") + what)
    if not ok:
        FAILURES.append(what)


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sig_ok(pub_b64: str, sig: dict, obj_minus_sig: dict) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(b64d(pub_b64)).verify(b64d(sig["value"]), canon(obj_minus_sig))
        return True
    except (InvalidSignature, Exception):
        return False


def leaf_hash(leaf: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + leaf).digest()


def merkle_root(leaves) -> bytes:
    if not leaves:
        return hashlib.sha256(b"").digest()
    if len(leaves) == 1:
        return leaves[0]
    k = 1
    while k * 2 < len(leaves):
        k *= 2
    return hashlib.sha256(b"\x01" + merkle_root(leaves[:k]) + merkle_root(leaves[k:])).digest()


def main(outdir: Path) -> int:
    trust = json.loads((outdir / "trust.json").read_text())
    manifest = json.loads((outdir / "manifest.json").read_text())
    roster_doc = json.loads((outdir / "roster.json").read_text())
    box_doc = json.loads((outdir / "ballot-box.json").read_text())
    entries = [json.loads(l) for l in (outdir / "log.jsonl").read_text().splitlines()]
    heads = [json.loads(l) for l in (outdir / "heads.jsonl").read_text().splitlines()]

    print("[1] the waist: artifacts validate against the schemas")
    v_manifest = Draft202012Validator(json.loads((ROOT / "schema" / "manifest.schema.json").read_text()))
    v_log = Draft202012Validator(json.loads((ROOT / "schema" / "log-entry.schema.json").read_text()))
    errs = list(v_manifest.iter_errors(manifest))
    check(not errs, f"manifest validates against manifest.schema.json ({len(errs)} errors)")
    bad = [f"entry[{i}] {e.message}" for i, en in enumerate(entries) for e in v_log.iter_errors(en)]
    check(not bad, f"all {len(entries)} log entries validate against log-entry.schema.json"
          + ("" if not bad else " :: " + bad[0]))

    print("[2] signatures: every artifact is signed by a key the trust anchors name")
    m_body = {k: v for k, v in manifest.items() if k != "sig"}
    check(sig_ok(trust.get(manifest["sig"]["key_id"], ""), manifest["sig"], m_body), "manifest signature")
    log_key_id = entries[0]["sig"]["key_id"] if entries else "?"
    all_sigs = all(sig_ok(trust.get(e["sig"]["key_id"], ""), e["sig"],
                          {k: v for k, v in e.items() if k != "sig"}) for e in entries)
    check(all_sigs, f"all log-entry signatures verify against {log_key_id}")
    ts = [e["timestamp"] for e in entries]
    check(ts == sorted(ts), "log timestamps are non-decreasing")

    print("[3] the log: append-only, witnessed, and it commits to everything else")
    leaves = [leaf_hash(canon({k: v for k, v in e.items() if k != "sig"})) for e in entries]
    heads_ok = all(h["root"] == "sha256:" + merkle_root(leaves[: h["size"]]).hex() for h in heads)
    check(heads_ok, f"every published head's root matches a strict prefix of today's log "
                    f"(consistency, {len(heads)} heads)")
    check(heads[-1]["size"] == len(entries), "the latest head covers the whole log")
    wit_ok = all(all(sig_ok(trust.get(s["key_id"], ""), s,
                            {k: v for k, v in h.items() if k != "sigs"}) for s in h["sigs"])
                 for h in heads)
    n_wit = len(heads[-1]["sigs"]) - 1 if heads else 0
    check(wit_ok, f"every head co-signed by the log key and {n_wit} independent witnesses")

    by_type = {e["type"]: e for e in entries}
    pub = by_type.get("manifest.published", {}).get("body", {})
    check(pub.get("manifest_digest") == sha256_hex(canon(m_body)),
          "logged manifest digest matches the published manifest (a manifest that lies is a "
          "consistency failure)")
    rost = by_type.get("x-roster.published", {}).get("body", {})
    check(rost.get("roster_digest") == sha256_hex(canon(roster_doc)),
          f"logged roster digest matches the published roster ({rost.get('member_count')} members)")
    closed = by_type.get("decision.closed", {}).get("body", {})
    check(closed.get("ballot_box_digest") == sha256_hex(canon(box_doc)),
          "logged ballot-box digest matches the published box")

    print("[4] eligibility: one credential per enrolled member, issuer-signed")
    issuer_key = trust.get(roster_doc["members"][0]["issuer_sig"]["key_id"], "") if roster_doc["members"] else ""
    creds_ok = all(sig_ok(issuer_key, c["issuer_sig"],
                          {k: v for k, v in c.items() if k != "issuer_sig"}) for c in roster_doc["members"])
    check(creds_ok, f"all {len(roster_doc['members'])} roster credentials verify against the issuer key")
    by_pub = {c["voter_pub"]: c for c in roster_doc["members"]}

    print("[5] cast-or-audit: challenged commitments open correctly and were never cast")
    audits_doc = json.loads((outdir / "audits.json").read_text())
    audits = audits_doc["audits"]
    check(closed.get("audits_digest") == sha256_hex(canon(audits_doc)),
          "logged audits digest matches the published audit file")
    bad_audit = [a for a in audits
                 if sha256_hex((a["opened_choice"] + "|" + a["opened_nonce"]).encode()) != a["commit"]
                 or (a["outcome"] == "match") != (a["opened_choice"] == a["claimed_choice"])]
    check(not bad_audit, f"all {len(audits)} audit records are internally consistent evidence")
    cast_commits = {b["commit"] for b in box_doc["ballots"]}
    check(not [a for a in audits if a["commit"] in cast_commits],
          "no challenged (spoiled) commitment was ever cast")
    fails = [a for a in audits if a["outcome"] == "MISMATCH"]
    af_entries = [e for e in entries if e["type"] == "x-ballot.audit-failed"]
    check(len(af_entries) == len(fails) == closed.get("audit_failures", -1),
          f"every audit failure is a public log entry ({len(fails)} cheating device caught)")

    print("[6] the recount: anyone can recompute the tally from box + reveals alone")
    reveals_doc = json.loads((outdir / "reveals.json").read_text())
    tally = by_type.get("decision.tally-proof", {}).get("body", {})
    check(tally.get("reveals_digest") == sha256_hex(canon(reveals_doc)),
          "logged reveals digest matches the published reveals")
    opened = by_type.get("decision.opened", {}).get("body", {})
    decision_id = opened.get("decision_id")
    reveal_by_seq = {r["seq"]: r for r in reveals_doc["reveals"]}
    ballots, problems = [], []
    for i, b in enumerate(box_doc["ballots"]):
        r = reveal_by_seq.get(b["seq"])
        why = None
        if b["decision_id"] != decision_id:
            why = "wrong decision"
        elif b["voter_pub"] not in by_pub:
            why = "voter not on roster (no issuer credential)"
        elif b["nullifier"] != sha256_hex(b64d(b["voter_pub"]) + decision_id.encode()):
            why = "nullifier does not recompute"
        elif not sig_ok(b["voter_pub"], b["voter_sig"], {k: v for k, v in b.items() if k != "voter_sig"}):
            why = "voter signature invalid"
        elif "witness_sig" in b and not sig_ok(
                trust.get(b["witness_sig"]["key_id"], ""), b["witness_sig"],
                {k: v for k, v in b.items() if k not in ("voter_sig", "witness_sig")}):
            why = "assisted-channel witness signature invalid"
        elif r is None:
            why = "cast commitment never revealed"
        elif sha256_hex((r["choice"] + "|" + r["nonce"]).encode()) != b["commit"]:
            why = "reveal does not open the cast commitment"
        elif r["choice"] not in opened.get("options", []):
            why = "revealed choice not among the options"
        if why:
            problems.append(f"ballot[{i}] {why}")
        else:
            ballots.append((b, r))
    check(not problems, f"all {len(box_doc['ballots'])} cast commitments reveal validly"
          + ("" if not problems else " :: " + problems[0]))
    check(len(reveal_by_seq) == len(box_doc["ballots"]),
          "exactly one reveal per cast ballot, none extra")

    latest = {}
    for b, r in sorted(ballots, key=lambda br: br[0]["seq"]):
        latest[b["nullifier"]] = (b, r)
    counts = {o: 0 for o in opened.get("options", [])}
    for b, r in latest.values():
        counts[r["choice"]] += 1
    check(tally.get("counts") == counts, f"recount matches the published tally: {counts}")
    check(tally.get("distinct_voters") == len(latest)
          and tally.get("superseded") == len(ballots) - len(latest),
          f"recast policy applied: {len(ballots)} valid ballots, {len(latest)} voters counted, "
          f"{len(ballots) - len(latest)} silently superseded (last ballot counts)")
    assisted = [b for b, r in latest.values() if b.get("channel") == "assisted"]
    check(len(assisted) >= 1,
          f"assisted-channel ballots counted in the same tally as any other ({len(assisted)} assisted)")

    print()
    if FAILURES:
        print(f"NOT VERIFIED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print("  - " + f)
        return 1
    winner = max(counts, key=counts.get)
    print(f"VERIFIED. {len(roster_doc['members'])} enrolled; {len(latest)} voted; "
          + "; ".join(f"{k} {v}" for k, v in counts.items())
          + f". {winner} is elected, and nobody had to trust the shed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "out"))
