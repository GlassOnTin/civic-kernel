# proto/ — the four verbs, running

The smallest real run of the kernel loop: the Heeley Bank allotment election
(the [`club-agm`](../scenarios/club-agm.json) scenario, §15's "wedge two") executed
end to end with real cryptography, emitting a transcript that an independent
verifier — sharing no code with the runner — confirms from the artifacts alone.

```sh
./test.sh          # the success test: run, verify, reproduce, catch 3 tampers
python3 clubvote.py run      # -> out/ (committed as the reference transcript)
python3 verify.py out        # independent verification, exit 0 = verified
```

Needs `cryptography` and `jsonschema` (`pip install -r ../requirements.txt`).

## The four verbs

| verb | where |
|---|---|
| **prove** | roster credential (issuer-signed voting key) + per-decision nullifier `sha256(voter_pub ‖ decision_id)` |
| **cast / challenge** | the device commits (`sha256(choice ‖ nonce)`); the voter may challenge it to open the commitment before casting (Benaloh — a cheating device cannot tell which is coming); a cast commitment enters the box, choices stay hidden until the close-time reveal; any later ballot with the same nullifier silently supersedes |
| **verify** | `verify.py`: schemas, signatures, witnessed Merkle heads, digests, credentials, audits, reveals, full recount |
| **read** | `out/log.jsonl` — six kernel events, each validating against the waist |

## What makes it this project's prototype

1. **The waist is executable.** Every log entry validates against
   [`schema/log-entry.schema.json`](../schema/log-entry.schema.json) and the manifest
   against [`schema/manifest.schema.json`](../schema/manifest.schema.json) — the same
   schemas the fiction validates against. Spec and code meet at the same two formats.
2. **The manifest declares the subtractions.** The prototype is honestly weak, and says
   so machine-readably: `receipt_free: false`, `unlinkable: false`,
   `sybil_resistance: weak`, `rights_guard: false`, `coercion_resistance: revote-silent`.
   The first implementation is a lattice point, subject to its own anti-dilution rule —
   and the climb is legible: v1 implemented the Benaloh challenge and flipped
   `cast_or_audit: false → true`, a one-field manifest diff backed by a working mechanism.
3. **The tampers fail where the design says they must.** An *insider* who rewrites
   history and re-signs it with the log key is caught by the witnessed head roots (the
   keys the insider does not hold); a flipped or stuffed ballot is caught by the box
   digest the log committed to; an unenrolled ballot has no issuer credential; a
   choice flipped at reveal time fails against its own cast commitment. And in the
   reference transcript itself, a compromised device that displayed Sandra while
   committing to Keith is caught by a challenge, logged (`x-ballot.audit-failed`), and
   repaired by a silent recast — the two remedies composing.

## What v0 deliberately is not (the manifest is the source of truth)

- Ballots are **commit-then-reveal pseudonymous**, verifiable by public recount: choices
  are hidden during the voting window but published at close — not receipt-free (a
  reveal links nullifier to choice), no homomorphic tally, no threshold trustees.
- **Reveal-dependence**: a device that never reveals leaves a visible invalid ballot —
  an availability cost the next rung (threshold encryption, no reveal step) removes.
- **Linkable**: the issuer can map nullifiers to the roster. Real unlinkability is the
  BBS-pseudonym work §13 tracks as pre-final.
- All actors run in one process; key custody and the enrolment ceremony are simulated.
  Verification-from-artifacts is the property under test, not endpoint security.
- Demo keys derive from a public seed so the transcript is byte-reproducible — zero
  privacy, by design. `trust.json` stands in for DID resolution and the witness
  ecosystem: it is the verifier's explicit trust anchor set.
- Canonicalization approximates JCS (RFC 8785) as sorted compact JSON — exact for this
  artifact set (strings, integers, booleans only).
- Total collusion (operator *and* both witnesses *and* the issuer) defeats v0, as §6
  predicts for any local-only witness set; the design's answer at that point is the
  external anchor, not implemented here.
