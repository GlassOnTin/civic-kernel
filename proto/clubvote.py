#!/usr/bin/env python3
"""The Heeley Bank club vote, end to end — the smallest real run of the four verbs.

Simulates every actor in one process (key custody is NOT the property under test;
verification-from-artifacts is) and emits a transcript any independent party can check
with verify.py, which shares no code with this file.

  python3 clubvote.py run [outdir]            deterministic full election -> artifacts
  python3 clubvote.py tamper <out> <dst> <mode>  copy transcript, corrupt it (mode: log|box|forge)

Deliberate v0 subtractions, declared in the emitted manifest rather than hidden:
ballots are pseudonymous but NOT encrypted (verifiable by recount, not receipt-free),
no cast-or-audit challenge, no unlinkability (the issuer can link nullifiers to the
roster), sybil resistance is the plot register. See README.md.
"""
import base64
import hashlib
import json
import shutil
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# ---------------------------------------------------------------- primitives

SEED = b"civic-kernel/proto/clubvote/v0"  # deterministic demo: zero privacy, by design


def canon(obj) -> bytes:
    # JCS (RFC 8785) approximation: exact for this artifact set (strings/ints/bools only)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def keypair(name: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(SEED + name.encode()).digest())


def pub_b64(priv: Ed25519PrivateKey) -> str:
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    return b64u(priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))


def sign_over(priv: Ed25519PrivateKey, key_id: str, obj_minus_sig: dict) -> dict:
    return {"key_id": key_id, "alg": "ed25519", "value": b64u(priv.sign(canon(obj_minus_sig)))}


# RFC 6962 Merkle tree
def leaf_hash(leaf: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + leaf).digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return hashlib.sha256(b"").digest()
    if len(leaves) == 1:
        return leaves[0]
    k = 1
    while k * 2 < len(leaves):
        k *= 2
    return hashlib.sha256(b"\x01" + merkle_root(leaves[:k]) + merkle_root(leaves[k:])).digest()


# ---------------------------------------------------------------- the cast

COMMUNITY = "did:web:heeley-bank-allotments.example"
DECISION = "2026-agm-treasurer"
QUESTION = "Who shall serve as treasurer of Heeley Bank Allotment Society for 2026-27?"
OPTIONS = ["Sandra Okafor", "Keith Bramall"]

ACTORS = {
    "log": (COMMUNITY + "#log-1", "society log key (held by the committee)"),
    "issuer": (COMMUNITY + "#roster-1", "roster issuer (plot register, simulated)"),
    "witness-fed": ("did:web:sheffield-allotment-federation.example#w1", "witness"),
    "witness-meers": ("did:web:meersbrook-allotments.example#w1", "witness"),
}

# 60 plots; named actors hold the story roles, the rest are ordinary members
MEMBERS = ["Sandra Okafor", "Keith Bramall", "Nalini Mistry", "Ernest Toft", "Derek Wainwright"] + [
    f"Plot-holder {i:02d}" for i in range(6, 61)
]


class Log:
    def __init__(self, log_priv, ts):
        self.entries, self.heads, self.log_priv, self.ts = [], [], log_priv, ts

    def append(self, type_, body, timestamp):
        entry = {"v": "civic-kernel/log-entry/v0", "type": type_, "community": COMMUNITY,
                 "timestamp": timestamp, "body": body}
        entry["sig"] = sign_over(self.log_priv, ACTORS["log"][0], entry)
        self.entries.append(entry)
        self._head(timestamp)
        return entry

    def _head(self, timestamp):
        leaves = [leaf_hash(canon({k: v for k, v in e.items() if k != "sig"})) for e in self.entries]
        head = {"log_id": COMMUNITY, "size": len(self.entries),
                "root": "sha256:" + merkle_root(leaves).hex(), "timestamp": timestamp}
        sigs = [sign_over(self.log_priv, ACTORS["log"][0], head)]
        for w in ("witness-fed", "witness-meers"):
            sigs.append(sign_over(keypair(w), ACTORS[w][0], head))
        self.heads.append({**head, "sigs": sigs})


