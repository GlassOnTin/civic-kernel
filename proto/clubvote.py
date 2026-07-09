#!/usr/bin/env python3
"""The Heeley Bank club vote, end to end — the smallest real run of the four verbs.

Simulates every actor in one process (key custody is NOT the property under test;
verification-from-artifacts is) and emits a transcript any independent party can check
with verify.py, which shares no code with this file.

  python3 clubvote.py run [outdir] [--real]      full election -> artifacts. Default: every
      secret derives from a public seed — byte-reproducible, zero privacy, by design.
      --real draws every key and scalar from the OS instead: same artifact set, same
      verifier, real secrets — and no tampering, because the tampers below simulate
      insiders who hold the demo keys, which a --real transcript's insiders do not.
  python3 clubvote.py collect <out> <dst> <ballot.json>...   the committee's side of a page
      cast: copy the transcript, add externally built ballots (e.g. from cast.html) to the
      box, then legitimately re-run everything downstream of it — box digest, tally,
      heads, anchor. Ballots are accepted, not judged: verify.py is the judge, so run it
      on <dst> afterwards. Demo-seed transcripts only (the committee keys must be held).
  python3 clubvote.py tamper <out> <dst> <mode>  copy transcript, corrupt it. The modes are an
      escalation. One insider holding the log key: log (edit an entry) -> rehead (edit it and
      regenerate the heads, dropping the witness co-signatures they cannot forge) -> unwitness
      (and rewrite the manifest to declare there were never any witnesses) -> roster (rewrite
      the eligibility rule in the published register). Attacks on the vote: box (swap a cast
      ciphertext), stuff (mint an extra ballot), doublevote (an enrolled voter negates his own
      linking tag to vote twice), smuggle (slip a malformed, out-of-subgroup ciphertext past the
      CDS proof as a superseded ballot), overvote (encrypt 2 votes, committee accepts). Most
      of the vote attacks assume the committee AND both witnesses collude on a rewritten
      history; the next two are pure tally lies under the same collusion: share (announce a
      rigged decryption), count (announce rigged counts). The last, drop, forges NOTHING:
      the same collusion erases a counted ballot and re-signs the shortened history end to
      end — deniability, not forgery — and only the externally anchored closing head objects.

Ballots are anonymous. Eligibility is proven, not asserted: each ballot carries a linkable
ring signature (LSAG, Liu-Wei-Wong 2004) over the whole published roster, proving the signer
holds SOME roster secret without revealing which, and binding the ballot to a per-decision
linking tag H(decision_id)^x — §3.1's `nym_secret x context_id` pseudonym, in the exponent.
Same voter twice in one decision: same tag, so the last ballot supersedes. Same voter in
another decision: another context generator, so nothing links.

Ballots are exponential-ElGamal encryptions to a 2-of-3 trustee key (RFC 3526 MODP-2048,
stdlib pow — auditable over compact): the box holds ciphertexts that are never individually
opened; the tally decrypts only their homomorphic SUM, each trustee share carrying a
Chaum-Pedersen correctness proof, each ballot a 0-or-1 validity proof (CDS). The key is
generated distributively — each trustee deals their own Feldman-committed polynomial, and
no party ever holds the joint secret. Deliberate subtractions, declared in the emitted
manifest rather than hidden: the DKG has no hash-commitment round (a rushing trustee could
bias the key's distribution), the anonymity set is the roster and the proof is linear in it,
sybil resistance is the plot register, receipt-freeness holds only if the client discards its
encryption randomness (this file does — r never outlives cast()). See README.md.
"""
import base64
import hashlib
import json
import secrets
import shutil
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# ---------------------------------------------------------------- primitives

SEED = b"civic-kernel/proto/clubvote/v0"  # deterministic demo: zero privacy, by design
REAL = False  # run --real: keys and scalars come from the OS, not the seed. A label then
# names a value only within this process (nyms and DKG shares are re-derived across
# functions), instead of deriving it for the world forever.
_real: dict = {}


def canon(obj) -> bytes:
    # JCS (RFC 8785) approximation: exact for this artifact set (strings/ints/bools only)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def keypair(name: str) -> Ed25519PrivateKey:
    if REAL:
        if "key|" + name not in _real:
            _real["key|" + name] = Ed25519PrivateKey.generate()
        return _real["key|" + name]
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


