#!/usr/bin/env python3
"""Independent verifier for a clubvote transcript: `python3 verify.py <outdir>`.

Shares NO code with clubvote.py — it reimplements canonicalization, the Merkle tree,
the group arithmetic, all three zero-knowledge proof verifications, and every check from
the published artifacts plus the waist schemas in ../schema/. Trust anchors come from
trust.json (in a real deployment: DID resolution and the witness ecosystem; here, a file
you choose to trust) — including which external parties must hold a receipt for the
closing log head, the one defence against a history that was quietly shortened rather
than forged. The ballot group is pinned BY NAME to this verifier's own
constants — a transcript that could supply its own group could supply a smooth one.

The ballots are anonymous, and this verifier never learns who cast one. It checks that
each carries a linkable ring signature over the published roster — proof that SOME
plot-holder cast it, bound to a per-decision linking tag that is the only thing
distinguishing one voter from another.

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

# The verifier's own copy of RFC 3526 group 14 — parameters come from the verifier,
# never from the transcript under audit.
KNOWN_GROUPS = {"rfc3526-modp-2048": int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74"
    "020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F1437"
    "4FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF05"
    "98DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB"
    "9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718"
    "3995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF", 16)}


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


def hx(n: int) -> str:
    return format(n, "x")


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
    # The trust anchors: keys the verifier already trusts, and which of those parties it
    # requires as independent witnesses. Nothing inside the transcript can lower this bar.
    anchors = json.loads((outdir / "trust.json").read_text())
    trust, required_witnesses = anchors["keys"], anchors["witnesses"]
    manifest = json.loads((outdir / "manifest.json").read_text())
    roster_doc = json.loads((outdir / "roster.json").read_text())
    box_doc = json.loads((outdir / "ballot-box.json").read_text())
    trustees_doc = json.loads((outdir / "trustees.json").read_text())
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
    # A head is only as good as WHO co-signed it. Checking that the signatures PRESENT
    # verify is not enough: an insider who rewrites an entry can regenerate every head,
    # re-sign each with the log key they hold, and simply drop the witnesses they cannot
    # forge — the heads then pass consistency and signature checks alike. Nor can the
    # standard be the manifest's own witness list: the manifest is signed by the log key,
    # so the same insider can lower their own bar to zero. The standard is therefore the
    # verifier's trust anchors, which name the witnesses independently (in reality: DID
    # resolution and the witness ecosystem). An unwitnessed log cannot defeat a records
    # rewrite, so verify.py declines to certify one.
    # Every witness the trust anchors REQUIRE (a bar the transcript cannot lower) and every
    # witness the manifest DECLARES (it may not advertise a guard it does not have) must
    # co-sign every head. Dropping a co-signature and inflating the declared set both fail.
    declared = manifest.get("transparency_log", {}).get("witnesses", [])
    expected = set(required_witnesses) | set(declared)

    def head_ok(h) -> bool:
        body = {k: v for k, v in h.items() if k != "sigs"}
        covered = set()
        for s in h["sigs"]:
            if not sig_ok(trust.get(s["key_id"], ""), s, body):
                return False  # a signature that is present but does not verify
            covered.update(w for w in expected
                           if s["key_id"] == w or s["key_id"].startswith(w + "#"))
        return expected <= covered

    missing = [h["size"] for h in heads if not head_ok(h)]
    check(bool(required_witnesses) and not missing,
          f"every head co-signed by the log key and all {len(expected)} required/declared witnesses"
          + ("" if required_witnesses else " :: the trust anchors name no witness, and an "
             "unwitnessed log cannot defeat a records rewrite")
          + ("" if not missing else f" :: head(s) at size {missing} lack a valid co-signature from "
             f"every witness — the log key alone re-signed this history"))

    check(set(required_witnesses) <= set(declared),
          "the manifest declares every witness the trust anchors require (the manifest is signed "
          "by the log key, so it cannot be its own standard: a manifest that quietly drops a "
          "witness is a lying manifest)")

    by_type = {e["type"]: e for e in entries}
    pub = by_type.get("manifest.published", {}).get("body", {})
    check(pub.get("manifest_digest") == sha256_hex(canon(m_body)),
          "logged manifest digest matches the published manifest (a manifest that lies is a "
          "consistency failure)")
    rost = by_type.get("x-roster.published", {}).get("body", {})
    check(rost.get("roster_digest") == sha256_hex(canon(roster_doc)),
          f"logged roster digest matches the published roster ({rost.get('member_count')} members)")
    trst = by_type.get("x-trustees.published", {}).get("body", {})
    check(trst.get("trustees_digest") == sha256_hex(canon(trustees_doc)),
          "logged trustee-setup digest matches the published setup")
    closed = by_type.get("decision.closed", {}).get("body", {})
    check(closed.get("ballot_box_digest") == sha256_hex(canon(box_doc)),
          "logged ballot-box digest matches the published box")

    print("[4] eligibility: the ring — one issuer-signed nym key per enrolled member")
    issuer_key = trust.get(roster_doc["members"][0]["issuer_sig"]["key_id"], "") if roster_doc["members"] else ""
    creds_ok = all(sig_ok(issuer_key, c["issuer_sig"],
                          {k: v for k, v in c.items() if k != "issuer_sig"}) for c in roster_doc["members"])
    check(creds_ok, f"all {len(roster_doc['members'])} roster credentials verify against the issuer key")

    # --- the ballot group, pinned by name; the trustee setup, derived not asserted
    opened = by_type.get("decision.opened", {}).get("body", {})
    decision_id = opened.get("decision_id")
    options = opened.get("options", [])
    check(trustees_doc.get("group") in KNOWN_GROUPS,
          f"ballot group '{trustees_doc.get('group')}' is one this verifier pins "
          "(parameters are the verifier's own, never the transcript's)")
    if trustees_doc.get("group") not in KNOWN_GROUPS:
        return finish(None, roster_doc, None)
    p = KNOWN_GROUPS[trustees_doc["group"]]
    q, g = (p - 1) // 2, 2
    # DKG: every trustee published their own Feldman commitment vector; the joint
    # commitments are their product, the election key is the joint constant term, and
    # every trustee key h_i derives from them — nothing about the key is ever asserted,
    # and no single party's contribution determines it.
    A = [1, 1]
    for tr in trustees_doc["trustees"]:
        A[0] = A[0] * int(tr["commitments"][0], 16) % p
        A[1] = A[1] * int(tr["commitments"][1], 16) % p
    h = A[0]

    def in_group(x: int) -> bool:
        return 0 < x < p and pow(x, q, p) == 1

    def fs_challenge(stmt: dict) -> int:
        return int.from_bytes(hashlib.sha256(canon(stmt)).digest()) % q

    def cds_ok(ct: dict, prf: dict) -> bool:
        # disjunctive Chaum-Pedersen (CDS): ct encrypts g^0 or g^1 under h
        c1, c2 = int(ct["c1"], 16), int(ct["c2"], 16)
        stmt = {"t": "cds01", "ctx": decision_id, "h": format(h, "x"),
                "c1": ct["c1"], "c2": ct["c2"],
                "a0": prf["a0"], "b0": prf["b0"], "a1": prf["a1"], "b1": prf["b1"]}
        cc = [int(prf["c0"], 16), int(prf["c1"], 16)]
        zz = [int(prf["z0"], 16), int(prf["z1"], 16)]
        if (cc[0] + cc[1]) % q != fs_challenge(stmt):
            return False
        for i in (0, 1):
            a_i, b_i = int(prf[f"a{i}"], 16), int(prf[f"b{i}"], 16)
            if pow(g, zz[i], p) != a_i * pow(c1, cc[i], p) % p:
                return False
            u = c2 * pow(pow(g, i, p), -1, p) % p  # c2 / g^i
            if pow(h, zz[i], p) != b_i * pow(u, cc[i], p) % p:
                return False
        return True

    # --- the anonymity set. The ring is the roster's keys, in the roster's order; the
    # context generator is derived from the decision id, so a voter's tag in this decision
    # says nothing about their tag in the next one. Neither is ever taken on the
    # transcript's word: both are recomputed here from artifacts already digest-committed.
    ring = [int(c["voter_pub"], 16) for c in roster_doc["members"]]
    ring_digest = sha256_hex(canon([c["voter_pub"] for c in roster_doc["members"]]))

    def context_gen(ctx: str) -> int:
        for i in range(64):
            c = int.from_bytes(hashlib.sha256(f"civic-kernel/ctx|{ctx}|{i}".encode()).digest()) % p
            if c > 1 and pow(c, 2, p) != 1:
                return pow(c, 2, p)
        raise ValueError("no context generator")

    def ring_challenge(msg: str, tag: int, z1: int, z2: int) -> int:
        return int.from_bytes(hashlib.sha256(canon(
            {"t": "lsag", "ring": ring_digest, "ctx": decision_id, "msg": msg,
             "tag": hx(tag), "z1": hx(z1), "z2": hx(z2)})).digest())

    hl = context_gen(decision_id)

    def lsag_ok(b: dict) -> bool:
        """The ring closes only if some ring key signed THIS ballot with THIS tag. Which
        key, the signature does not say — and there is no other way to ask."""
        sig = b.get("ring_sig") or {}
        s = [int(v, 16) for v in sig.get("s", [])]
        if len(s) != len(ring):
            return False
        tag, c0 = int(b["nullifier"], 16), int(sig.get("c0", "0"), 16)
        msg, c = sha256_hex(canon({k: v for k, v in b.items() if k != "ring_sig"})), c0
        for i, y in enumerate(ring):
            z1 = pow(g, s[i], p) * pow(y, c, p) % p
            z2 = pow(hl, s[i], p) * pow(tag, c, p) % p
            c = ring_challenge(msg, tag, z1, z2)
        return c == c0

    print("[5] cast-or-audit: challenged ciphertexts open correctly and were never cast")
    audits_doc = json.loads((outdir / "audits.json").read_text())
    audits = audits_doc["audits"]
    check(closed.get("audits_digest") == sha256_hex(canon(audits_doc)),
          "logged audits digest matches the published audit file")

    def reencrypts(a) -> bool:
        m = 1 if a["opened_choice"] == options[0] else 0
        r = int(a["opened_r"], 16)
        return (int(a["ciphertext"]["c1"], 16) == pow(g, r, p)
                and int(a["ciphertext"]["c2"], 16) == pow(g, m, p) * pow(h, r, p) % p)

    bad_audit = [a for a in audits
                 if not reencrypts(a)
                 or (a["outcome"] == "match") != (a["opened_choice"] == a["claimed_choice"])]
    check(not bad_audit, f"all {len(audits)} audit records re-encrypt to their opened choice "
                         "(internally consistent evidence)")
    cast_cts = {(b["ciphertext"]["c1"], b["ciphertext"]["c2"]) for b in box_doc["ballots"]}
    check(not [a for a in audits if (a["ciphertext"]["c1"], a["ciphertext"]["c2"]) in cast_cts],
          "no challenged (spoiled) ciphertext was ever cast")
    fails = [a for a in audits if a["outcome"] == "MISMATCH"]
    af_entries = [e for e in entries if e["type"] == "x-ballot.audit-failed"]
    check(len(af_entries) == len(fails) == closed.get("audit_failures", -1),
          f"every audit failure is a public log entry ({len(fails)} cheating device caught)")

    # Stage gate. Sections [1]–[5] are cheap; verifying a ballot is O(roster), and there
    # are as many ballots as voters. If the log, its witnesses, or the digests committing
    # to the box and the roster have already failed, the ballots would be checked against
    # artifacts this transcript has not earned the right to assert — so decline here rather
    # than spend the ring on a box the log does not vouch for. Same verdict, sooner.
    if FAILURES:
        print("[6-7] not checked: the artifacts that commit to the ballots did not verify (above)")
        return finish(None, roster_doc, None)

    print("[6] the box: anonymous ballots, each proving roster membership, in-group and 0-or-1")
    check(all(in_group(y) for y in ring),
          f"all {len(ring)} roster keys are prime-order subgroup elements (input hygiene on the "
          "ring: no tamper reaches it, because a rewritten roster fails its logged digest first)")
    ballots, problems = [], []
    for i, b in enumerate(box_doc["ballots"]):
        tag = int(b["nullifier"], 16)
        why = None
        if b["decision_id"] != decision_id:
            why = "wrong decision"
        elif not (in_group(tag) and tag != 1):
            # -T verifies as readily as T for a signer willing to grind, and links to
            # nothing. Without this line, one secret yields two voters.
            why = "nullifier is not in the prime-order subgroup (a negated linking tag votes twice)"
        elif not (in_group(int(b["ciphertext"]["c1"], 16)) and in_group(int(b["ciphertext"]["c2"], 16))):
            why = "ciphertext component not in the prime-order subgroup"
        elif not lsag_ok(b):
            why = "ring signature does not verify (no roster member signed this ballot with this nullifier)"
        elif not cds_ok(b["ciphertext"], b["proof"]):
            why = "ballot validity proof does not verify (not a 0-or-1 encryption)"
        if why:
            problems.append(f"ballot[{i}] {why}")
        else:
            ballots.append(b)
    check(not problems, f"all {len(box_doc['ballots'])} cast ballots are well-formed anonymous votes "
          "(subgroup membership, ring-membership proof, 0-or-1 validity proof)"
          + ("" if not problems else " :: " + problems[0]))

    # The tally is a function of the valid ballots. If the box did not verify there is
    # nothing sound to tally, and checking announced counts against a poisoned box would
    # only bury the real failure above under cascade noise.
    if FAILURES:
        print("[7] not checked: the ballots did not verify, so neither can their tally")
        return finish(None, roster_doc, None)

    print("[7] the tally: threshold-decrypted from the sum alone — no ballot is ever opened")
    tally = by_type.get("decision.tally-proof", {}).get("body", {})
    latest = {}
    for b in sorted(ballots, key=lambda b: b["seq"]):
        latest[b["nullifier"]] = b
    C1 = C2 = 1
    for b in latest.values():
        C1 = C1 * int(b["ciphertext"]["c1"], 16) % p
        C2 = C2 * int(b["ciphertext"]["c2"], 16) % p
    check(tally.get("sum_ciphertext") == {"c1": format(C1, "x"), "c2": format(C2, "x")},
          f"the logged sum ciphertext is the homomorphic product of the {len(latest)} counted ballots")

    # Each share carries a Chaum-Pedersen proof against a trustee key DERIVED from the
    # Feldman commitments (h_i = A0 * A1^i) — the setup cannot assert keys it cannot
    # prove, and the committee cannot manufacture a share for a secret it does not hold.
    shares = tally.get("trustee_shares", [])
    required = trustees_doc["threshold"]["required"]
    valid = []
    for s in shares:
        idx, d = s.get("index"), int(s.get("share", "0"), 16)
        if not (isinstance(idx, int) and 1 <= idx <= trustees_doc["threshold"]["of"]):
            continue
        if idx in [v[0] for v in valid] or not in_group(d):
            continue
        h_i = A[0] * pow(A[1], idx, p) % p
        prf = s.get("proof", {})
        stmt = {"t": "cp", "ctx": decision_id, "index": idx, "h_i": format(h_i, "x"),
                "c1": format(C1, "x"), "d": s["share"], "a": prf.get("a"), "b": prf.get("b")}
        c, z = fs_challenge(stmt), int(prf.get("z", "0"), 16)
        a_, b_ = int(prf.get("a", "0"), 16), int(prf.get("b", "0"), 16)
        if pow(g, z, p) == a_ * pow(h_i, c, p) % p and pow(C1, z, p) == b_ * pow(d, c, p) % p:
            valid.append((idx, d))
    check(len(valid) >= required,
          f"a {required}-of-{trustees_doc['threshold']['of']} trustee quorum proved the decryption "
          f"({len(valid)}/{required} required Chaum-Pedersen decryption proofs valid)")

    counts_dec, T = None, None
    if len(valid) >= required:
        D = 1
        for idx, d in valid:
            lam = 1
            for jdx, _ in valid:
                if jdx != idx:
                    lam = lam * jdx % q * pow(jdx - idx, -1, q) % q
            D = D * pow(d, lam, p) % p
        gT, acc = C2 * pow(D, -1, p) % p, 1
        for t_ in range(len(latest) + 1):
            if acc == gT:
                T = t_
                break
            acc = acc * g % p
        check(T is not None, "the combined decryption opens as a small exponent (the sum is well-formed)")
        if T is not None:
            counts_dec = {options[0]: T, options[1]: len(latest) - T}
    check(counts_dec is not None and tally.get("counts") == counts_dec,
          f"announced counts match the threshold decryption: {counts_dec}")
    check(tally.get("distinct_voters") == len(latest)
          and tally.get("superseded") == len(ballots) - len(latest),
          f"recast policy applied: {len(ballots)} valid ballots, {len(latest)} distinct linking tags "
          f"counted, {len(ballots) - len(latest)} silently superseded (last ballot counts)")

    # A transcript in which every proof verifies can still be a lie of omission: total
    # signature collusion cannot forge a ballot (everything above), but it can erase one
    # and re-sign the shortened history — every artifact then genuine, nothing inside the
    # transcript left to object. So the last check is against something outside it: the
    # closing head, republished beyond the collusion's reach, by parties the trust anchors
    # name (here a newspaper's pinned key stands in for its printed archive). The receipt
    # must cover THIS exact history, whole: a shortened, rewritten or extended log all
    # fail to match the head the world saw.
    if FAILURES:
        print("[8] not checked: the transcript did not verify, so no anchor can vouch for it")
        return finish(None, roster_doc, None)

    print("[8] the anchor: the world's copy of the closing head — history cannot quietly shorten")
    anchor_file = outdir / "anchor.json"
    receipts = json.loads(anchor_file.read_text()).get("receipts", []) if anchor_file.exists() else []
    required_anchors = anchors.get("anchors", [])

    def receipt_ok(r) -> bool:
        body = {k: v for k, v in r.items() if k != "sig"}
        return (sig_ok(trust.get(r.get("sig", {}).get("key_id", ""), ""), r.get("sig", {}), body)
                and body.get("log_id") == manifest.get("community", {}).get("id")
                and body.get("size") == len(entries)
                and body.get("root") == "sha256:" + merkle_root(leaves).hex())

    unanchored = [a for a in required_anchors if not any(
        (r.get("sig", {}).get("key_id", "") == a or r.get("sig", {}).get("key_id", "").startswith(a + "#"))
        and receipt_ok(r) for r in receipts)]
    check(bool(required_anchors) and not unanchored,
          f"the closing head is anchored outside the collusion set ({len(required_anchors)} required "
          "anchor(s) hold a valid receipt for this exact history)"
          + ("" if required_anchors else " :: the trust anchors name no external anchor, and an "
             "unanchored log cannot refute a quietly erased ballot")
          + ("" if not unanchored else f" :: no valid receipt from {unanchored} matches this log's "
             "closing head — the history under audit is not the history the world saw"))

    return finish(counts_dec, roster_doc, latest)


def finish(counts, roster_doc, latest) -> int:
    print()
    if FAILURES:
        print(f"NOT VERIFIED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print("  - " + f)
        return 1
    winner = max(counts, key=counts.get)
    print(f"VERIFIED. {len(roster_doc['members'])} enrolled; {len(latest)} voted; "
          + "; ".join(f"{k} {v}" for k, v in counts.items())
          + f". {winner} is elected. No ballot was ever opened, no voter was ever named, "
            "and nobody had to trust the shed.")
    return 0


if __name__ == "__main__":
    # A verifier is a trust boundary: it is handed bytes by whoever wants them believed.
    # Malformed input is a verdict, not a crash — "I could not check this" and "this checks
    # out" must never be told apart by reading a stack trace.
    try:
        sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "out"))
    except Exception as e:
        print(f"\nNOT VERIFIED — the transcript is malformed: {type(e).__name__}: {e}")
        sys.exit(1)