def run(outdir: Path):
    out = outdir
    out.mkdir(parents=True, exist_ok=True)
    t = lambda day, hh, mm=0: f"2026-07-{day:02d}T{hh:02d}:{mm:02d}:00Z"

    # --- ceremony (prove, part 1): the issuer signs each member's voting key
    issuer = keypair("issuer")
    roster = []
    for name in MEMBERS:
        voter = keypair("member:" + name)
        vpub = pub_b64(voter)
        cred = {"member": name, "voter_pub": vpub}
        cred["issuer_sig"] = sign_over(issuer, ACTORS["issuer"][0], cred)
        roster.append(cred)
    roster_doc = {"community": COMMUNITY, "eligibility": "plot-register/2026: one vote per named plot-holder",
                  "members": roster}
    (out / "roster.json").write_text(json.dumps(roster_doc, indent=1) + "\n")
    roster_digest = sha256_hex(canon(roster_doc))

    # --- manifest: what this deployment ACTUALLY upholds (subtraction is legible)
    manifest = {
        "v": "civic-kernel/manifest/v0",
        "community": {"id": COMMUNITY, "name": "Heeley Bank Allotment Society, Sheffield (prototype run)",
                      "parent": "did:web:sheffield-allotment-federation.example"},
        "services": {"personhood": True, "decisions": True, "rights_guard": False, "transparency_log": True},
        "personhood": {"method": "platform-account", "issuer": "plot-register roster (simulated ceremony)",
                       "unlinkable": False, "sybil_resistance": "weak",
                       "eligibility_rules": "plot-register/2026 " + roster_digest},
        "decisions": {"verifiable": True, "receipt_free": False, "cast_or_audit": False,
                      "paper_channel": False, "coercion_resistance": "revote-silent"},
        "transparency_log": {"log_id": COMMUNITY,
                             "witnesses": ["did:web:sheffield-allotment-federation.example",
                                           "did:web:meersbrook-allotments.example"]},
        "decision_metadata": False,
    }
    manifest["sig"] = sign_over(keypair("log"), COMMUNITY + "#manifest-1", manifest)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    manifest_digest = sha256_hex(canon({k: v for k, v in manifest.items() if k != "sig"}))

    # --- the log opens
    log = Log(keypair("log"), t(1, 19))
    log.append("manifest.published", {
        "manifest_digest": manifest_digest,
        "note": "Prototype run. Declares: roster personhood (sybil-weak, linkable), plaintext "
                "pseudonymous ballots (verifiable by recount, NOT receipt-free, no cast-or-audit), "
                "silent re-vote, no rights guard, no paper channel."}, t(1, 19))
    log.append("x-roster.published", {"roster_digest": roster_digest, "member_count": len(MEMBERS)}, t(1, 19, 5))
    log.append("decision.opened", {
        "decision_id": DECISION, "question": QUESTION, "question_hash": sha256_hex(QUESTION.encode()),
        "options": OPTIONS, "eligibility_rules": "roster " + roster_digest,
        "recast_policy": "last-ballot-counts",
        "window": {"deliberation_ends": t(14, 18), "cast_ends": t(21, 18)}}, t(7, 18))

    # --- casting (prove part 2 + cast): nullifier = sha256(voter_pub || decision_id)
    box, seq = [], 0

    def cast(name, choice, channel="app", witness=None):
        nonlocal seq
        seq += 1
        voter = keypair("member:" + name)
        vpub = pub_b64(voter)
        cred = next(c for c in roster if c["voter_pub"] == vpub)
        ballot = {"decision_id": DECISION, "seq": seq,
                  "nullifier": sha256_hex(b64d(vpub) + DECISION.encode()),
                  "choice": choice, "voter_pub": vpub, "issuer_sig": cred["issuer_sig"], "channel": channel}
        if witness:
            ballot["witness_sig"] = sign_over(keypair("member:" + witness),
                                              "assisted-witness:" + witness, ballot)
        ballot["voter_sig"] = sign_over(voter, "voter:" + vpub, ballot)
        box.append(ballot)

    # ordinary members vote (deterministic split: 27 Sandra, 21 Keith, 7 abstain)
    for i, name in enumerate(MEMBERS[5:]):
        if i % 8 == 7:
            continue  # abstainers
        cast(name, OPTIONS[0] if i % 7 < 4 else OPTIONS[1])
    cast("Sandra Okafor", OPTIONS[0])
    cast("Keith Bramall", OPTIONS[1])
    cast("Derek Wainwright", OPTIONS[1])
    # Nalini votes, thinks about the water-rate surplus overnight, and silently re-votes:
    cast("Nalini Mistry", OPTIONS[1])
    cast("Nalini Mistry", OPTIONS[0])          # same nullifier, later seq -> supersedes
    # Ernest (no smartphone, trusts none of it) casts through the assisted channel,
    # two tellers at the table, Jordan's key witnessing the ballot:
    cast("Ernest Toft", OPTIONS[1], channel="assisted", witness="Plot-holder 12")
    # Derek tries to mint an extra voice for his unenrolled cousin: no roster credential
    try:
        cast("Cousin Ray", OPTIONS[1])
    except StopIteration:
        rejected = {"attempt": "cast by unenrolled key", "member": "Cousin Ray",
                    "result": "rejected: no roster credential"}

    box_doc = {"decision_id": DECISION, "ballots": box}
    (out / "ballot-box.json").write_text(json.dumps(box_doc, indent=1) + "\n")
    box_digest = sha256_hex(canon(box_doc))

    # --- close + tally (a recount anyone can redo; the 'proof' is recomputability)
    latest = {}
    for b in box:
        latest[b["nullifier"]] = b  # ascending seq: last write wins
    counts = {o: 0 for o in OPTIONS}
    for b in latest.values():
        counts[b["choice"]] += 1
    log.append("decision.closed", {
        "decision_id": DECISION, "ballot_box_digest": box_digest,
        "ballots_recorded": len(box), "rejected_at_cast": [rejected]}, t(21, 18))
    log.append("decision.tally-proof", {
        "decision_id": DECISION, "method": "public-recount/v0 (last ballot per nullifier counts)",
        "ballot_box_digest": box_digest, "counts": counts,
        "distinct_voters": len(latest), "superseded": len(box) - len(latest)}, t(21, 18, 30))

    (out / "log.jsonl").write_text("".join(json.dumps(e) + "\n" for e in log.entries))
    (out / "heads.jsonl").write_text("".join(json.dumps(h) + "\n" for h in log.heads))

    # --- trust anchors: what a verifier must already trust (in reality: DID resolution + witnesses)
    trust = {ACTORS[a][0]: pub_b64(keypair(a)) for a in ACTORS}
    trust[COMMUNITY + "#manifest-1"] = pub_b64(keypair("log"))
    trust["assisted-witness:Plot-holder 12"] = pub_b64(keypair("member:Plot-holder 12"))
    (out / "trust.json").write_text(json.dumps(trust, indent=1) + "\n")

    print(f"run complete -> {out}")
    print(f"  {len(MEMBERS)} enrolled, {len(box)} ballots ({len(latest)} counted, "
          f"{len(box) - len(latest)} superseded), 1 unenrolled cast rejected")
    print(f"  tally: " + ", ".join(f"{k} {v}" for k, v in counts.items()))