def rand_scalar(label: str) -> int:
    if REAL:
        if label not in _real:
            _real[label] = secrets.randbelow(Q)
        return _real[label]
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
    zf, cf = rand_scalar(label + "|zf"), rand_scalar(label + "|cf")
    uf = c2 * pow(pow(G, f, P), -1, P) % P
    af = pow(G, zf, P) * pow(c1, -cf, P) % P
    bf = pow(h, zf, P) * pow(uf, -cf, P) % P
    w = rand_scalar(label + "|w")
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
    w = rand_scalar(f"cp|{index}|{ctx}")
    a, b = pow(G, w, P), pow(c1_sum, w, P)
    stmt = {"t": "cp", "ctx": ctx, "index": index, "h_i": hx(pow(G, x_i, P)),
            "c1": hx(c1_sum), "d": hx(d), "a": hx(a), "b": hx(b)}
    c = fs_challenge(stmt)
    z = (w + c * x_i) % Q
    return d, {"a": hx(a), "b": hx(b), "z": hx(z)}


# ------------------------------------- unlinkable eligibility: the ring and the tag
# §3.1 asks eligibility for `prove(eligible, decision_id) -> pseudonym + proof`, with the
# pseudonym derived as `nym_secret x context_id`. Here context_id is a subgroup generator
# hashed from the decision, and the pseudonym — the nullifier — is that generator raised
# to the voter's nym secret. The proof is a linkable ring signature over the whole roster:
# it proves the signer knows SOME roster secret and that the nullifier is that same
# secret's tag, without revealing which roster entry signed. This is the village-scale
# instantiation of the abstraction; BBS (§13) is the one that scales.


def nym_secret(name: str) -> int:
    return rand_scalar("nym|" + name)  # in a deployment: generated on the voter's device


def context_gen(ctx: str) -> int:
    """A subgroup generator whose discrete log to base G nobody knows: square a hash.
    A different decision means a different generator, so tags never link across decisions."""
    for i in range(64):
        c = int.from_bytes(hashlib.sha256(f"civic-kernel/ctx|{ctx}|{i}".encode()).digest()) % P
        if c > 1 and pow(c, 2, P) != 1:
            return pow(c, 2, P)
    raise ValueError("no context generator")


def link_tag(x: int, ctx: str) -> int:
    return pow(context_gen(ctx), x, P)


def ring_challenge(ring_digest: str, ctx: str, msg: str, tag: int, z1: int, z2: int) -> int:
    # 256-bit challenge (not reduced mod q): ample for soundness, and eight times cheaper
    # as an exponent than a full-width one. The ring digest binds the signature to THIS
    # ring, so a ballot cannot be replayed against a roster it was not signed over.
    return int.from_bytes(hashlib.sha256(canon(
        {"t": "lsag", "ring": ring_digest, "ctx": ctx, "msg": msg,
         "tag": hx(tag), "z1": hx(z1), "z2": hx(z2)})).digest())


def ring_sign(ring: list[int], pi: int, x: int, ctx: str, msg: str, ring_digest: str,
              label: str, tag: int | None = None) -> tuple[dict, int]:
    """LSAG: simulate every ring position but the signer's, answer that one for real, and
    close the challenge chain back onto itself. Returns (signature, challenge at the
    signer's index) — the caller needs the latter only when forging a tag (see doublevote).
    """
    n = len(ring)
    hl = context_gen(ctx)
    tag = pow(hl, x, P) if tag is None else tag
    u = rand_scalar(label + "|u")
    c, s = [0] * n, [0] * n
    c[(pi + 1) % n] = ring_challenge(ring_digest, ctx, msg, tag, pow(G, u, P), pow(hl, u, P))
    i = (pi + 1) % n
    while i != pi:
        s[i] = rand_scalar(f"{label}|s|{i}")
        z1 = pow(G, s[i], P) * pow(ring[i], c[i], P) % P
        z2 = pow(hl, s[i], P) * pow(tag, c[i], P) % P
        c[(i + 1) % n] = ring_challenge(ring_digest, ctx, msg, tag, z1, z2)
        i = (i + 1) % n
    s[pi] = (u - x * c[pi]) % Q
    return {"c0": hx(c[0]), "s": [hx(v) for v in s]}, c[pi]


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
    "anchor": ("did:web:sheffield-star.example#notices-1",
               "external anchor: the newspaper's public-notices column (simulated)"),
}
# Members hold no signing key at all: the ballot is signed by the RING, not by a name.
# What the issuer certifies is a nym public key g^x — the entry in the anonymity set.

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


def dkg_polys() -> dict:
    # Pedersen-style DKG: each trustee deals their OWN degree-1 polynomial f_j(z) =
    # a_j0 + a_j1*z over Z_q. The joint secret x = sum_j a_j0 is never assembled anywhere;
    # trustee i's share is x_i = sum_j f_j(i), and the joint polynomial F = sum_j f_j has
    # F(0) = x, so any 2 shares reconstruct exponents of x — of a number no one knows.
    return {j: (rand_scalar(f"dkg|{j}|a0"), rand_scalar(f"dkg|{j}|a1")) for j in (1, 2, 3)}


