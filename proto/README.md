# proto/ — the four verbs, running

The smallest real run of the kernel loop: the Heeley Bank allotment election
(the [`club-agm`](../scenarios/club-agm.json) scenario, §15's "wedge two") executed
end to end with real cryptography, emitting a transcript that an independent
verifier — sharing no code with the runner — confirms from the artifacts alone.

```sh
./test.sh          # the success test: run, verify, reproduce, catch 11 tampers
python3 clubvote.py run      # -> out/ (committed as the reference transcript)
python3 verify.py out        # independent verification, exit 0 = verified
```

Needs `cryptography` and `jsonschema` (`pip install -r ../requirements.txt`). The ballot
group is RFC 3526 MODP-2048 over stdlib `pow` — auditable over compact; a production
system would use an elliptic-curve group for kilobyte ballots.

## The four verbs

| verb | where |
|---|---|
| **prove** | the issuer certifies each plot-holder's nym key `g^x` into a published roster. A ballot then proves membership of that **ring** with a linkable ring signature (LSAG), and carries the per-decision pseudonym `nullifier = H(decision_id)^x` — §3.1's `nym_secret × context_id`, in the exponent. Which of the sixty keys signed, nothing says |
| **cast / challenge** | the device encrypts the choice to a 2-of-3 trustee key (exponential ElGamal) and attaches a 0-or-1 validity proof (CDS); the voter may challenge it to open the encryption before casting (Benaloh — a cheating device cannot tell which is coming; a challenged ciphertext is a receipt by construction, so it is spoiled, never cast); sealed ciphertexts enter the box and are never individually opened; any later ballot with the same nullifier silently supersedes |
| **verify** | `verify.py`: schemas, signatures, witnessed Merkle heads, digests, credentials, audits, per-ballot ring-membership and validity proofs, and the tally — recompute the homomorphic sum, check each trustee share's Chaum-Pedersen proof, combine, brute-force the small exponent, compare with the announcement |
| **read** | `out/log.jsonl` — seven kernel events, each validating against the waist |

## What makes it this project's prototype

1. **The waist is executable.** Every log entry validates against
   [`schema/log-entry.schema.json`](../schema/log-entry.schema.json) and the manifest
   against [`schema/manifest.schema.json`](../schema/manifest.schema.json) — the same
   schemas the fiction validates against. Spec and code meet at the same two formats.
2. **The manifest declares the subtractions.** The prototype is honestly weak, and says
   so machine-readably: `sybil_resistance: weak`, `rights_guard: false`,
   `coercion_resistance: revote-silent`, `paper_channel: false`.
   The first implementation is a lattice point, subject to its own anti-dilution rule —
   and the climb is legible, one manifest field at a time, each flip backed by a working
   mechanism: v1 implemented the Benaloh challenge (`cast_or_audit: false → true`); v2
   sealed the ballots behind a 2-of-3 trustee key and a homomorphic tally
   (`receipt_free: false → true`, `trustee_quorum` declared), which also removed v1's
   reveal-dependence — there is no reveal step for a device to fail at; v3 deleted v2's
   dealer — the trustees generate the key distributively, so the caveat "someone knew
   the joint secret" is not declared any more, it is gone; v4 made the voters anonymous
   (`unlinkable: false → true`) — the ballot proves eligibility instead of asserting it,
   and **one proof retired two identity checks**: where a ballot used to carry a voter's
   public key, the issuer's credential on it, and that voter's signature over it, it now
   carries a ring signature and a linking tag, and nobody — the issuer included — can say
   who cast it.
3. **Every tamper is caught by the defence the design names for it** — and the test
   asserts *which* check fired, because a tamper caught by the wrong check is a test that
   passes for the wrong reason and would stay green if the named defence rotted. Each
   verifier check earns its place by having a tamper that exercises it; each new check
   was mutation-tested (disable it, and its tamper is certified or loses its named
   defence). The first four are one insider escalating; the rest are worse — the
   committee **and both witnesses** colluding on a rewritten history, every hash and
   signature agreeing, so that only mathematics is left standing:

   | tamper | who does what | what catches it |
   |---|---|---|
   | `log` | insider edits an entry, re-signs it with the log key | Merkle consistency — the published heads no longer root the log (**no witness required**) |
   | `rehead` | edits it *and* regenerates every head to match | the missing witness co-signatures — they hold the log key, not the federation's |
   | `unwitness` | *and* rewrites the manifest to say it never had witnesses | the verifier's trust anchors — the manifest is log-key-signed, so it cannot be its own standard |
   | `roster` | rewrites the *eligibility rule* in the published register after the vote | the logged, witnessed roster digest — every credential still verifies, and it is still a lie |
   | `box` | re-aims Sandra's own sealed ballot at Keith — fresh valid 0-or-1 proof to match, digests repaired, witnesses co-sign — taking her 8–6 win to a 7–7 tie | the ring signature, which covers the ballot — they can re-encrypt and re-prove, but not re-prove *membership* |
   | `stuff` | mints an extra ballot for Keith: real ciphertext, real 0-or-1 proof, fresh tag, digests repaired, witnesses co-sign | the same ring signature — there is no credential left to steal, and they cannot prove membership of a ring they hold no key to |
   | `doublevote` | an enrolled voter **negates his own linking tag** and grinds his nonce until the ring closes: one secret, two tags, two votes | the nullifier's subgroup membership — the single check unlinkability makes load-bearing |
   | `negate` | a saboteur voter warps his own *ciphertext* out of the group, poisoning the sum | subgroup membership, per ballot — which *attributes* the sabotage instead of leaving an unexplainable dead tally |
   | `overvote` | an enrolled voter encrypts **2**; the corrupt committee counts it; witnesses co-sign | the 0-or-1 validity proof he cannot forge — it convicts his ballot, and the tally built on it falls with it |
   | `share` | committee + witnesses announce a rigged decryption, arithmetically consistent | the Chaum-Pedersen proof on each trustee share — the rigged share needs a secret nobody colluding holds |
   | `count` | same collusion, honest shares, lying counts | the recount — combine the proven shares, take the small exponent, and the announcement refutes itself |

   `rehead` is the one the records-rewrite scenario is actually about. `share` and `count`
   are the trustee layer's independence result: **the tally survives everyone who signs
   things.** A rigged tally is caught by proof verification even when the log key and
   every witness co-sign the lie — and the election key itself cannot be swapped by that
   collusion, because every ballot's validity proof binds to it under a ring signature
   only a plot-holder can make. What total collusion *can* still do is drop ballots from
   history (deniability, not forgery); the design's answer there is the external anchor,
   not implemented here.

   `stuff` and `box` are two attacks answered by one check, and that is the point of the
   anonymity rung rather than a gap in it: eligibility used to be *asserted* by a
   credential the box carried, and is now *proven* by a signature only a ring member can
   produce. There is nothing left to steal. `doublevote` is the check the rung had to
   add, and it is not decoration: `p` is a safe prime, so `-1` is a quadratic non-residue
   and the negated tag `-T` lies outside the prime-order subgroup. The ring signature
   still closes on it whenever the challenge at the signer's own index happens to be even
   — two grinds, on average. Exactly two tags exist per secret (`±T`), and the subgroup
   check deletes the second.

   Both new checks were mutation-tested, and both are load-bearing — disable one, and a
   verifier that reports `VERIFIED` on a rigged election:

   | mutation | tamper | result |
   |---|---|---|
   | ring-signature verification always returns true | `box` | **certifies** — Sandra's 8–6 win recorded as a 7–7 tie |
   | ring-signature verification always returns true | `stuff` | **certifies** — "15 voted", one of them nobody |
   | ring-signature verification always returns true | `doublevote` | still caught, by the nullifier check: the two are independent |
   | nullifier subgroup check removed | `doublevote` | **certifies** — "15 voted", and one of them is Derek twice |
   | logged-roster-digest check removed | `roster` | **certifies** — the eligibility rule rewritten after the vote |

   The `box` row is why the tamper had to be sharpened: an earlier version swapped a
   ciphertext without re-proving it, and the 0-or-1 proof caught it even with the ring
   signature disabled. It looked like a passing test for the ring signature and was not
   one. A tamper the *wrong* check can also catch does not prove the right check.

   And in the reference transcript itself, a compromised device that displayed Sandra
   while encrypting Keith is caught by a challenge, logged (`x-ballot.audit-failed`),
   and repaired by a silent recast — the two remedies composing. **It decided the
   election**: Sandra wins 8–6, and the unrepaired phone ballot would have made it 7–7.
   What that phone actually encrypted stays sealed forever.

## What v4 deliberately is not (the manifest is the source of truth)

- **`unlinkable: true` means the anonymity set is the roster, and the cost is linear in
  it.** A ballot is indistinguishable among the sixty enrolled keys — not among a
  million. Measured on this run (60-key ring, 16 ballots): the ring signature is
  **8.4 kB** of a **13.4 kB** ballot and takes **~0.7 s** to verify; a whole-transcript
  verification is **14 s**. `test.sh` verifies the transcript a dozen times over, but the
  checks are independent, so it fans them across cores and gates the O(roster) ballot pass
  behind the cheap ones that commit to it — **~45 s** on a four-core runner (a tamper
  caught in the log never reaches the ring). That is kilobytes and seconds at village
  scale, which is the only scale this prototype claims — and §4's kilobyte-payload
  requirement (T14) survives *here*, at sixty. It does not survive a national roster, and
  no amount of engineering turns an O(n) proof into an O(1) one. This is precisely why §13
  tracks the BBS per-verifier-linkability drafts as the pre-final answer: they give the
  same `prove(eligible, decision_id) → pseudonym + proof` interface with a constant-size
  presentation. **The kernel commits to the abstraction, not to the ring.** A ring
  signature is one lattice point beneath it; BBS is another. Swapping them changes no
  other line of the protocol — which is the claim §13 makes, and this rung is the first
  evidence for it.
- **Unlinkable, not anonymous against the seed.** Every secret in this transcript,
  including each voter's `nym_secret`, derives from a public constant so the run is
  byte-reproducible. Anyone can therefore recompute every tag and de-anonymize *this
  particular* transcript. That is the same declared subtraction that makes `receipt_free`
  reproducible: the mechanism is real, this run's privacy is not, by design. A deployment
  generates `x` on the voter's device, and then the issuer — who certified `g^x` and
  never saw `x` — cannot link a ballot to a member either.
- **What the box still shows.** How many distinct voters, how many re-voted and how many
  times (tags are equal or they are not), and that one device cheated. Not who. Cast
  order carries no identity: the reference run casts in a shuffled order and publishes the
  box sorted by tag, because `seq` decides which of a voter's ballots counts and so must
  be inside the signed ballot.
- **The assisted channel is unmarked, and that is the guarantee.** Ernest votes at the
  table with two tellers; his ballot carries no `channel` field and no teller's
  countersignature, because one `assisted` label in a ring of sixty names him. T9 promises
  he can vote and have it verified like anyone's — not that the record says he needed help.
- **Sybil resistance is unchanged and still `weak`.** The ring proves *a* plot-holder
  cast this ballot, exactly once. It cannot know whether two roster entries are one human.
  That was always the issuer's job, and unlinkability neither helps nor hurts it.
- **`receipt_free: true` holds at the transcript level, with a named behavioural edge.**
  The public artifacts never link any ballot to a choice — only the aggregate is
  decrypted, so nothing on the bulletin board can prove what you voted. But a client
  that *retains* its encryption randomness can reconstruct a receipt (the Helios
  caveat), so the protocol requires — and `clubvote.py` literally does — discarding `r`
  the moment a ballot is cast. Challenged ciphertexts, whose `r` is public by design,
  are spoiled and never cast. Receipt-freeness against a coercer who seizes the device
  *before* casting remains `coercion_resistance: revote-silent`, and breaks against
  live observation, as the harness has always said. Anonymity adds one thing here and
  only one: a coercer who does not hold your nym secret can no longer read the public
  box to check whether you abstained.
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
- All actors run in one process; key custody and the enrolment ceremony are simulated.
  Verification-from-artifacts is the property under test, not endpoint security. The
  tampers are handed a power no real attacker has — the seed, and so every voter's tag —
  precisely so they can aim at a named victim's ballot inside an anonymous box.
- `trust.json` stands in for DID resolution and the witness ecosystem: it is the
  verifier's explicit trust anchor set, naming both the keys it trusts and, in
  `witnesses`, which parties it *requires* to co-sign every log head. That list has to
  live outside the transcript. The manifest declares its own witnesses, but the manifest
  is signed by the log key — so an insider holding that key can lower their own bar to
  zero, and did, until `unwitness` was written to prove it. A manifest cannot be its own
  standard. Correspondingly, `verify.py` declines to certify a log whose trust anchors
  name no witness. It holds **no voter keys at all**, and that is the shape of the rung:
  a verifier trusts the ring, never a name. The trustees need no anchor either — their
  layer is held up by proofs, not signatures, which is why it survives the collusions
  that defeat the log.
- The ballot group is pinned **by name** to the verifier's own constants; a transcript
  that could supply its own group parameters could supply a smooth one. The verifier
  also subgroup-checks the roster's keys, which no tamper exercises (a rewritten roster
  fails its logged digest first) — declared here as input hygiene, not as a defence.
- Canonicalization approximates JCS (RFC 8785) as sorted compact JSON — exact for this
  artifact set (strings, integers, booleans only).
