#!/usr/bin/env python3
"""The Heeley Bank club vote, end to end — the smallest real run of the four verbs.

Simulates every actor in one process (key custody is NOT the property under test;
verification-from-artifacts is) and emits a transcript any independent party can check
with verify.py, which shares no code with this file.

  python3 clubvote.py run [outdir]               deterministic full election -> artifacts
  python3 clubvote.py tamper <out> <dst> <mode>  copy transcript, corrupt it. The modes are an
      escalation. One insider holding the log key: log (edit an entry) -> rehead (edit it and
      regenerate the heads, dropping the witness co-signatures they cannot forge) -> unwitness
      (and rewrite the manifest to declare there were never any witnesses). Attacks on the vote:
      box (swap a cast ciphertext), forge (stuff an unenrolled ballot), negate (a saboteur voter
      warps his own ciphertext out of the group), overvote (an enrolled voter encrypts 2 votes,
      and the committee accepts it). And, with the committee AND both witnesses colluding on a
      rewritten history: share (announce a rigged decryption), count (announce rigged counts).

Ballots are exponential-ElGamal encryptions to a 2-of-3 trustee key (RFC 3526 MODP-2048,
stdlib pow — auditable over compact): the box holds ciphertexts that are never individually
opened; the tally decrypts only their homomorphic SUM, each trustee share carrying a
Chaum-Pedersen correctness proof, each ballot a 0-or-1 validity proof (CDS). Deliberate
subtractions, declared in the emitted manifest rather than hidden: the trustee ceremony is
a dealer who knows the joint secret (DKG is the next rung), the issuer can link nullifiers
to the roster, sybil resistance is the plot register, receipt-freeness holds only if the
client discards its encryption randomness (this file does — r never outlives cast()).
See README.md.
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


# --------------------------------------------- the ballot group and its proofs
# RFC 3526 group 14: p a 2048-bit safe prime, g=2 generating the prime-order-q subgroup
# (q=(p-1)/2). The verifier pins these parameters by NAME — a transcript never supplies
# its own group, or it could supply a smooth one.

GROUP = "rfc3526-modp-2048"
P = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74"
    "020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F1437"
    "4FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF05"
    "98DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB"
    "9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718"
    "3995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF", 16)
Q = (P - 1) // 2
G = 2


def hx(n: int) -> str:
    return format(n, "x")


def det_scalar(label: str) -> int:
    # all demo "randomness" derives from the public seed, so the run is byte-reproducible
    return int.from_bytes(hashlib.shake_256(SEED + b"|" + label.encode()).digest(64)) % Q


def enc(m: int, r: int, h: int) -> dict:
    # exponential ElGamal: Enc(m; r) = (g^r, g^m * h^r) — additively homomorphic in m
    return {"c1": hx(pow(G, r, P)), "c2": hx(pow(G, m, P) * pow(h, r, P) % P)}


def fs_challenge(statement: dict) -> int:
    # Fiat-Shamir: the challenge is a hash of the full statement, so proofs are
    # non-interactive and bind to the exact ciphertext (no proof transplanting)
    return int.from_bytes(hashlib.sha256(canon(statement)).digest()) % Q


def prove01(m: int, r: int, ct: dict, h: int, ctx: str, label: str) -> dict:
    """CDS disjunctive proof that ct encrypts g^0 or g^1 — simulate the false branch,
    answer the true one, split the challenge so the verifier cannot tell which is which."""
    c1, c2 = int(ct["c1"], 16), int(ct["c2"], 16)
    f = 1 - m
    zf, cf = det_scalar(label + "|zf"), det_scalar(label + "|cf")
    uf = c2 * pow(pow(G, f, P), -1, P) % P
    af = pow(G, zf, P) * pow(c1, -cf, P) % P
    bf = pow(h, zf, P) * pow(uf, -cf, P) % P
    w = det_scalar(label + "|w")
    at, bt = pow(G, w, P), pow(h, w, P)
    a = {m: (at, bt), f: (af, bf)}
    stmt = {"t": "cds01", "ctx": ctx, "h": hx(h), "c1": ct["c1"], "c2": ct["c2"],
            "a0": hx(a[0][0]), "b0": hx(a[0][1]), "a1": hx(a[1][0]), "b1": hx(a[1][1])}
    c = fs_challenge(stmt)
    ct_ = (c - cf) % Q
    zt = (w + ct_ * r) % Q
    cc, zz = {m: ct_, f: cf}, {m: zt, f: zf}
    return {"a0": stmt["a0"], "b0": stmt["b0"], "a1": stmt["a1"], "b1": stmt["b1"],
            "c0": hx(cc[0]), "c1": hx(cc[1]), "z0": hx(zz[0]), "z1": hx(zz[1])}


def cp_prove(x_i: int, c1_sum: int, index: int, ctx: str) -> tuple[int, dict]:
    """Trustee share d = C1^x_i with a Chaum-Pedersen proof that log_g(h_i) = log_C1(d):
    the share is correct or the proof is impossible, no trust in the trustee required."""
    d = pow(c1_sum, x_i, P)
    w = det_scalar(f"cp|{index}|{ctx}")
    a, b = pow(G, w, P), pow(c1_sum, w, P)
    stmt = {"t": "cp", "ctx": ctx, "index": index, "h_i": hx(pow(G, x_i, P)),
            "c1": hx(c1_sum), "d": hx(d), "a": hx(a), "b": hx(b)}
    c = fs_challenge(stmt)
    z = (w + c * x_i) % Q
    return d, {"a": hx(a), "b": hx(b), "z": hx(z)}


# ---------------------------------------------------------------- the cast

COMMUNITY = "did:web:heeley-bank-allotments.example"
DECISION = "2026-agm-treasurer"
QUESTION = "Who shall serve as treasurer of Heeley Bank Allotment Society for 2026-27?"
OPTIONS = ["Sandra Okafor", "Keith Bramall"]  # encoding: m=1 is OPTIONS[0], m=0 is OPTIONS[1]

ACTORS = {
    "log": (COMMUNITY + "#log-1", "society log key (held by the committee)"),
    "issuer": (COMMUNITY + "#roster-1", "roster issuer (plot register, simulated)"),
    "witness-fed": ("did:web:sheffield-allotment-federation.example#w1", "witness"),
    "witness-meers": ("did:web:meersbrook-allotments.example#w1", "witness"),
}

# 2-of-3 trustees; two happen to also be witnesses, the third is a neutral neighbour.
# Trustees never sign anything — their shares are proven correct by mathematics (CP),
# so trust.json needs no trustee keys.
TRUSTEES = [
    {"did": "did:web:sheffield-allotment-federation.example", "index": 1},
    {"did": "did:web:meersbrook-allotments.example", "index": 2},
    {"did": "did:web:heeley-city-farm.example", "index": 3},
]
THRESHOLD = 2

# 60 plots; named actors hold the story roles, the rest are ordinary members
MEMBERS = ["Sandra Okafor", "Keith Bramall", "Nalini Mistry", "Ernest Toft", "Derek Wainwright"] + [
    f"Plot-holder {i:02d}" for i in range(6, 61)
]


def trustee_share(index: int) -> int:
    # dealer-based Feldman: f(z) = x + a1*z over Z_q; the dealer (the enrolment ceremony,
    # simulated) knows x — the declared subtraction DKG would remove
    return (det_scalar("dealer-x") + det_scalar("dealer-a1") * index) % Q


def election_pub() -> int:
    return pow(G, det_scalar("dealer-x"), P)


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


def build_tally(box: list, present_indices: list[int]) -> dict:
    """Homomorphically sum the counted set (last ballot per nullifier), threshold-decrypt
    the sum with the present trustees' shares, brute-force the small exponent. This is
    also what the colluding-committee tampers reuse: even they cannot skip the proofs."""
    latest = {}
    for b in sorted(box, key=lambda b: b["seq"]):
        latest[b["nullifier"]] = b
    C1 = C2 = 1
    for b in latest.values():
        C1 = C1 * int(b["ciphertext"]["c1"], 16) % P
        C2 = C2 * int(b["ciphertext"]["c2"], 16) % P
    shares = []
    for i in present_indices:
        d, proof = cp_prove(trustee_share(i), C1, i, DECISION)
        shares.append({"trustee": TRUSTEES[i - 1]["did"], "index": i,
                       "share": hx(d), "proof": proof})
    lagrange = {i: 1 for i in present_indices}
    for i in present_indices:
        for j in present_indices:
            if j != i:
                lagrange[i] = lagrange[i] * j % Q * pow(j - i, -1, Q) % Q
    D = 1
    for s in shares:
        D = D * pow(int(s["share"], 16), lagrange[s["index"]], P) % P
    gT = C2 * pow(D, -1, P) % P
    T, acc = None, 1
    for t in range(2 * len(latest) + 3):
        if acc == gT:
            T = t
            break
        acc = acc * G % P
    if T is None:
        raise ValueError("tally is not a small discrete log — a ciphertext was malformed")
    counts = {OPTIONS[0]: T, OPTIONS[1]: len(latest) - T}
    return {"latest": latest, "sum_ciphertext": {"c1": hx(C1), "c2": hx(C2)},
            "shares": shares, "counts": counts}


def tally_body(box: list, box_digest: str, present_indices: list[int], note: str) -> dict:
    t = build_tally(box, present_indices)
    return {
        "decision_id": DECISION,
        "method": "homomorphic exp-elgamal recount, 2-of-3 threshold decryption/v1 "
                  "(m=1 encodes options[0]; last ballot per nullifier counts)",
        "ballot_box_digest": box_digest,
        "sum_ciphertext": t["sum_ciphertext"],
        "trustee_shares": t["shares"],
        "counts": t["counts"],
        "distinct_voters": len(t["latest"]),
        "superseded": len(box) - len(t["latest"]),
        "note": note,
    }


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

    # --- the same ceremony deals the election key: 2-of-3 Feldman shares. The published
    # setup is only the commitments — h_i is DERIVED from them by any verifier, so a
    # mis-dealt setup cannot produce provable shares.
    h = election_pub()
    trustees_doc = {
        "community": COMMUNITY, "decision_id": DECISION, "group": GROUP,
        "threshold": {"required": THRESHOLD, "of": len(TRUSTEES)},
        "feldman_commitments": [hx(h), hx(pow(G, det_scalar("dealer-a1"), P))],
        "trustees": TRUSTEES,
        "note": "shares dealt at the enrolment ceremony in the parish room; the dealer "
                "knows the joint secret (declared subtraction — DKG is the next rung)",
    }
    (out / "trustees.json").write_text(json.dumps(trustees_doc, indent=1) + "\n")
    trustees_digest = sha256_hex(canon(trustees_doc))

    # --- manifest: what this deployment ACTUALLY upholds (subtraction is legible)
    manifest = {
        "v": "civic-kernel/manifest/v0",
        "community": {"id": COMMUNITY, "name": "Heeley Bank Allotment Society, Sheffield (prototype run)",
                      "parent": "did:web:sheffield-allotment-federation.example"},
        "services": {"personhood": True, "decisions": True, "rights_guard": False, "transparency_log": True},
        "personhood": {"method": "platform-account", "issuer": "plot-register roster (simulated ceremony)",
                       "unlinkable": False, "sybil_resistance": "weak",
                       "eligibility_rules": "plot-register/2026 " + roster_digest},
        "decisions": {"verifiable": True, "receipt_free": True, "cast_or_audit": True,
                      "paper_channel": False, "coercion_resistance": "revote-silent",
                      "trustee_quorum": "2-of-3: Sheffield Allotment Federation, "
                                        "Meersbrook Allotments, Heeley City Farm"},
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
        "note": "Prototype run. Declares: roster personhood (sybil-weak, linkable), ballots "
                "encrypted to a 2-of-3 trustee key and never individually opened — only the "
                "homomorphic sum is decrypted; receipt-free at the transcript level (the "
                "client must discard its encryption randomness after cast; a retained r "
                "reconstructs a receipt), cast-or-audit device challenges, silent re-vote, "
                "no rights guard, no paper channel."}, t(1, 19))
    log.append("x-roster.published", {"roster_digest": roster_digest, "member_count": len(MEMBERS)}, t(1, 19, 5))
    log.append("x-trustees.published", {
        "trustees_digest": trustees_digest, "threshold": "2-of-3",
        "trustees": [tr["did"] for tr in TRUSTEES]}, t(1, 19, 10))
    log.append("decision.opened", {
        "decision_id": DECISION, "question": QUESTION, "question_hash": sha256_hex(QUESTION.encode()),
        "options": OPTIONS, "eligibility_rules": "roster " + roster_digest,
        "recast_policy": "last-ballot-counts",
        "window": {"deliberation_ends": t(14, 18), "cast_ends": t(21, 18)}}, t(7, 18))

    # --- casting (prove part 2 + cast/challenge). The DEVICE encrypts the choice to the
    # trustee key and proves the plaintext is 0 or 1; the box holds ciphertexts that no
    # one will ever individually open. Before casting, a voter may CHALLENGE: the device
    # must reveal (choice, r), and since it cannot tell a challenge from a cast when it
    # encrypts, a cheating device is caught with probability = the challenge rate
    # (Benaloh). A challenged ciphertext is a receipt by construction, so it is spoiled —
    # logged in the audit file, never cast. After a real cast, r is discarded: nothing
    # this function returns can prove what the ballot says.
    h_pub = h
    box, seq, audits = [], 0, []

    def device_encrypt(choice, who, attempt, cheat=False):
        m = 1 if choice == OPTIONS[0] else 0
        if cheat:
            m = 0  # commits to Keith whatever it displays
        r = det_scalar(f"ballot|{who}|{attempt}")
        return enc(m, r, h_pub), m, r

    def challenge(name, choice, attempt, cheat=False):
        ct, m, r = device_encrypt(choice, name, attempt, cheat)
        opened = OPTIONS[0] if m == 1 else OPTIONS[1]
        rec = {"ciphertext": ct, "claimed_choice": choice, "opened_choice": opened,
               "opened_r": hx(r), "outcome": "match" if opened == choice else "MISMATCH"}
        audits.append(rec)
        return rec

    def cast(name, choice, channel="app", witness=None, attempt=0):
        nonlocal seq
        seq += 1
        voter = keypair("member:" + name)
        vpub = pub_b64(voter)
        cred = next(c for c in roster if c["voter_pub"] == vpub)
        ct, m, r = device_encrypt(choice, name, attempt)
        proof = prove01(m, r, ct, h_pub, DECISION, f"cds|{name}|{attempt}")
        ballot = {"decision_id": DECISION, "seq": seq,
                  "nullifier": sha256_hex(b64d(vpub) + DECISION.encode()),
                  "ciphertext": ct, "proof": proof, "voter_pub": vpub,
                  "issuer_sig": cred["issuer_sig"], "channel": channel}
        if witness:
            ballot["witness_sig"] = sign_over(keypair("member:" + witness),
                                              "assisted-witness:" + witness, ballot)
        ballot["voter_sig"] = sign_over(voter, "voter:" + vpub, ballot)
        box.append(ballot)  # m and r go out of scope here — that is the receipt-freeness

    # ordinary members vote (deterministic split; sealed ciphertexts enter the box)
    for i, name in enumerate(MEMBERS[5:]):
        if i % 8 == 7:
            continue  # abstainers
        cast(name, OPTIONS[0] if i % 7 < 4 else OPTIONS[1])
    # routine deterrence: two cautious members challenge first, see a match, then cast fresh
    challenge("Sandra Okafor", OPTIONS[0], attempt=0)
    cast("Sandra Okafor", OPTIONS[0], attempt=1)
    cast("Keith Bramall", OPTIONS[1])
    cast("Derek Wainwright", OPTIONS[1])
    # Plot-holder 23's phone is compromised: it displays Sandra but encrypts Keith.
    # She challenges on a whim — the opened encryption does not match, the failure is
    # logged publicly, and she recasts from the clubhouse kiosk: her earlier cast from
    # that phone is silently superseded (and stays sealed forever — nobody will ever
    # learn what the compromised phone actually encrypted). The two remedies compose —
    # cast-or-audit caught the device, and the recast policy repaired the vote.
    caught = challenge("Plot-holder 23", OPTIONS[0], attempt=1, cheat=True)
    log.append("x-ballot.audit-failed", {
        "decision_id": DECISION, "ciphertext": caught["ciphertext"],
        "claimed_choice": caught["claimed_choice"], "opened_choice": caught["opened_choice"],
        "note": "cast-or-audit challenge: device display disagreed with its opened encryption; "
                "ciphertext spoiled, member recast from a clean device"}, t(9, 11))
    cast("Plot-holder 23", OPTIONS[0], channel="kiosk", attempt=2)
    # Nalini votes, thinks about the water-rate surplus overnight, and silently re-votes:
    cast("Nalini Mistry", OPTIONS[1])
    cast("Nalini Mistry", OPTIONS[0], attempt=1)   # same nullifier, later seq -> supersedes
    # Ernest (no smartphone, trusts none of it) casts through the assisted channel, two
    # tellers at the table; the second teller runs one challenge in front of him first:
    challenge("Ernest Toft", OPTIONS[1], attempt=0)
    cast("Ernest Toft", OPTIONS[1], channel="assisted", witness="Plot-holder 12", attempt=1)
    # Derek tries to mint an extra voice for his unenrolled cousin: no roster credential
    try:
        cast("Cousin Ray", OPTIONS[1])
    except StopIteration:
        rejected = {"attempt": "cast by unenrolled key", "member": "Cousin Ray",
                    "result": "rejected: no roster credential"}

    box_doc = {"decision_id": DECISION, "ballots": box}
    (out / "ballot-box.json").write_text(json.dumps(box_doc, indent=1) + "\n")
    box_digest = sha256_hex(canon(box_doc))
    audits_doc = {"decision_id": DECISION, "audits": audits}
    (out / "audits.json").write_text(json.dumps(audits_doc, indent=1) + "\n")
    audits_digest = sha256_hex(canon(audits_doc))

    # --- close: casting ends
    log.append("decision.closed", {
        "decision_id": DECISION, "ballot_box_digest": box_digest,
        "ballots_recorded": len(box), "audits_digest": audits_digest,
        "commitments_audited": len(audits),
        "audit_failures": sum(1 for a in audits if a["outcome"] == "MISMATCH"),
        "rejected_at_cast": [rejected]}, t(21, 18))

    # --- tally: two of the three trustees decrypt the SUM (Meersbrook's secretary is in
    # Whitby with the key card in a drawer — the threshold is the point). No individual
    # ballot is opened; the tally proof lives in the log itself.
    body = tally_body(box, box_digest, [1, 3],
                      "Meersbrook trustee share absent (secretary away); quorum met 2-of-3 "
                      "by the Federation and Heeley City Farm")
    log.append("decision.tally-proof", body, t(21, 18, 30))

    (out / "log.jsonl").write_text("".join(json.dumps(e) + "\n" for e in log.entries))
    (out / "heads.jsonl").write_text("".join(json.dumps(h_) + "\n" for h_ in log.heads))

    # --- trust anchors: what a verifier must already trust (in reality: DID resolution +
    # the witness ecosystem). `witnesses` is the bar the transcript cannot lower: the
    # manifest is signed by the log key, so it cannot vouch for its own witness count.
    # No trustee keys here — trustee shares are proven by Chaum-Pedersen against the
    # Feldman commitments, which ride the witnessed log; and the election key cannot be
    # swapped either, because every voter's validity proof binds to it under a signature
    # only that voter can make.
    keys = {ACTORS[a][0]: pub_b64(keypair(a)) for a in ACTORS}
    keys[COMMUNITY + "#manifest-1"] = pub_b64(keypair("log"))
    keys["assisted-witness:Plot-holder 12"] = pub_b64(keypair("member:Plot-holder 12"))
    (out / "trust.json").write_text(json.dumps(
        {"keys": keys, "witnesses": manifest["transparency_log"]["witnesses"]}, indent=1) + "\n")

    counts = body["counts"]
    print(f"run complete -> {out}")
    print(f"  {len(MEMBERS)} enrolled, {len(box)} ballots ({body['distinct_voters']} counted, "
          f"{body['superseded']} superseded), 1 unenrolled cast rejected")
    print(f"  {len(audits)} cast-or-audit challenges, "
          f"{sum(1 for a in audits if a['outcome'] == 'MISMATCH')} cheating device caught and logged")
    print(f"  tally (threshold-decrypted sum; no ballot ever opened): "
          + ", ".join(f"{k} {v}" for k, v in counts.items()))


# ---------------------------------------------------------------- tampers

def reforge(dst: Path, entries: list, with_witnesses=False):
    """Re-sign every entry and regenerate every head from the history the insider wishes
    were true. They hold the log key, so all of that is available to them. Without the
    witnesses' keys the heads come out carrying one signature where they carried three;
    with_witnesses simulates the total-collusion case where the witnesses co-sign the lie.
    """
    for e in entries:
        del e["sig"]
        e["sig"] = sign_over(keypair("log"), ACTORS["log"][0], e)
    (dst / "log.jsonl").write_text("".join(json.dumps(e) + "\n" for e in entries))
    heads = []
    for n in range(1, len(entries) + 1):
        leaves = [leaf_hash(canon({k: v for k, v in e.items() if k != "sig"})) for e in entries[:n]]
        head = {"log_id": COMMUNITY, "size": n, "root": "sha256:" + merkle_root(leaves).hex(),
                "timestamp": entries[n - 1]["timestamp"]}
        sigs = [sign_over(keypair("log"), ACTORS["log"][0], head)]
        if with_witnesses:
            for w in ("witness-fed", "witness-meers"):
                sigs.append(sign_over(keypair(w), ACTORS[w][0], head))
        heads.append({**head, "sigs": sigs})
    (dst / "heads.jsonl").write_text("".join(json.dumps(h) + "\n" for h in heads))


def load_entries(dst: Path) -> list:
    return [json.loads(l) for l in (dst / "log.jsonl").read_text().splitlines()]


def entry(entries: list, type_: str) -> dict:
    return next(e for e in entries if e["type"] == type_)


def rewrite_box(dst: Path, mutate, collude=False):
    """Apply `mutate` to the ballot box. If the committee colludes, it repairs the box
    digest in the log, re-runs the threshold decryption honestly over the poisoned box,
    and the witnesses co-sign the rewritten history — every hash and signature then
    agrees, and only the voter-level proofs can object."""
    doc = json.loads((dst / "ballot-box.json").read_text())
    mutate(doc["ballots"])
    (dst / "ballot-box.json").write_text(json.dumps(doc, indent=1) + "\n")
    if collude:
        digest = sha256_hex(canon(doc))
        entries = load_entries(dst)
        entry(entries, "decision.closed")["body"]["ballot_box_digest"] = digest
        old = entry(entries, "decision.tally-proof")["body"]
        entry(entries, "decision.tally-proof")["body"] = tally_body(
            doc["ballots"], digest, [1, 3], old["note"])
        reforge(dst, entries, with_witnesses=True)


def resign_ballot(b: dict, name: str):
    voter = keypair("member:" + name)
    for k in ("voter_sig",):
        b.pop(k, None)
    b["voter_sig"] = sign_over(voter, "voter:" + b["voter_pub"], b)


def tamper(src: Path, dst: Path, mode: str):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    derek_null = sha256_hex(b64d(pub_b64(keypair("member:Derek Wainwright"))) + DECISION.encode())
    if mode == "log":
        # An INSIDER rewrites history: the committee holds the log key, edits the recorded
        # question after the fact and re-signs it validly. Every signature still verifies —
        # but the entry's Merkle leaf changed, so the already-published heads no longer
        # root the log they claim to. This is caught by consistency alone, and needs no
        # witnesses; the insider who thinks to regenerate the heads is mode "rehead".
        entries = load_entries(dst)
        e = entry(entries, "decision.opened")
        e["body"]["question"] = QUESTION.replace("treasurer", "treasurer-for-life")
        del e["sig"]
        e["sig"] = sign_over(keypair("log"), ACTORS["log"][0], e)
        (dst / "log.jsonl").write_text("".join(json.dumps(x) + "\n" for x in entries))
    elif mode == "rehead":
        # The insider's BEST move against a witnessed log. Editing an entry alone (mode
        # "log") breaks the head roots and is caught by plain Merkle consistency — no
        # witnesses required. So the insider goes further: edit the entry AND regenerate
        # every head to match, re-signing each with the log key they hold. They cannot
        # forge the federation's and Meersbrook's co-signatures, so their only move is to
        # drop them. The transcript is now internally consistent and every signature on it
        # verifies. The one thing that betrays the rewrite is who ISN'T on the heads.
        entries = load_entries(dst)
        entry(entries, "decision.opened")["body"]["question"] = \
            QUESTION.replace("treasurer", "treasurer-for-life")
        reforge(dst, entries)
    elif mode == "unwitness":
        # ...and the insider's follow-up, once told the manifest is what declares the
        # witnesses: rewrite the manifest to declare none, repair the logged manifest
        # digest, and regenerate the heads. Now nothing INSIDE the transcript is
        # inconsistent — the manifest, signed by the log key the insider holds, simply
        # says this log never had witnesses. Only a bar set outside the transcript (the
        # verifier's trust anchors) can still catch it. A manifest cannot be its own standard.
        manifest = json.loads((dst / "manifest.json").read_text())
        manifest["transparency_log"]["witnesses"] = []
        del manifest["sig"]
        manifest["sig"] = sign_over(keypair("log"), COMMUNITY + "#manifest-1", manifest)
        (dst / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
        entries = load_entries(dst)
        entry(entries, "manifest.published")["body"]["manifest_digest"] = sha256_hex(
            canon({k: v for k, v in manifest.items() if k != "sig"}))
        entry(entries, "decision.opened")["body"]["question"] = \
            QUESTION.replace("treasurer", "treasurer-for-life")
        reforge(dst, entries)
    elif mode == "box":  # quietly swap one ballot's ciphertext for an encryption of the other option
        rewrite_box(dst, lambda ballots: ballots[0].__setitem__(
            "ciphertext", enc(0, det_scalar("tamper-box"), election_pub())))
    elif mode == "forge":  # stuff the box with a ballot from a key the issuer never signed
        def stuff(ballots):
            ghost = keypair("member:Ghost")
            gpub = pub_b64(ghost)
            b = {"decision_id": DECISION, "seq": 999,
                 "nullifier": sha256_hex(b64d(gpub) + DECISION.encode()),
                 "ciphertext": ballots[0]["ciphertext"], "proof": ballots[0]["proof"],
                 "voter_pub": gpub,
                 "issuer_sig": ballots[0]["issuer_sig"], "channel": "app"}  # stolen credential sig
            b["voter_sig"] = sign_over(ghost, "voter:" + gpub, b)
            ballots.append(b)
        rewrite_box(dst, stuff)
    elif mode == "negate":
        # A saboteur VOTER (enrolled — it is Derek) warps his own ciphertext out of the
        # prime-order subgroup: c2 -> -c2, validly re-signed with his own voter key. The
        # sum then decrypts to no small exponent at all and the election is griefed —
        # UNLESS the verifier checks group membership per ballot, which pins the sabotage
        # to this ballot instead of leaving an unattributable dead tally.
        def negate(ballots):
            b = next(b for b in ballots if b["nullifier"] == derek_null)
            b["ciphertext"]["c2"] = hx(P - int(b["ciphertext"]["c2"], 16))
            resign_ballot(b, "Derek Wainwright")
        rewrite_box(dst, negate)
    elif mode == "overvote":
        # An enrolled voter (Derek again) encrypts m=2 — two votes for Sandra in one
        # ballot — signs it validly, and the corrupt committee ACCEPTS it: box digest
        # repaired, sum re-decrypted honestly, witnesses co-sign the history. Every hash,
        # signature and trustee proof in the transcript now agrees. The only thing that
        # cannot be manufactured is the 0-or-1 validity proof for a ballot that encrypts 2.
        def overvote(ballots):
            b = next(b for b in ballots if b["nullifier"] == derek_null)
            b["ciphertext"] = enc(2, det_scalar("tamper-overvote"), election_pub())
            resign_ballot(b, "Derek Wainwright")  # keeps his old proof: it binds to the old ciphertext
        rewrite_box(dst, overvote, collude=True)
    elif mode == "share":
        # Total signature collusion: the committee AND both witnesses rewrite the tally to
        # make Keith win, regenerating heads with all three signatures. The counts, the
        # combined decryption and one share are arithmetically consistent with the lie —
        # but a Chaum-Pedersen proof for the rigged share requires a secret the committee
        # does not hold. The tally survives even those who sign the history.
        entries = load_entries(dst)
        body = entry(entries, "decision.tally-proof")["body"]
        n = body["distinct_voters"]
        rig_T = n // 3  # hand Keith a comfortable win
        C1, C2 = (int(body["sum_ciphertext"][k], 16) for k in ("c1", "c2"))
        lam1, lam3 = 3 * pow(2, -1, Q) % Q, (Q - pow(2, -1, Q)) % Q
        d1 = int(body["trustee_shares"][0]["share"], 16)  # honest share, honest proof
        D_rig = C2 * pow(G, -rig_T, P) % P
        d3_rig = pow(D_rig * pow(d1, -lam1, P) % P, pow(lam3, -1, Q), P)
        body["trustee_shares"][1]["share"] = hx(d3_rig)  # its old proof is now impossible
        body["counts"] = {OPTIONS[0]: rig_T, OPTIONS[1]: n - rig_T}
        reforge(dst, entries, with_witnesses=True)
    elif mode == "count":
        # Same total collusion, lazier lie: honest shares, honest proofs, rigged counts.
        # Anyone redoing the recount — combine the proven shares, brute-force the small
        # exponent — gets the true numbers and the announcement refutes itself.
        entries = load_entries(dst)
        body = entry(entries, "decision.tally-proof")["body"]
        a, b = body["counts"][OPTIONS[0]], body["counts"][OPTIONS[1]]
        body["counts"] = {OPTIONS[0]: b, OPTIONS[1]: a}
        reforge(dst, entries, with_witnesses=True)
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