def tamper(src: Path, dst: Path, mode: str):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    if mode == "log":
        # An INSIDER rewrites history: the committee holds the log key, edits the recorded
        # question after the fact and re-signs it validly. Signatures pass; the witnessed
        # heads cannot be re-signed (the insider does not hold the witnesses' keys), so the
        # rewrite must fail against the co-signed roots — records-rewrite, the scenario.
        lines = (dst / "log.jsonl").read_text().splitlines()
        e = json.loads(lines[2])
        e["body"]["question"] = QUESTION.replace("treasurer", "treasurer-for-life")
        del e["sig"]
        e["sig"] = sign_over(keypair("log"), ACTORS["log"][0], e)
        lines[2] = json.dumps(e)
        (dst / "log.jsonl").write_text("\n".join(lines) + "\n")
    elif mode == "box":  # quietly flip one counted ballot's choice
        doc = json.loads((dst / "ballot-box.json").read_text())
        doc["ballots"][0]["choice"] = OPTIONS[1]
        (dst / "ballot-box.json").write_text(json.dumps(doc, indent=1) + "\n")
    elif mode == "forge":  # stuff the box with a ballot from a key the issuer never signed
        doc = json.loads((dst / "ballot-box.json").read_text())
        ghost = keypair("member:Ghost")
        gpub = pub_b64(ghost)
        b = {"decision_id": DECISION, "seq": 999,
             "nullifier": sha256_hex(b64d(gpub) + DECISION.encode()),
             "choice": OPTIONS[1], "voter_pub": gpub,
             "issuer_sig": doc["ballots"][0]["issuer_sig"], "channel": "app"}  # stolen credential sig
        b["voter_sig"] = sign_over(ghost, "voter:" + gpub, b)
        doc["ballots"].append(b)
        (dst / "ballot-box.json").write_text(json.dumps(doc, indent=1) + "\n")
    else:
        sys.exit(f"unknown tamper mode: {mode}")
    print(f"tampered ({mode}) -> {dst}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["run"]:
        run(Path(args[1]) if len(args) > 1 else Path(__file__).parent / "out")
    elif args[:1] == ["tamper"] and len(args) == 4:
        tamper(Path(args[1]), Path(args[2]), args[3])
    else:
        sys.exit(__doc__)
