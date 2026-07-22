# proto/ — the four verbs, running

One election, run end to end with real cryptography, then attacked twelve ways. This
is the smallest real run of the kernel loop: the Heeley Bank allotment election (the
[`club-agm`](../scenarios/club-agm.json) scenario, [§15](https://glassontin.github.io/civic-kernel/#s15 "Nobody installs an app out of civic virtue. Two things people already want: money they are owed and cannot find, and a club vote nobody can rig.")'s "wedge two"). It emits a
transcript, and an independent verifier — sharing no code with the runner — confirms
the election from those artifacts alone.

```sh
./test.sh          # the success test: run, verify, reproduce, verify a --real run, catch
                   # 12 tampers, browser verifier parity, casting-page parity, agm flow
./waist-boundary.sh   # the shadow of test.sh: the 4 narrative-record attacks (the
                      # "Yes Minister" moves) pass the ballot verifier, by design
python3 clubvote.py run      # -> out/ (committed as the reference transcript)
python3 verify.py out        # independent verification, exit 0 = verified
python3 clubvote.py run mydir --real   # same election, OS randomness: secrets are real,
                                       # the verifier is identical, tampering refuses
python3 clubvote.py collect out dst b.json   # committee side of an external ballot (e.g.
                                             # from ../cast.html): add to the box, re-run
                                             # tally/heads/anchor; verify.py is the judge
```

And a **real election the committee can run across days, with witnesses, trustees and
the anchor on their own machines** — persistent keys, OS randomness, an append-only
public transcript whose every checkpoint must come back co-signed, a tally no single
machine can compute, and a closing head lodged where the committee cannot reach it
(this is the shadow-AGM runbook):

```sh
# each witnessing society, on ITS OWN machine — or in its own BROWSER, no install:
# ../witness.html is the same witness (same file, card, co-signature, refusals;
# tools/witness-parity.mjs holds the two to each other across a whole election):
python3 clubvote.py witness new fed did:web:the-federation.example#w1   # -> fed/card.json
#   hand card.json to the committee; get the community id + log key back OUT OF BAND
#   (two secretaries at a federation meeting — that exchange is the ceremony):
python3 clubvote.py witness watch fed <community-id> <log-pub>

# each trustee, on ITS OWN machine (indices 1..3):
python3 clubvote.py trustee new t1 1        # deal your own polynomial -> t1/deal.json
#   (public: to the committee AND the other trustees) + t1/share-for-N.json (PRIVATE:
#   to trustee N only, directly — never via the committee); verify what the others send:
python3 clubvote.py trustee receive t1 t2-deal.json t2-share-for-1.json   # Feldman check

# the anchor — the newspaper's public notices as a tool, on ITS OWN machine:
python3 clubvote.py anchor new star did:web:the-star.example#notices-1   # -> star/card.json
python3 clubvote.py anchor watch star <community-id> <log-pub>

# the register — the plot book's pen, on ITS OWN machine:
python3 clubvote.py issuer new register did:web:myclub.example#roster-1  # -> register/card.json

# the committee — holding ONE key, the log's; it can certify nobody, tally nothing,
# anchor nothing, and cannot get a rewrite witnessed:
python3 clubvote.py agm new myclub fed-card.json meers-card.json star-card.json \
                                   register-card.json \
                                   t1-deal.json t2-deal.json t3-deal.json
#   Every step that grows the log ends "head awaits its witnesses": email
#   myclub/witness-request.json out; each witness runs
#       python3 clubvote.py witness sign fed witness-request.json   # -> fed/cosig-N.json
#   and the committee attaches the answers before history can advance:
python3 clubvote.py agm witness-import myclub cosig-*.json

python3 clubvote.py issuer certify register "A. Member" <voter_pub>  # the REGISTER signs
                                            # (pub from cast.html step 1; the member's
                                            # secret never leaves their device)
python3 clubvote.py agm enrol myclub register/cert-a-member.json     # the committee can
                                            # only verify and file it
python3 clubvote.py agm open myclub 2026-agm "Question?" "Yes" "No"  # pins the roster digest
# members cast at cast.html (point it at the published myclub/public/) and hand over files
python3 clubvote.py agm collect myclub ballot-*.json
python3 clubvote.py agm close myclub        # commits the digests; emits tally-request.json —
                                            # the committee CANNOT tally: it has no share
python3 clubvote.py trustee share t1 tally-request.json   # each trustee, on its machine:
                                            # recompute the sum FROM THE BOX, prove a share
python3 clubvote.py agm tally-import myclub t1-share-1.json t3-share-3.json  # 2-of-3 quorum
                                            # -> tally; then the witness round one last time
python3 clubvote.py anchor lodge star anchor-request.json  # the anchor lodges the witnessed
                                            # closing head — once per log, forever
python3 clubvote.py agm anchor-import myclub star/receipt-N.json  # the election is complete
python3 verify.py myclub/public             # anyone judges it from the published files alone
```

The committee never reforges history — `agm` only appends (rewriting is the tampers'
move, and `tamper`/demo-`collect` refuse an agm transcript outright: its keys are
nobody's to re-derive). The register alone can certify a member: `agm enrol` verifies a
credential against the register's card and files it, so a phantom member needs the
registrar's pen, not the log-keeper's. A witness co-signs only what its own memory
allows: it recomputes the head from the log it is sent, and refuses any history that
does not *extend* the one it last co-signed — a committee that rewrites the past cannot
get its checkpoint witnessed, which is what witnessing is for. A trustee decrypts only
a sum it recomputed itself from the box in the request — never a bare number, which
would make it a decryption oracle for any single ballot — and its cross-shares
travelled trustee-to-trustee, so no machine anywhere ever held the joint key. And the
anchor lodges a log's closing head at most once: asked later for a receipt over a
*different* closing head — the drop attack, politely — it refuses on the one thing it
remembers, which is what it already printed (`tools/agm-flow.mjs` proves all five
refusals: a phantom credential dies at enrol, a re-signed rewrite on the witness's
memory, a corrupted cross-share on the Feldman check, a bogus tally share on its own
Chaum-Pedersen proof, a rewritten close on the anchor's memory). The committee ends
holding one key — the log's: it publishes, gates and assembles, and vouches for nothing
by itself. The declared residue, on the cast page itself: whoever collects the ballot
files sees who handed over which.

The same checks run in any current browser: [`../verifier.html`](../verifier.html)
([live](https://glassontin.github.io/civic-kernel/verifier.html)) loads or accepts a dropped
transcript, shows every check as it runs, and lets a voter look up their own ballot by its
linking tag. `tools/verify-parity.mjs` (part of `test.sh`, and CI) holds its engine to
`verify.py`'s verdicts. On the reference transcript — and only there, because only the demo
publishes its trustees' joint secret — the page also takes a handed-in ballot and replays
`collect` in the browser: judged with the box's own checks, the re-vote rule applied, the
new total unsealed in front of the voter. `tools/collect-parity.mjs` (ditto) holds all four
outcomes — counted, superseded, duplicate, forged — to `collect` + `verify.py`'s; the page
refuses to count any transcript whose committed election key is not `g^(its pinned secret)`,
which is every real one.

The voter's side runs in the browser too: [`../cast.html`](../cast.html)
([live](https://glassontin.github.io/civic-kernel/cast.html)) generates an enrolment secret
on the device (the issuer certifies only the public key), seals a choice to the election
key, offers the Benaloh challenge before casting, and signs the ballot over the roster
ring — emitting a ballot file for the committee to `collect`. `tools/cast-parity.mjs`
(part of `test.sh`, and CI) asserts the whole loop: a ballot built by `cast.js`, collected
into the reference transcript, must be accepted by `verify.py` and must move the tally
(8–6 → 9–5: Derek's re-cast supersedes, nothing is stuffed). The collection channel is
deliberately dumb — hand over a file, email it — because verification is from artifacts;
the honest cost, declared on the page itself: whoever collects the files sees who sent
which sealed ballot, so shadow-mode unlinkability holds against the world but not against
the collector. A deployment uses an anonymous drop.

Needs `cryptography` and `jsonschema` (`pip install -r ../requirements.txt`). The ballot
group is RFC 3526 MODP-2048 over stdlib `pow` — auditable over compact; a production
system would use an elliptic-curve group for kilobyte ballots.

## The four verbs

<details>
<summary><b>Plainly</b> <i>The election as four moves: prove you are an enrolled member without saying which, seal your choice and prove it well-formed, verify the whole run from the files alone, read the record.</i></summary>

| verb | where |
|---|---|
| **prove** | the issuer certifies each plot-holder's nym key `g^x` into a published roster. A ballot then proves membership of that **ring** with a [linkable ring signature](../README.md#w-ring-signature) (LSAG), and carries the [per-decision pseudonym](../README.md#w-linking-tag) `nullifier = H(decision_id)^x` — [§3.1](https://glassontin.github.io/civic-kernel/#s3-1 "Prove you are on the list and have not already spoken — without saying which name on the list you are. No file on anyone is ever built.")'s `nym_secret × context_id`, in the exponent. Which of the sixty keys signed, nothing says |
| **cast / challenge** | the device encrypts the choice to a 2-of-3 trustee key (exponential ElGamal) and attaches a 0-or-1 validity proof (CDS); the voter may challenge it to open the encryption before casting ([Benaloh](../README.md#w-cast-or-audit) — a cheating device cannot tell which is coming; a challenged ciphertext is a receipt by construction, so it is spoiled, never cast); sealed ciphertexts enter the box and are never individually opened; any later ballot with the same nullifier silently supersedes |
| **verify** | `verify.py`: schemas, signatures, [witnessed](../README.md#w-witness) Merkle heads, digests, credentials, audits, per-ballot ring-membership and validity proofs, the tally — recompute the [homomorphic sum](../README.md#w-homomorphic-tally), check each trustee share's Chaum-Pedersen proof, combine, brute-force the small exponent, compare with the announcement — and last, the [anchor](../README.md#w-anchor): the closing head must match a receipt from outside the collusion set |
| **read** | `out/log.jsonl` — seven kernel events, each validating against the [waist](../README.md#w-waist) |

</details>

## What makes it this project's prototype

<details>
<summary><b>Plainly</b> <i>Three claims made good: the spec's two formats are what the code actually emits, every weakness is declared in the manifest — and each of the twelve frauds is caught by the exact check the design names for it, proven by switching that check off.</i></summary>

1. **The [waist](../README.md#w-waist) is executable.** Every log entry validates against
   [`schema/log-entry.schema.json`](../schema/log-entry.schema.json) and the manifest
   against [`schema/manifest.schema.json`](../schema/manifest.schema.json) — the same
   schemas the fiction validates against. Spec and code meet at the same two formats.
2. **The [manifest](../README.md#w-manifest) declares the [subtractions](../README.md#w-subtraction).** The prototype is honestly weak, and says
   so machine-readably: `sybil_resistance: weak`, `rights_guard: false`,
   `coercion_resistance: revote-silent`, `paper_channel: false`.
   The first implementation is a [lattice](../README.md#w-lattice) point, subject to its own anti-dilution rule —
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
   who cast it; v5 anchored the closing head outside the collusion set — the last thing
   total signature collusion could still do was *erase* history, and now the world holds
   a copy. No manifest field flips for v5, and that is its lesson: the manifest is signed
   by the log key, so it could never carry this bar — the requirement lives in the
   verifier's trust anchors (`trust.json` names who must hold a receipt), where
   `unwitness` taught such bars to live.
3. **Every tamper is caught by the defence the design names for it** — and the test
   asserts *which* check fired, because a tamper caught by the wrong check is a test that
   passes for the wrong reason and would stay green if the named defence rotted. Each
   verifier check earns its place by having a tamper that exercises it; each new check
   was mutation-tested (disable it, and its tamper is certified or loses its named
   defence). The first four are one insider escalating; the rest are worse — the
   committee **and both witnesses** colluding on a rewritten history, every hash and
   signature agreeing, so that only mathematics is left standing. The last is worst of
   all, because even mathematics has nothing to convict: nothing is forged, the lie is
   pure omission, and only the world's copy of the closing head objects:

   | tamper | who does what | what catches it |
   |---|---|---|
   | `log` | insider edits an entry, re-signs it with the log key | Merkle consistency — the published heads no longer root the log (**no witness required**) |
   | `rehead` | edits it *and* regenerates every head to match | the missing witness co-signatures — they hold the log key, not the federation's |
   | `unwitness` | *and* rewrites the manifest to say it never had witnesses | the verifier's trust anchors — the manifest is log-key-signed, so it cannot be its own standard |
   | `roster` | rewrites the *eligibility rule* in the published register after the vote | the logged, witnessed roster digest — every credential still verifies, and it is still a lie |
   | `box` | re-aims Sandra's own sealed ballot at Keith — fresh valid 0-or-1 proof to match, digests repaired, witnesses co-sign — taking her 8–6 win to a 7–7 tie | the ring signature, which covers the ballot — they can re-encrypt and re-prove, but not re-prove *membership* |
   | `stuff` | mints an extra ballot for Keith: real ciphertext, real 0-or-1 proof, fresh tag, digests repaired, witnesses co-sign | the same ring signature — there is no credential left to steal, and they cannot prove membership of a ring they hold no key to |
   | `doublevote` | an enrolled voter **negates his own linking tag** and grinds his nonce until the ring closes: one secret, two tags, two votes | the *nullifier's* subgroup membership — negated, the tag `-T` leaves the subgroup |
   | `smuggle` | slips a malformed ciphertext (c2 negated, **out of the subgroup**) into the box behind a forged-but-valid 0-or-1 proof and a real ring signature, riding in as a superseded ballot | the *ciphertext's* subgroup membership, per ballot — the only check that examines the group, and nothing else catches it |
   | `overvote` | an enrolled voter encrypts **2**; the corrupt committee counts it; witnesses co-sign | the 0-or-1 validity proof he cannot forge — it convicts his ballot, and the tally built on it falls with it |
   | `share` | committee + witnesses announce a rigged decryption, arithmetically consistent | the Chaum-Pedersen proof on each trustee share — the rigged share needs a secret nobody colluding holds |
   | `count` | same collusion, honest shares, lying counts | the recount — combine the proven shares, take the small exponent, and the announcement refutes itself |
   | `drop` | same collusion **erases the kiosk recast** — the ballot that repaired the compromised phone — re-signs history end to end and retallies honestly: every artifact genuine, Sandra's 8–6 win now a 7–7 tie, nothing forged | the **anchored closing head** — the receipt in `anchor.json`, from a party `trust.json` requires and the collusion does not include, matches the history the world saw and not this one |

   `rehead` is the one the records-rewrite scenario is actually about. `share` and `count`
   are the trustee layer's independence result: **the tally survives everyone who signs
   things.** A rigged tally is caught by proof verification even when the log key and
   every witness co-sign the lie — and the election key itself cannot be swapped by that
   collusion, because every ballot's validity proof binds to it under a ring signature
   only a plot-holder can make. `drop` is the attack that remained when all of that held:
   proofs convict what is *present*, so the last collusion move is subtraction —
   deniability, not forgery. The anchor answers it, and the check runs **last, gated
   behind every internal check**, so its failure means exactly one thing: this transcript
   is internally flawless and is still not the history that was published. The receipt
   must cover the *whole, final* log — a shortened history fails the root, an extended
   one fails the size (an appended entry would otherwise shadow the tally, since the
   verifier reads the latest entry of each type), and a rewritten one fails both.

   `stuff` and `box` are two attacks answered by one check, and that is the point of the
   anonymity rung rather than a gap in it: eligibility used to be *asserted* by a
   credential the box carried, and is now *proven* by a signature only a ring member can
   produce. There is nothing left to steal. `doublevote` and `smuggle` are the two checks
   the rung had to add, and both turn on the same fact: `p` is a safe prime, so `-1` is a
   quadratic non-residue and negating an element pushes it *out* of the prime-order
   subgroup — while a Fiat–Shamir proof written over it still closes whenever the relevant
   challenge comes out even (two grinds, on average, since `(-1)^even = 1`). `doublevote`
   negates the *linking tag* to forge a second identity; `smuggle` negates the *ciphertext*
   and wraps it in a freshly-forged 0-or-1 proof, then rides in superseded so the honest
   tally is unaffected and the announced result is exactly right. Each is caught by one
   subgroup check and nothing else.

   Every check that anonymity added or repurposed, and the anchor check after them, was
   mutation-tested, and each is *uniquely* load-bearing — disable it alone and the
   verifier reports `VERIFIED` on a transcript it should reject:

   | disable this check | and this tamper | certifies |
   |---|---|---|
   | ring-signature verification | `box` | Sandra's 8–6 win recorded as a 7–7 tie |
   | ring-signature verification | `stuff` | "15 voted", one of them nobody |
   | nullifier subgroup membership | `doublevote` | "15 voted", one of them Derek twice |
   | ciphertext subgroup membership | `smuggle` | a transcript carrying a non-group-element ciphertext |
   | logged-roster digest | `roster` | the eligibility rule rewritten after the vote |
   | anchored closing head | `drop` | a counted ballot erased from history — 7–7, announced and proven honestly, minus one voter's vote |

   (Ring-signature-off does *not* let `doublevote` through — the nullifier check still
   catches it; the two are independent.) Getting to *uniquely* load-bearing took work in
   two places. `box` was sharpened: an earlier version swapped a ciphertext without
   re-proving it, so the 0-or-1 proof caught it even with the ring signature disabled — a
   test that passed for the wrong reason. And `smuggle` replaced a cruder tamper (`negate`)
   that merely flipped a *counted* ballot's ciphertext: that poisons the homomorphic sum,
   so the tally recount already refuses to decrypt it — meaning the subgroup check looked
   redundant. Riding in *superseded* keeps the sum clean, so the malformed element reaches
   the box and only the subgroup check stands between it and a `VERIFIED`. A tamper another
   check also catches is not evidence for the check you are claiming.

   And in the reference transcript itself, a compromised device that displayed Sandra
   while encrypting Keith is caught by a challenge, logged (`x-ballot.audit-failed`),
   and repaired by a silent recast — the two remedies composing. **It decided the
   election**: Sandra wins 8–6, and the unrepaired phone ballot would have made it 7–7.
   What that phone actually encrypted stays sealed forever.

</details>

### The shadow of the table: what the ballot verifier is blind to

The tamper table proves what the verifier catches. Its shadow — `./waist-boundary.sh`,
run alongside `test.sh` in CI — proves what it does *not*, and must not: the four
"Yes Minister" attacks that corrupt the **narrative record** rather than the ballot.
Each passes the ballot verifier untouched, because the verifier certifies the count and
never reads the account for meaning — a machine that graded the honesty of a minute
would be the ministry of truth the kernel refuses to build.

   | narrative attack | what the verifier does | scenario · verdict |
   |---|---|---|
   | **the artful minute** — the recorded account says "carried nem con" over a ballot that split 8–6 | `VERIFIED` — it recomputes the tally, never checks it against the words | `minutes-written-by-the-winner` · **strains** |
   | **off the record** — the real choice made off-log, the logged vote a ratification | `VERIFIED` — and `drop` shows only an *anchored* omission is caught; a decision never logged has no head to anchor | `government-by-whatsapp` · **breaks** |
   | **who told the minister** — the advice that shaped the outcome, unrecorded | no advice artifact is emitted and none is checked; an outcome binds to no advice trail | `who-told-the-minister` · **strains** |
   | **the long grass** — the decision deferred past the point of mattering | timestamps are checked for order only; no deadline is enforced | the clock family · **covered** |

So the polarity is inverted: a probe is **green when the boundary holds** — the attack
still passes. It goes **red only if the verifier's behaviour has moved** (if someone
taught it to read the account), which would mean the named scenario's verdict needs
revisiting. `test.sh` proves the ballot is defended; this proves the account is the
reader's — a court's, a member's — to judge, which is the whole reason the waist is
drawn where it is.

## What v5 deliberately is not (the manifest is the source of truth)

<details>
<summary><b>Plainly</b> <i>The honest limits, one by one: anonymity the size of a village, a reproducible run whose privacy is deliberately not real, and every other caveat — declared here rather than discovered later.</i></summary>

- **`unlinkable: true` means the anonymity set is the roster, and the cost is linear in
  it.** A ballot is indistinguishable among the sixty enrolled keys — not among a
  million. Measured on this run (60-key ring, 16 ballots): the ring signature is
  **8.4 kB** of a **13.4 kB** ballot and takes **~0.7 s** to verify; a whole-transcript
  verification is **14 s**. `test.sh` verifies the transcript a dozen times over, but the
  checks are independent, so it fans them across cores and gates the O(roster) ballot pass
  behind the cheap ones that commit to it — **~45 s** on a four-core runner (a tamper
  caught in the log never reaches the ring). That is kilobytes and seconds at village
  scale, which is the only scale this prototype claims — and [§4](https://glassontin.github.io/civic-kernel/#s4 "The phone in your pocket is a polling booth that can also keep checking, all year, that nobody has touched the record. No phone? Your vote counts identically — the same maths checks it on your behalf.")'s kilobyte-payload
  requirement (T14) survives *here*, at sixty. It does not survive a national roster, and
  no amount of engineering turns an O(n) proof into an O(1) one. This is precisely why [§13](https://glassontin.github.io/civic-kernel/#s13 "Every piece of this already exists somewhere, well funded. Nobody is joining the pieces up, and no one has built the citizen's side — the phone that checks. That gap sets the plan.")
  tracks the BBS per-verifier-linkability drafts as the pre-final answer: they give the
  same `prove(eligible, decision_id) → pseudonym + proof` interface with a constant-size
  presentation. **The kernel commits to the abstraction, not to the ring.** A ring
  signature is one lattice point beneath it; BBS is another. Swapping them changes no
  other line of the protocol — which is the claim [§13](https://glassontin.github.io/civic-kernel/#s13 "Every piece of this already exists somewhere, well funded. Nobody is joining the pieces up, and no one has built the citizen's side — the phone that checks. That gap sets the plan.") makes, and this rung is the first
  evidence for it.
- **Unlinkable, not anonymous against the seed.** Every secret in the *reference*
  transcript, including each voter's `nym_secret`, derives from a public constant so
  that run is byte-reproducible. Anyone can therefore recompute every tag and
  de-anonymize *this particular* transcript. That is the same declared subtraction that
  makes `receipt_free` reproducible: the mechanism is real, this run's privacy is not,
  by design. `run --real` lifts exactly this subtraction — every key and scalar from
  the OS, encryption randomness discarded at cast — and the verifier passes unchanged,
  which is the point: it never depended on where the secrets came from. What `--real`
  does *not* change: one process still plays every actor, so key custody and the
  enrolment ceremony are still simulated. The `agm` flow then lifts custody for real,
  party by party: `x` is generated on the voter's device (cast.html) and the register —
  which certifies `g^x` on its own machine and never sees `x` — cannot link a ballot
  to a member even in principle, while the committee cannot enrol anyone the register
  did not certify; the witnesses hold their own keys on their own machines, co-signing
  checkpoints only when the history extends the one they remember; the trustees deal
  their own polynomials on their own machines, exchanging cross-shares directly, so no
  machine anywhere holds the joint decryption key and the committee cannot tally
  alone; and the anchor lodges the closing head on its own machine, once per log,
  refusing forever after to reprint a different one. The committee is left with one
  key, the log's: it publishes, gates and assembles, and vouches for nothing by
  itself. The tamper suite refuses every real-randomness transcript, `run --real` or
  `agm`, because its insiders' keys are no longer anyone's to hold.
- **What the box still shows.** How many distinct voters, how many re-voted and how many
  times (tags are equal or they are not), and that one device cheated. Not who. Cast
  order carries no identity: the reference run casts in a shuffled order and publishes the
  box sorted by tag, because `seq` decides which of a voter's ballots counts and so must
  be inside the signed ballot.
- **The assisted channel is unmarked, and that is the guarantee.** Ernest votes at the
  table with two tellers; his ballot carries no `channel` field and no teller's
  countersignature, because one `assisted` label in a ring of sixty names him. T9 promises
  he can vote and have it verified like anyone's — not that the record says he needed help.
- **[Sybil resistance](../README.md#w-sybil) is unchanged and still `weak`.** The ring proves *a* plot-holder
  cast this ballot, exactly once. It cannot know whether two roster entries are one human.
  That was always the issuer's job, and unlinkability neither helps nor hurts it.
- **`receipt_free: true` holds at the transcript level, with a named behavioural edge.**
  The public artifacts never link any ballot to a choice — only the aggregate is
  decrypted, so nothing on the bulletin board can prove what you voted. But a client
  that *retains* its encryption randomness can reconstruct a receipt (the Helios
  caveat), so the protocol requires — and `clubvote.py` literally does — discarding `r`
  the moment a ballot is cast. Challenged ciphertexts, whose `r` is public by design,
  are spoiled and never cast. [Receipt-freeness](../README.md#w-receipt-free) against a coercer who seizes the device
  *before* casting remains `coercion_resistance: revote-silent`, and breaks against
  live observation, as the harness has always said. Anonymity adds one thing here and
  only one: a coercer who does not hold your nym secret can no longer read the public
  box to check whether you abstained.
- **The anchor seals the close of history, not the window.** The Star's receipt pins the
  final head: once printed, history can no longer shorten, stretch, or change. A ballot
  suppressed *before* the head is published is not the anchor's to catch — that is the
  voter's own check (recorded-as-cast): only she knows her tag, so only she can see it
  missing from the public box, a check anonymity preserves rather than defeats. And an
  anchor is one more party, not magic: a newspaper that colludes too is answered by a
  second receipt — `trust.json` names as many anchors as the verifier requires, and
  receipts are additive. In this simulation the pinned key stands in for the printed
  page; in a deployment the receipt is the archive itself, or refusal 5's chain —
  notary of last resort, never gatekeeper.
- **The DKG (distributed key generation) has no hash-commitment round.** Each trustee deals their own
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
  verifier's explicit trust anchor set, naming the keys it trusts, in `witnesses` the
  parties it *requires* to co-sign every log head, and in `anchors` the external parties
  that must hold a receipt for the closing one. Those lists have to
  live outside the transcript. The manifest declares its own witnesses, but the manifest
  is signed by the log key — so an insider holding that key can lower their own bar to
  zero, and did, until `unwitness` was written to prove it. A manifest cannot be its own
  standard. Correspondingly, `verify.py` declines to certify a log whose trust anchors
  name no witness — or no external anchor, since an unanchored log cannot refute a
  quietly erased ballot. It holds **no voter keys at all**, and that is the shape of the rung:
  a verifier trusts the ring, never a name. The trustees need no anchor either — their
  layer is held up by proofs, not signatures, which is why it survives the collusions
  that defeat the log.
- The ballot group is pinned **by name** to the verifier's own constants; a transcript
  that could supply its own group parameters could supply a smooth one. The verifier
  also subgroup-checks the roster's keys, which no tamper exercises (a rewritten roster
  fails its logged digest first) — declared here as input hygiene, not as a defence.
- Canonicalization approximates JCS (RFC 8785) as sorted compact JSON — exact for this
  artifact set (strings, integers, booleans only).

</details>