def trustee_share(index: int) -> int:
    return sum(a0 + a1 * index for a0, a1 in dkg_polys().values()) % Q


def election_pub() -> int:
    return pow(G, sum(a0 for a0, _ in dkg_polys().values()) % Q, P)


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

    # --- ceremony (prove, part 1): the issuer certifies each member's nym public key.
    # This is the last time a name and a key appear together. Everything downstream sees
    # the ring — the set of keys — and never learns which of them signed a ballot.
    issuer = keypair("issuer")
    roster = []
    for name in MEMBERS:
        cred = {"member": name, "voter_pub": hx(pow(G, nym_secret(name), P))}
        cred["issuer_sig"] = sign_over(issuer, ACTORS["issuer"][0], cred)
        roster.append(cred)
    roster_doc = {"community": COMMUNITY, "eligibility": "plot-register/2026: one vote per named plot-holder",
                  "members": roster}
    (out / "roster.json").write_text(json.dumps(roster_doc, indent=1) + "\n")
    roster_digest = sha256_hex(canon(roster_doc))
    ring = [int(c["voter_pub"], 16) for c in roster]
    ring_index = {y: i for i, y in enumerate(ring)}
    # the ring signature binds to the KEYS, not to the whole register: rewriting the
    # eligibility prose is a records attack for the logged digest to catch, not a
    # reason for every honest voter's proof to stop verifying
    ring_digest = sha256_hex(canon([c["voter_pub"] for c in roster]))

    # --- the trustees generate the election key TOGETHER: each deals their own
    # Feldman-committed polynomial and sends every other trustee a private share, which
    # the recipient verifies against the dealer-trustee's commitments before accepting.
    # The published setup is only the per-trustee commitments — the election key and
    # every h_i are DERIVED from their product by any verifier, so a mis-run ceremony
    # cannot produce provable shares, and no party ever holds the joint secret.
    polys = dkg_polys()
    comms = {j: [pow(G, a0, P), pow(G, a1, P)] for j, (a0, a1) in polys.items()}
    for j, (a0, a1) in polys.items():          # each recipient's Feldman check
        for i in (1, 2, 3):
            assert pow(G, (a0 + a1 * i) % Q, P) == comms[j][0] * pow(comms[j][1], i, P) % P
    h = election_pub()
    trustees_doc = {
        "community": COMMUNITY, "decision_id": DECISION, "group": GROUP,
        "threshold": {"required": THRESHOLD, "of": len(TRUSTEES)},
        "trustees": [{**tr, "commitments": [hx(c) for c in comms[tr["index"]]]}
                     for tr in TRUSTEES],
        "note": "distributed key generation in the parish room: each trustee dealt their "
                "own polynomial and exchanged Feldman-verified shares; no party — not the "
                "committee, not the ceremony, not any single trustee — ever held the joint "
                "secret. Not defended: a trustee who waits to see the others' commitments "
                "before choosing their own could bias the key's distribution (the rushing "
                "attack, Gennaro et al.); the fix is a hash-commitment round that a single "
                "transcript cannot evidence, so it is declared instead",
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
                       "unlinkable": True, "sybil_resistance": "weak",
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
        "note": "Prototype run. Declares: roster personhood, sybil-weak but UNLINKABLE — a "
                "ballot proves membership of the roster ring by linkable ring signature and "
                "carries a per-decision pseudonym H(decision)^nym_secret, so no party, the "
                "issuer included, learns who cast which ballot, and nothing links a voter "
                "across decisions (the anonymity set is the roster; the proof is linear in "
                "it). Ballots encrypted to a distributively-generated 2-of-3 trustee key (no "
                "dealer; no party ever holds the joint secret) and never individually opened "
                "— only the homomorphic sum is decrypted; receipt-free at the transcript "
                "level (the client must discard its encryption randomness after cast; a "
                "retained r reconstructs a receipt), cast-or-audit device challenges, silent "
                "re-vote, no rights guard, no paper channel."}, t(1, 19))
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
    # this function returns can prove what the ballot says. Nor WHO said it: the ballot is
    # signed by the ring, so what leaves this function is "some plot-holder, exactly once."
    h_pub = h
    box, seq, audits = [], 0, []

    def device_encrypt(choice, who, attempt, cheat=False):
        m = 1 if choice == OPTIONS[0] else 0
        if cheat:
            m = 0  # commits to Keith whatever it displays
        r = rand_scalar(f"ballot|{who}|{attempt}")
        return enc(m, r, h_pub), m, r

    def challenge(name, choice, attempt, cheat=False):
        ct, m, r = device_encrypt(choice, name, attempt, cheat)
        opened = OPTIONS[0] if m == 1 else OPTIONS[1]
        rec = {"ciphertext": ct, "claimed_choice": choice, "opened_choice": opened,
               "opened_r": hx(r), "outcome": "match" if opened == choice else "MISMATCH"}
        audits.append(rec)
        return rec

    def cast(name, choice, attempt=0, cheat=False):
        nonlocal seq
        x = nym_secret(name)
        pi = ring_index[pow(G, x, P)]      # KeyError = not a plot-holder; nothing to sign with
        seq += 1
        ct, m, r = device_encrypt(choice, name, attempt, cheat)
        proof = prove01(m, r, ct, h_pub, DECISION, f"cds|{name}|{attempt}")
        ballot = {"decision_id": DECISION, "seq": seq, "nullifier": hx(link_tag(x, DECISION)),
                  "ciphertext": ct, "proof": proof}
        ballot["ring_sig"], _ = ring_sign(ring, pi, x, DECISION, sha256_hex(canon(ballot)),
                                          ring_digest, f"lsag|{name}|{attempt}")
        box.append(ballot)  # m, r and pi all go out of scope here: no receipt, no name
        _real.pop(f"ballot|{name}|{attempt}", None)  # and under --real, r dies with them

    # Who turns up to an allotment AGM: about a plot in six, and the five named members.
    # Sandra and Ernest challenge their devices first and cast on the next attempt.
    # Plot-holder 23's phone is compromised — it displays Sandra and encrypts Keith — so
    # her first cast is a lie she does not know she told. She challenges on a whim, the
    # opened encryption does not match, the failure is logged publicly, and she recasts
    # from the clubhouse kiosk: the phone's ballot is silently superseded, and stays
    # sealed forever. Nobody will ever learn what it said. The two remedies compose —
    # cast-or-audit caught the device, the recast policy repaired the vote.
    # Nalini votes, thinks about the water-rate surplus overnight, and re-votes: same
    # linking tag, later seq, so the first ballot is superseded without anyone knowing
    # it was hers. Ernest (no smartphone, trusts none of it) votes at the table with two
    # tellers; his ballot carries no mark of that — an "assisted" label on one ballot in
    # a ring of sixty would name him.
    def turns_out(name: str) -> bool:
        return hashlib.sha256(("turnout|" + name).encode()).digest()[0] < 30

    def leaning(name: str) -> str:
        return OPTIONS[hashlib.sha256(("choice|" + name).encode()).digest()[0] % 7 // 4]

    plan = [(n, leaning(n), 0, False) for n in MEMBERS[5:]
            if turns_out(n) and n != "Plot-holder 23"]
    plan += [("Sandra Okafor", OPTIONS[0], 1, False),
             ("Keith Bramall", OPTIONS[1], 0, False),
             ("Derek Wainwright", OPTIONS[1], 0, False),
             ("Nalini Mistry", OPTIONS[1], 0, False),
             ("Nalini Mistry", OPTIONS[0], 1, False),   # same tag, later seq -> supersedes
             ("Plot-holder 23", OPTIONS[0], 0, True),   # the compromised phone
             ("Plot-holder 23", OPTIONS[0], 2, False),  # the clubhouse kiosk, after the challenge
             ("Ernest Toft", OPTIONS[1], 1, False)]
    # Cast order is not roster order. `seq` decides which of a voter's ballots counts, so
    # it has to be in the signed ballot — which means it must carry no trace of who cast it.
    plan.sort(key=lambda p: (hashlib.sha256(("order|" + p[0]).encode()).hexdigest(), p[2]))
    for name, choice, attempt, cheat in plan:
        cast(name, choice, attempt, cheat)

    challenge("Sandra Okafor", OPTIONS[0], attempt=0)
    challenge("Ernest Toft", OPTIONS[1], attempt=0)
    caught = challenge("Plot-holder 23", OPTIONS[0], attempt=1, cheat=True)
    log.append("x-ballot.audit-failed", {
        "decision_id": DECISION, "ciphertext": caught["ciphertext"],
        "claimed_choice": caught["claimed_choice"], "opened_choice": caught["opened_choice"],
        "note": "cast-or-audit challenge: device display disagreed with its opened encryption; "
                "ciphertext spoiled, member recast from a clean device"}, t(9, 11))
    # Derek tries to mint an extra voice for his unenrolled cousin. There is no credential
    # to steal and no signature to forge: Ray's key is not in the ring, so no proof exists.
    try:
        cast("Cousin Ray", OPTIONS[1])
    except KeyError:
        rejected = {"attempt": "cast by unenrolled key", "member": "Cousin Ray",
                    "result": "rejected: not in the roster ring, so no membership proof exists"}

    # Published in tag order: a ballot's position in the box must say nothing either.
    box.sort(key=lambda b: b["nullifier"])
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

    # --- the anchor: the closing head, republished where neither the committee nor the
    # witnesses can reach it. Everything above survives signature collusion because it is
    # held up by proofs — but a proof can only convict what is PRESENT. A colluding
    # committee's last move is subtraction: erase a ballot, re-sign the shortened history,
    # retally honestly, and nothing inside the transcript objects. So the closing head
    # goes outside: the treasurer pays for three lines in the Sheffield Star's public
    # notices (the key here stands in for the printed page — in reality the receipt is
    # the archive itself; a chain as notary of last resort is the same move, see the
    # kernel's refusal 5). History can still be lied about; it can no longer quietly shorten.
    head = log.heads[-1]
    receipt = {"log_id": COMMUNITY, "size": head["size"], "root": head["root"],
               "published": "Sheffield Star public notices, 2026-07-23 print edition (simulated)"}
    receipt["sig"] = sign_over(keypair("anchor"), ACTORS["anchor"][0], receipt)
    (out / "anchor.json").write_text(json.dumps({"receipts": [receipt]}, indent=1) + "\n")

    # --- trust anchors: what a verifier must already trust (in reality: DID resolution +
    # the witness ecosystem). `witnesses` is the bar the transcript cannot lower: the
    # manifest is signed by the log key, so it cannot vouch for its own witness count.
    # No trustee keys here — trustee shares are proven by Chaum-Pedersen against the
    # Feldman commitments, which ride the witnessed log; and the election key cannot be
    # swapped either, because every ballot's validity proof binds to it under a ring
    # signature only a plot-holder can make. No voter keys either, and that is the point:
    # a verifier trusts the ring, never a name.
    keys = {ACTORS[a][0]: pub_b64(keypair(a)) for a in ACTORS}
    keys[COMMUNITY + "#manifest-1"] = pub_b64(keypair("log"))
    (out / "trust.json").write_text(json.dumps(
        {"keys": keys, "witnesses": manifest["transparency_log"]["witnesses"],
         "anchors": ["did:web:sheffield-star.example"]}, indent=1) + "\n")

    counts = body["counts"]
    print(f"run complete -> {out}")
    print("  randomness: " + ("the OS (--real) — secrets are real, the run is not reproducible"
                              if REAL else "the public demo seed — reproducible, zero privacy"))
    print(f"  {len(MEMBERS)} enrolled, {len(box)} anonymous ballots ({body['distinct_voters']} counted, "
          f"{body['superseded']} superseded), 1 unenrolled cast rejected")
    print(f"  each ballot proves membership of the {len(ring)}-key ring; nothing says which key")
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


def rewrite_box(dst: Path, mutate, collude=False, retally=True):
    """Apply `mutate` to the ballot box. If the committee colludes, it repairs the box
    digest in the log and the witnesses co-sign the rewritten history — every hash and
    signature then agrees, and only the voter-level proofs can object. `retally` re-runs
    the threshold decryption honestly over the poisoned box; set it False when the poison
    makes the sum undecryptable (a griefed tally cannot be re-announced), leaving the stale
    tally to be gated away once a ballot is convicted."""
    doc = json.loads((dst / "ballot-box.json").read_text())
    mutate(doc["ballots"])
    (dst / "ballot-box.json").write_text(json.dumps(doc, indent=1) + "\n")
    if collude:
        digest = sha256_hex(canon(doc))
        entries = load_entries(dst)
        entry(entries, "decision.closed")["body"]["ballot_box_digest"] = digest
        entry(entries, "decision.closed")["body"]["ballots_recorded"] = len(doc["ballots"])
        if retally:
            old = entry(entries, "decision.tally-proof")["body"]
            entry(entries, "decision.tally-proof")["body"] = tally_body(
                doc["ballots"], digest, [1, 3], old["note"])
        reforge(dst, entries, with_witnesses=True)


def ring_of(dst: Path) -> tuple[list, dict, str]:
    members = json.loads((dst / "roster.json").read_text())["members"]
    ring = [int(c["voter_pub"], 16) for c in members]
    return ring, {y: i for i, y in enumerate(ring)}, sha256_hex(canon([c["voter_pub"] for c in members]))


def resign_ballot(dst: Path, b: dict, name: str, label: str):
    """A saboteur re-proves his OWN altered ballot. He can: it is his ring secret. What he
    cannot do is make the altered ciphertext legal — that is a different check's job."""
    ring, index, rd = ring_of(dst)
    x = nym_secret(name)
    b.pop("ring_sig", None)
    b["ring_sig"], _ = ring_sign(ring, index[pow(G, x, P)], x, DECISION,
                                 sha256_hex(canon(b)), rd, label)


def find_by_tag(ballots: list, name: str) -> dict:
    tag = hx(link_tag(nym_secret(name), DECISION))
    return next(b for b in ballots if b["nullifier"] == tag)


def forge_cds_outside(c1: int, c2_bad: int, h: int, m: int, r: int, ctx: str, label: str) -> dict:
    """A CDS 0-or-1 proof for a ciphertext whose c2 is OUTSIDE the prime-order subgroup.
    prove01 for an honest c2 works because c2 = g^m·h^r; here c2 has been negated, so the
    real branch's h-equation picks up a factor (-1)^challenge that the honest prover never
    sees. But p is a safe prime — (-1)^even = 1 — so grind the nonce until the real-branch
    challenge is even and the factor vanishes. The proof then verifies over a ciphertext
    that is not a well-formed group element at all: precisely what the per-ballot subgroup
    check, and nothing else, refuses to wave through."""
    f = 1 - m
    cf, zf = rand_scalar(label + "|cf"), rand_scalar(label + "|zf")
    uf = c2_bad * pow(pow(G, f, P), -1, P) % P
    af = pow(G, zf, P) * pow(c1, -cf, P) % P
    bf = pow(h, zf, P) * pow(uf, -cf, P) % P
    for i in range(200):
        w = rand_scalar(f"{label}|w|{i}")
        a = {m: (pow(G, w, P), pow(h, w, P)), f: (af, bf)}
        stmt = {"t": "cds01", "ctx": ctx, "h": hx(h), "c1": hx(c1), "c2": hx(c2_bad),
                "a0": hx(a[0][0]), "b0": hx(a[0][1]), "a1": hx(a[1][0]), "b1": hx(a[1][1])}
        ct_ = (fs_challenge(stmt) - cf) % Q
        if ct_ % 2 == 0:                                 # (-1)^ct_ == 1: the real branch closes
            zt = (w + ct_ * r) % Q
            cc, zz = {m: ct_, f: cf}, {m: (w + ct_ * r) % Q, f: zf}
            return {"a0": stmt["a0"], "b0": stmt["b0"], "a1": stmt["a1"], "b1": stmt["b1"],
                    "c0": hx(cc[0]), "c1": hx(cc[1]), "z0": hx(zz[0]), "z1": hx(zz[1])}
    raise ValueError("no even challenge found in 200 grinds")


def require_demo_keys(src: Path, who: str):
    # Both collect and every tamper act AS a key-holder — the committee or an insider.
    # Those keys are re-derived from the demo seed, so on a --real transcript there is
    # no one here to play: refuse rather than mis-simulate.
    trust = json.loads((src / "trust.json").read_text())
    if trust["keys"][ACTORS["log"][0]] != pub_b64(keypair("log")):
        sys.exit(f"{src}: not a demo-seed transcript (--real?). {who} holds the demo "
                 "keys, and this transcript's keys are not derivable.")


def reanchor(dst: Path):
    """Republish the closing head after a legitimate re-run of the close: the anchor
    receipt must cover the WHOLE final log, so anything that grows or re-signs history
    ends by re-anchoring — the committee's last act, same as in run()."""
    heads = [json.loads(l) for l in (dst / "heads.jsonl").read_text().splitlines()]
    head = heads[-1]
    receipt = {"log_id": COMMUNITY, "size": head["size"], "root": head["root"],
               "published": "Sheffield Star public notices, reprinted after collection "
                            "closed (simulated)"}
    receipt["sig"] = sign_over(keypair("anchor"), ACTORS["anchor"][0], receipt)
    (dst / "anchor.json").write_text(json.dumps({"receipts": [receipt]}, indent=1) + "\n")


def collect(src: Path, dst: Path, ballot_paths: list[Path]):
    """The committee's side of an externally cast ballot (cast.html, or any tool that
    emits the ballot format): add it to the box and legitimately re-run everything the
    box feeds — digest, tally, heads, anchor. This is the same machinery the colluding
    tampers reuse, pointed at its honest purpose: even the committee cannot skip the
    proofs, so a bad external ballot is not caught here — it is caught by verify.py,
    which is the judge. Run it on <dst> afterwards."""
    require_demo_keys(src, "collection re-runs the close, so the committee")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    incoming = [json.loads(p.read_text()) for p in ballot_paths]

    def add(ballots):
        have = {(b["nullifier"], b["seq"]) for b in ballots}
        for b in incoming:
            if b.get("decision_id") != DECISION:
                sys.exit(f"ballot is for decision {b.get('decision_id')!r}, not {DECISION!r}")
            if (b["nullifier"], b["seq"]) in have:
                sys.exit(f"a ballot with tag {b['nullifier'][:16]}… and seq {b['seq']} is "
                         "already in the box — a re-cast needs a higher attempt number")
            ballots.append(b)
        ballots.sort(key=lambda b: b["nullifier"])  # position must say nothing, as in run()
    rewrite_box(dst, add, collude=True)
    reanchor(dst)
    print(f"collected {len(incoming)} ballot(s) -> {dst}")
    print("  the box, tally, heads and anchor were re-run; verify.py is the judge:")
    print(f"  python3 {Path(__file__).parent / 'verify.py'} {dst}")


def tamper(src: Path, dst: Path, mode: str):
    require_demo_keys(src, "the tampers simulate insiders, so each")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
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
    elif mode == "roster":
        # The committee rewrites the eligibility RULE in the published register after the
        # fact — "one vote per plot", so a member holding two plots may vote twice. Every
        # credential still verifies, the ring is untouched, and every ballot still proves
        # membership. What pins the register as it stood when the decision opened is the
        # digest the witnessed log recorded. Until this tamper existed nothing exercised
        # that check, so nothing proved it was load-bearing.
        doc = json.loads((dst / "roster.json").read_text())
        doc["eligibility"] = "plot-register/2026: one vote per plot"
        (dst / "roster.json").write_text(json.dumps(doc, indent=1) + "\n")
    elif mode == "box":
        # Total collusion re-aims a sealed ballot — Sandra's own, which takes her 8-6 win to
        # a 7-7 tie. The committee replaces her ciphertext with its own encryption of Keith
        # and, since it chose the randomness, a perfectly valid fresh 0-or-1 proof to match;
        # repairs the box digest; re-decrypts the sum honestly; and both witnesses co-sign.
        # Nothing about the ballot is malformed any more. It is simply not the ballot its
        # author signed — and its author is one of sixty people the committee cannot
        # identify, never mind impersonate. (Here it can: it holds the seed. A real one
        # could not even find her ballot in the box.)
        def swap(ballots):
            b = find_by_tag(ballots, "Sandra Okafor")
            r = rand_scalar("tamper-box")
            b["ciphertext"] = enc(0, r, election_pub())
            b["proof"] = prove01(0, r, b["ciphertext"], election_pub(), DECISION, "cds|tamper-box")
        rewrite_box(dst, swap, collude=True)
    elif mode == "stuff":
        # Total collusion mints a vote. The committee builds a flawless extra ballot for
        # Keith — a real encryption of 0, a real 0-or-1 proof, a well-formed linking tag
        # nobody has used — repairs the box digest, re-decrypts the sum honestly, and both
        # witnesses co-sign the rewritten history. Everything a signature or a hash could
        # certify, they certified. The one artifact they cannot produce is a proof of
        # membership in a ring they hold no key to. Eligibility is proven here, not
        # asserted, so there is no credential left to steal: they copy a real ballot's ring
        # signature, and it is bound to that ballot's contents and that voter's tag.
        def stuff(ballots):
            r = rand_scalar("tamper-stuff")
            ct = enc(0, r, election_pub())
            ballots.append({
                "decision_id": DECISION, "seq": 999,
                "nullifier": hx(link_tag(rand_scalar("tamper-stuff-nym"), DECISION)),
                "ciphertext": ct,
                "proof": prove01(0, r, ct, election_pub(), DECISION, "cds|stuffed"),
                "ring_sig": ballots[0]["ring_sig"]})
        rewrite_box(dst, stuff, collude=True)
    elif mode == "doublevote":
        # The attack unlinkability invites, and the reason the nullifier's subgroup check is
        # not decoration. Derek cannot derive two tags from one secret: the ring signature
        # binds the tag to the key. But p is a safe prime, so -1 is a non-residue — the
        # NEGATED tag -T lies outside the prime-order subgroup, and the signature still
        # closes whenever the challenge at Derek's own ring index comes out even. He grinds
        # his nonce until it does (two tries, on average), and his second ballot — same
        # secret, same ring, a tag that links to nothing — reads as a different voter. The
        # corrupt committee counts both. Only `nullifier in the subgroup` says otherwise.
        def doublevote(ballots):
            ring, index, rd = ring_of(dst)
            x = nym_secret("Derek Wainwright")
            pi = index[pow(G, x, P)]
            r = rand_scalar("tamper-doublevote")
            ct = enc(0, r, election_pub())          # a second voice, for Keith
            b = {"decision_id": DECISION, "seq": 998,
                 "nullifier": hx(P - link_tag(x, DECISION)),   # his own tag, negated
                 "ciphertext": ct,
                 "proof": prove01(0, r, ct, election_pub(), DECISION, "cds|doublevote")}
            for grind in range(64):
                sig, c_pi = ring_sign(ring, pi, x, DECISION, sha256_hex(canon(b)), rd,
                                      f"doublevote|{grind}", tag=int(b["nullifier"], 16))
                if c_pi % 2 == 0:                   # (-1)^c_pi == 1, so the ring closes
                    b["ring_sig"] = sig
                    ballots.append(b)
                    return
            raise ValueError("no even challenge found in 64 grinds")
        rewrite_box(dst, doublevote, collude=True)
    elif mode == "smuggle":
        # The proof that the ciphertext subgroup check is load-bearing on its OWN, not as a
        # spare for the CDS proof beside it. A saboteur (Derek) smuggles a malformed group
        # element into the box: c2 negated to -c2, which lies outside the prime-order
        # subgroup, wrapped in a FRESH 0-or-1 proof forged through the even-challenge grind
        # above — so the CDS check accepts it — and a valid ring signature over his own key.
        # He gives it a low seq under his real ballot, so it is superseded and never counted:
        # the tally decrypts honestly, the announced result is exactly right, and only the
        # box itself now contains an element that is not a group element. The committee and
        # witnesses collude to log it consistently. Every other check passes. Turn off the
        # subgroup line and the verifier CERTIFIES a transcript carrying malformed
        # ciphertext — the small-subgroup foothold this check exists to deny.
        def smuggle(ballots):
            x = nym_secret("Derek Wainwright")
            ring, index, rd = ring_of(dst)
            r = rand_scalar("tamper-smuggle")
            ct = enc(0, r, election_pub())
            c1, c2_bad = int(ct["c1"], 16), P - int(ct["c2"], 16)   # -c2: out of the subgroup
            b = {"decision_id": DECISION, "seq": 0,                 # below his real ballot -> superseded
                 "nullifier": hx(link_tag(x, DECISION)),
                 "ciphertext": {"c1": ct["c1"], "c2": hx(c2_bad)},
                 "proof": forge_cds_outside(c1, c2_bad, election_pub(), 0, r, DECISION, "smuggle")}
            b["ring_sig"], _ = ring_sign(ring, index[pow(G, x, P)], x, DECISION,
                                         sha256_hex(canon(b)), rd, "tamper|smuggle")
            ballots.append(b)
        rewrite_box(dst, smuggle, collude=True)
    elif mode == "overvote":
        # An enrolled voter (Derek again) encrypts m=2 — two votes for Sandra in one
        # ballot — proves membership validly, and the corrupt committee ACCEPTS it: box
        # digest repaired, sum re-decrypted honestly, witnesses co-sign the history. Every
        # hash, signature and trustee proof in the transcript now agrees. The only thing
        # that cannot be manufactured is the 0-or-1 proof for a ballot that encrypts 2.
        def overvote(ballots):
            b = find_by_tag(ballots, "Derek Wainwright")
            b["ciphertext"] = enc(2, rand_scalar("tamper-overvote"), election_pub())
            resign_ballot(dst, b, "Derek Wainwright", "tamper|overvote")  # old CDS proof binds the old ciphertext
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
    elif mode == "drop":
        # The end of the escalation, and the one tamper that forges NOTHING. The committee
        # and both witnesses erase Plot-holder 23's kiosk recast — the ballot that repaired
        # her compromised phone's lie — repair the box digest, re-decrypt the shortened sum
        # honestly, and re-sign history end to end. Her phone's sealed vote for Keith
        # quietly becomes her vote, and Sandra's 8-6 win a 7-7 tie. Every hash, signature
        # and proof now agrees, because every artifact is genuine: this is the true record
        # of an election minus one inconvenient ballot. Deniability, not forgery. The only
        # artifact that still objects is the one the collusion cannot reprint: the closing
        # log head, anchored outside it.
        def drop(ballots):
            tag = hx(link_tag(nym_secret("Plot-holder 23"), DECISION))
            kiosk = max((b for b in ballots if b["nullifier"] == tag), key=lambda b: b["seq"])
            ballots.remove(kiosk)
        rewrite_box(dst, drop, collude=True)
    else:
        sys.exit(f"unknown tamper mode: {mode}")
    print(f"tampered ({mode}) -> {dst}")


if __name__ == "__main__":
    args = sys.argv[1:]
    REAL = "--real" in args
    args = [a for a in args if a != "--real"]
    if args[:1] == ["run"]:
        run(Path(args[1]) if len(args) > 1 else Path(__file__).parent / "out")
    elif args[:1] == ["collect"] and len(args) >= 4:
        collect(Path(args[1]), Path(args[2]), [Path(a) for a in args[3:]])
    elif args[:1] == ["tamper"] and len(args) == 4:
        tamper(Path(args[1]), Path(args[2]), args[3])
    else:
        sys.exit(__doc__)
