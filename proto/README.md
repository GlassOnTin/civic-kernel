# proto/ — the four verbs, running

The smallest real run of the kernel loop: the Heeley Bank allotment election
(the [`club-agm`](../scenarios/club-agm.json) scenario, §15's "wedge two") executed
end to end with real cryptography, emitting a transcript that an independent
verifier — sharing no code with the runner — confirms from the artifacts alone.

```sh
./test.sh          # the success test: run, verify, reproduce, catch 9 tampers
python3 clubvote.py run      # -> out/ (committed as the reference transcript)
python3 verify.py out        # independent verification, exit 0 = verified
```

Needs `cryptography` and `jsonschema` (`pip install -r ../requirements.txt`). The ballot
group is RFC 3526 MODP-2048 over stdlib `pow` — auditable over compact; a production
system would use an elliptic-curve group for kilobyte ballots.

## The four verbs

| verb | where |
|---|---|
| **prove** | roster credential (issuer-signed voting key) + per-decision nullifier `sha256(voter_pub ‖ decision_id)` |
| **cast / challenge** | the device encrypts the choice to a 2-of-3 trustee key (exponential ElGamal) and attaches a 0-or-1 validity proof (CDS); the voter may challenge it to open the encryption before casting (Benaloh — a cheating device cannot tell which is coming; a challenged ciphertext is a receipt by construction, so it is spoiled, never cast); sealed ciphertexts enter the box and are never individually opened; any later ballot with the same nullifier silently supersedes |
| **verify** | `verify.py`: schemas, signatures, witnessed Merkle heads, digests, credentials, audits, per-ballot validity proofs, and the tally — recompute the homomorphic sum, check each trustee share's Chaum-Pedersen proof, combine, brute-force the small exponent, compare with the announcement |
| **read** | `out/log.jsonl` — seven kernel events, each validating against the waist |

## What makes it this project's prototype

1. **The waist is executable.** Every log entry validates against
   [`schema/log-entry.schema.json`](../schema/log-entry.schema.json) and the manifest
   against [`schema/manifest.schema.json`](../schema/manifest.schema.json) — the same
   schemas the fiction validates against. Spec and code meet at the same two formats.
2. **The manifest declares the subtractions.** The prototype is honestly weak, and says
   so machine-readably: `unlinkable: false`, `sybil_resistance: weak`,
   `rights_guard: false`, `coercion_resistance: revote-silent`.
   The first implementation is a lattice point, subject to its own anti-dilution rule —
   and the climb is legible, one manifest field at a time, each flip backed by a working
   mechanism: v1 implemented the Benaloh challenge (`cast_or_audit: false → true`); v2
   sealed the ballots behind a 2-of-3 trustee key and a homomorphic tally
   (`receipt_free: false → true`, `trustee_quorum` declared), which also removed v1's
   reveal-dependence — there is no reveal step for a device to fail at; v3 deleted v2's
   dealer — the trustees generate the key distributively, so the caveat "someone knew
   the joint secret" is not declared any more, it is gone.
3. **Every tamper is caught by the defence the design names for it** — and the test
   asserts *which* check fired, because a tamper caught by the wrong check is a test that
   passes for the wrong reason and would stay green if the named defence rotted. Each
   verifier check earns its place by having a tamper that exercises it; each new check
   was mutation-tested (disable it, and its tamper is certified or loses its named
   defence). The first three are one insider escalating; the last three are worse — the
   committee **and both witnesses** colluding on a rewritten history, every hash and
   signature agreeing, so that only mathematics is left standing:

   | tamper | who does what | what catches it |
   |---|---|---|
   | `log` | insider edits an entry, re-signs it with the log key | Merkle consistency — the published heads no longer root the log (**no witness required**) |
   | `rehead` | edits it *and* regenerates every head to match | the missing witness co-signatures — they hold the log key, not the federation's |
   | `unwitness` | *and* rewrites the manifest to say it never had witnesses | the verifier's trust anchors — the manifest is log-key-signed, so it cannot be its own standard |
   | `box` | swaps a cast ciphertext | the voter's own signature, which covers it |
   | `forge` | stuffs a ballot from an unenrolled key | no issuer credential on the roster |
   | `negate` | a saboteur voter warps his own ciphertext out of the group, poisoning the sum | subgroup membership, per ballot — which *attributes* the sabotage instead of leaving an unexplainable dead tally |
   | `overvote` | an enrolled voter encrypts **2**; the corrupt committee counts it; witnesses co-sign | the 0-or-1 validity proof he cannot forge — it convicts his ballot, and the tally built on it falls with it |
   | `share` | committee + witnesses announce a rigged decryption, arithmetically consistent | the Chaum-Pedersen proof on each trustee share — the rigged share needs a secret nobody colluding holds |
   | `count` | same collusion, honest shares, lying counts | the recount — combine the proven shares, take the small exponent, and the announcement refutes itself |

   `rehead` is the one the records-rewrite scenario is actually about. The last two are
   the trustee layer's independence result: **the tally survives everyone who signs
   things.** A rigged tally is caught by proof verification even when the log key and
   every witness co-sign the lie — and the election key itself cannot be swapped by that
   collusion, because every voter's validity proof binds to it under a signature only
   that voter can make. What total collusion *can* still do is drop ballots from history
   (deniability, not forgery); the design's answer there is the external anchor, not
   implemented here.

   And in the reference transcript itself, a compromised device that displayed Sandra
   while encrypting Keith is caught by a challenge, logged (`x-ballot.audit-failed`),
   and repaired by a silent recast — the two remedies composing. What the compromised
   phone actually encrypted stays sealed forever.

## What v3 deliberately is not (the manifest is the source of truth)

- **`receipt_free: true` holds at the transcript level, with a named behavioural edge.**
  The public artifacts never link any ballot to a choice — only the aggregate is
  decrypted, so nothing on the bulletin board can prove what you voted. But a client
  that *retains* its encryption randomness can reconstruct a receipt (the Helios
  caveat), so the protocol requires — and `clubvote.py` literally does — discarding `r`
  the moment a ballot is cast. Challenged ciphertexts, whose `r` is public by design,
  are spoiled and never cast. Receipt-freeness against a coercer who seizes the device
  *before* casting remains `coercion_resistance: revote-silent`, and breaks against
  live observation, as the harness has always said.
- **The DKG has no hash-commitment round.** Each trustee deals their own
  Feldman-committed polynomial and no party ever holds the joint secret — but a
  trustee who waits to see the others' commitments before choosing their own could
  bias the key's *distribution* (the rushing attack, Gennaro et al. 2007). The fix is
  a commit-then-reveal round at the ceremony; a single transcript cannot evidence one
  (a full-collusion rewrite fakes it, and everything it protects is already held by
  voter binding and the share proofs), so per this project's own rule — no verifier
  check without a tamper that exercises it — it is declared rather than half-checked.
  A verifier is protected from a *mis-run* ceremony regardless: the election key and
  every trustee key are derived from the commitment products, never asserted.
- **Two options, one ciphertext.** `m ∈ {0,1}` with a disjunctive proof; `k` options
  generalise as a ciphertext vector with one 0-or-1 proof each plus a sum-to-1 proof.
- **Linkable**: the issuer can map nullifiers to the roster. Real unlinkability is the
  BBS-pseudonym work §13 tracks as pre-final.
- All actors run in one process; key custody and the enrolment ceremony are simulated.
  Verification-from-artifacts is the property under test, not endpoint security.
- Demo keys and all protocol randomness derive from a public seed so the transcript is
  byte-reproducible — zero privacy for *this* run, by design. `trust.json` stands in
  for DID resolution and the witness ecosystem: it is the verifier's explicit trust
  anchor set, naming both the keys it trusts and, in `witnesses`, which parties it
  *requires* to co-sign every log head. That list has to live outside the transcript.
  The manifest declares its own witnesses, but the manifest is signed by the log key —
  so an insider holding that key can lower their own bar to zero, and did, until
  `unwitness` was written to prove it. A manifest cannot be its own standard.
  Correspondingly, `verify.py` declines to certify a log whose trust anchors name no
  witness. The trustees need no such anchor: their layer is held up by proofs, not
  signatures — which is why it survives the collusions that defeat the log.
- The ballot group is pinned **by name** to the verifier's own constants; a transcript
  that could supply its own group parameters could supply a smooth one.
- Canonicalization approximates JCS (RFC 8785) as sorted compact JSON — exact for this
  artifact set (strings, integers, booleans only).
