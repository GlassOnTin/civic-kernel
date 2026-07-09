# The Kernel

The rules of the Civic Kernel, on one page. The
[essay](https://glassontin.github.io/civic-kernel/) argues them, the
[schemas](schema/) define them, the [prototype](proto/) runs them, the
[harness](https://glassontin.github.io/civic-kernel/scenarios.html) measures them, the
[model](docs/functional-model.md) gives them motion — this page only states them. If
it is not here, it is not a rule: it is explanation, evidence, or the layer above.

> **Fourteen threats, four services, four verbs, two formats, one floor — and twelve refusals.**

*(§N refers to the essay's sections; T-numbers to the threat register below.)*

## The problem (§1)

<details>
<summary><b>Plainly</b> <i>The job: keep producing decisions the losers still accept, while everyone — the operators included — has a reason to cheat.</i></summary>

A democracy must produce one output — decisions that losers accept as legitimate — under
permanently adversarial conditions, for decades, while its own rules change underneath it.
That is a distributed-systems problem with a hostile threat model. The kernel is the
smallest set of guarantees that markets and communities cannot provide for themselves.

</details>

## Goals, in priority order (§1)

<details>
<summary><b>Plainly</b> <i>Five promises, strongest first: know as little as possible about anyone, be too small to steal, keep every decision inside human rights, stay changeable, leave nobody out.</i></summary>

1. **Freedom by default** — the system knows as little as possible about each person.
2. **Capture resistance** — no state, vendor, or majority faction can seize the machinery.
3. **Rights as invariants** — the UDHR is the type system; a violating decision fails to
   type-check, whatever its majority.
4. **Evolvability** — the rules amend through the system itself: versioned, staged, reversible.
5. **Inclusion** — no smartphone, no sight, no trust in computers: still first-class.

</details>

## The threats (§2)

<details>
<summary><b>Plainly</b> <i>Every way to break it, listed before designing it: fourteen attacks, each with a named answer — and two unanswered on purpose, because the cure would be a ministry of truth.</i></summary>

Design runs from the attacks backwards. T1–T9 attack the machinery, T10–T12 the terms
of participation, T13 the defense itself, T14 the wires beneath it all.

| | threat | answer |
|---|---|---|
| T1 | state capture | nothing worth capturing: thin kernel, distributed operators, forkable with history (§3, §5) |
| T2 | vendor capture | open protocol, open clients, no remote attestation (§1, §4) |
| T3 | sybils | ceremony-issued credentials; cryptographic uniqueness per decision (§3.1, §10) |
| T4 | coercion & vote buying | receipt-free verifiable ballots; silent re-vote, last ballot counts (§3.2) |
| T5 | device compromise | keys in enclaves, cast-or-audit challenges, second channel, paper path (§3.2, §4) |
| T6 | surveillance chill | zero-knowledge eligibility, unlinkable pseudonyms, local-first data (§3.1, §4) |
| T7 | majoritarian rights-stripping | rights guard re-routes to the constitutional path (§3.3) |
| T8 | record tampering | witnessed append-only logs; any phone detects a rewritten past (§3.4) |
| T9 | digital exclusion | paper, kiosk, assisted — same protocol, same verifiability (§4) |
| T10 | dilution & standards capture | signed conformance manifests; subtraction is legible (§6) |
| T11 | epistemic gating | no gate on the ballot path; scaffold everything, assess nothing (§7) |
| T12 | sludge | four verbs, computable eligibility, cited demands, published interaction cost (§8) |
| T13 | autoimmune defense | sense at machine speed, respond at constitutional speed (§9) |
| T14 | infrastructure denial | kilobyte payloads, delay-tolerant, paper as the zero-bandwidth floor (§4, §3.4) |

Two threats are deliberately unanswered — disinformation and bad judgment — because a
central answer is a ministry of truth (refusal 11). And the answers are measured claims,
not promises: under the harness, T4 breaks against coercion under live observation (the
limit §12 concedes), and the `executive-ignores` run breaks on an enforcement gap no
T-number owns — a decision binds only where power obeys the record. The register states
what the design answers; the harness reports what survives.

</details>

## Four services, and no fifth (§3)

<details>
<summary><b>Plainly</b> <i>The whole machine is four small parts: prove you may speak, decide things anyone can check, keep decisions inside human rights, keep a record nobody can rewrite.</i></summary>

| service | guarantees | answers |
|---|---|---|
| **SVC-1 Personhood** | "eligible, and not already spoken in this decision," proven without revealing which person — unlinkable per-decision pseudonyms | T3 sybils, T6 surveillance |
| **SVC-2 Decisions** | end-to-end verifiable ballots: cast-as-intended (cast-or-audit) *and* receipt-free; sortition as a publicly checkable claim | T4 coercion, T5 device compromise |
| **SVC-3 Rights guard** | every UDHR article a machine-checkable invariant over decision metadata; a tripped invariant re-routes to supermajority + deliberation + adversarial review — escalates, never vetoes | T7 rights-stripping |
| **SVC-4 Transparency log** | append-only Merkle log, cross-witnessed; any phone proves inclusion and that today's log extends yesterday's | T8 tampering, T14 shutdown |

Admission test for a fifth: a function enters the kernel only if the ecosystem cannot
provide it competitively **and** its absence breaks a §1 goal. Reputation, deliberation,
fact-checking, delegation registries all fail it — each embeds an opinion about how
politics should work, and opinion lives above the kernel, where it can be abandoned.

</details>

## Four verbs (§8)

<details>
<summary><b>Plainly</b> <i>Everything a citizen ever does is one of four moves — prove, cast, verify, read — in messages small enough to travel by radio, or on paper.</i></summary>

**prove · cast/challenge · verify · read** — the entire citizen surface. Payloads are
kilobytes, self-contained, valid whenever they arrive: transport-agnostic,
delay-tolerant, deliverable over mesh, radio, or sneakernet when IP dies (§4, T14).
Paper is the zero-bandwidth floor — same protocol, same tally, same audit, not a legacy
annex (T9). A surface this small has nowhere to hide burden (T12).

</details>

## Two formats — the waist (§6, [`schema/`](schema/))

<details>
<summary><b>Plainly</b> <i>The waist is the narrow middle everything must share to talk at all — for the internet that is the IP packet; here it is two file formats. Any group may run a weakened version, but its manifest must say so in a form anyone's phone can read — and the one thing a manifest cannot vouch for is its own witnesses.</i></summary>

Thinner than the services: a [log entry](schema/log-entry.schema.json) and a
[conformance manifest](schema/manifest.schema.json). Adoption is per-person subscription
on a lattice, not jurisdictional sovereignty. A community may sit anywhere below the full
profile — but its manifest declares every subtraction machine-readably, and the citizen's
client renders it. Dilution becomes legible, not lethal (T10); a manifest that lies is a
consistency-proof failure, not a marketing dispute.

One limit, measured in [`proto/`](proto/) rather than assumed: the manifest is signed by the
operator's own log key, so it cannot vouch for *who witnesses it*. An operator can rewrite
history, regenerate the log heads, declare in the manifest that the log never had witnesses,
and hand over a transcript on which every signature verifies and nothing internally
disagrees. The witness set is therefore the one thing a verifier must hold out of band — from
DID resolution and the witness ecosystem, never from the transcript under audit. A manifest
cannot be its own standard (§6, T8, T10).

</details>

## One floor (§5)

<details>
<summary><b>Plainly</b> <i>Mechanisms stay cheap to change; a person's standing as free and equal is nearly impossible to change. That asymmetry is the whole design.</i></summary>

The goals above and the thirty UDHR invariants are pinned beneath the amendment process:
changeable only by near-consensus, while everything about mechanism stays cheap to amend —
staged, canaried, sunset-claused. Cheap to change mechanisms, nearly impossible to change
personhood: the design in one sentence. Scope, precisely: the pin binds inside a community
subscribed to the full profile; across the lattice it is the reference posture adoption
pressure pushes toward — elsewhere the kernel guarantees only that the gap is legible (§5–§6).

</details>

## Twelve refusals

<details>
<summary><b>Plainly</b> <i>Twelve things the kernel will never do — each one a door capture could have walked through.</i></summary>

Each closes a capture surface. The pointer is the argument.

1. **No fifth service.** Nothing opinionated in the core. (§3)
2. **No population database.** Uniqueness without identity, even against the issuer. (§3.1)
3. **No remote attestation.** Integrity comes from the protocol, or a vendor holds a veto
   over participation. (§4)
4. **No required device.** The phone is the richest endpoint, never a required one. (§4, T9)
5. **No token in the citizen's path.** A chain may anchor log heads — notary of last
   resort, never database, never gatekeeper. Participation never costs gas. (§6)
6. **No comprehension gate on the ballot path.** Scaffold everything, assess nothing:
   whoever writes the test owns the electorate. (§7, T11)
7. **Measure the process, never the person.** The same datum is tyranny as an individual
   gate and hygiene as a population signal. (§7–§8)
8. **No demand without a cited rule.** A form field that cannot point to the
   machine-readable provision requiring it cannot be asked. (§8, §11, T12)
9. **AI holds a microscope, never a pen.** Sense at machine speed, respond at
   constitutional speed; break-glass powers pre-legislated, witnessed, self-expiring. (§9, T13)
10. **The kernel enforces a membership boundary; it never decides one.** Who counts is
    versioned, witnessed governance. (§10)
11. **No ministry of truth.** The kernel does not decide truth, host debate, rank
    arguments, moderate speech, or pick outcomes — process integrity only. (§1–§2)
12. **The math never carries the objective.** Representation, damping, legibility — yes;
    the heading is declared per domain, per community, revisably. The UDHR enters as
    coordinate frame and floor, never as telos. ([model](docs/functional-model.md), Part 7)

</details>

## The dynamics ([model](docs/functional-model.md))

<details>
<summary><b>Plainly</b> <i>The maths of change: each policy area moves toward its own best, slowly, and flips only on durable shifts. The structure is solid; the numbers to tune it are honestly unknown.</i></summary>

The OS-sense kernel induces a second, mathematical one: an operator on the space of
democracies. State is a tensor over (community × policy-domain × axis); "better" is a
partial order, per domain — subsidiarity as geometry, one attractor per domain, no global
optimum. Two declared, per-domain controls govern movement: **damping** (τ — how fast)
and **decaying hysteresis** (whether to flip at all: the setpoint is a continuous,
always-current vote; the law is a debounced actuator that moves only on durable, settled
shifts). The floor constrains; it is never the target. Status, honestly: the structure is
well-posed; the coefficients are radically underdetermined — a specification and a
research program, not a trained system.

</details>

## What is measured (July 2026)

<details>
<summary><b>Plainly</b> <i>Results, not promises: what held, what strained, what broke — and the one fraud only the world's copy of history catches.</i></summary>

- **The remedy axis gates the flagship verdict.** One attack — a 61% majority banning a
  minority's worship — against four real rights settlements: the UK (remedy
  `declaration`) **breaks**; Germany, the US, and the EU (remedy `strike`; the EU's scope
  conditional under Art 51) **strain**. All four back the religion right (invariant 18) —
  the flip is remedy, not coverage. A byte-identical UK counterfactual with `strike`
  flips `breaks → strains`.
  ([corpus](https://glassontin.github.io/civic-kernel/scenarios.html#corpus))
- **The UK improvement path stalls at the remedy step**
  ([trajectory](docs/uk-trajectory.md)). The cheap, sovereignty-free moves — adopt the
  log, verifiable ballots — are worth taking and don't flip the verdict; the one move
  that flips it requires the sovereign to bind itself. Legibility ≠ availability ≠
  movement.
- **The tally survives everyone who signs things.** In [`proto/`](proto/), ballots are
  sealed to a distributively-generated 2-of-3 trustee key — no party ever holds the
  joint secret — and only their homomorphic sum is ever decrypted. A
  committee that holds the log key *and* both witnesses' keys can rewrite history with
  every hash and signature agreeing — and a rigged decryption, a rigged count, and an
  accepted double-vote are still each caught, by a Chaum-Pedersen share proof, a public
  recount, and a 0-or-1 ballot-validity proof respectively (mutation-tested: disable any
  one check and its fraud certifies). Signature collusion's last move was to *drop*
  history — deniability, not forgery: erase one counted ballot, re-sign everything,
  retally honestly, and nothing inside the transcript objects, because nothing in it is
  forged. The external anchor closes it: the closing log head is republished beyond the
  collusion's reach (a newspaper's public notices, simulated — refusal 5's notary of last
  resort), and the erasure is caught by the anchor check alone (mutation-tested: disable
  it and the erased history certifies). Declared residue: the anchor seals history at
  close; suppression *before* the head is published is caught by the voter finding their
  own tag missing from the public box — a check anonymity preserves, since only they
  know the tag.
- **So does the franchise, and it costs anonymity nothing.** A ballot carries no name: it
  proves membership of the roster's key ring (a linkable ring signature) and a per-decision
  pseudonym `H(decision_id)^nym_secret` — SVC-1's `nym_secret × context_id`, running. The
  same total collusion cannot mint a ballot or re-aim one, because eligibility is *proven*,
  not asserted by a credential the box carries; and no voter can vote twice, because the
  pseudonym is bound to the ring signature and checked into the prime-order subgroup
  (mutation-tested: remove that one check and one secret becomes two voters — the negated
  tag `-T` verifies just as well). The honest limit is arithmetic, not cryptographic: the
  anonymity set is the roster and the proof is linear in it — 8.4 kB a ballot at sixty
  plot-holders. Populations need the constant-size BBS presentation §13 tracks. The
  interface — `prove(eligible, decision_id) → pseudonym + proof` — was written against the
  abstraction, so swapping the proof system changes nothing else.
- **T5's challenge and T4's silent re-vote compose — and decided the election.** In the
  reference run, a compromised device that displayed one candidate while encrypting the
  other was caught by a cast-or-audit challenge, logged (`x-ballot.audit-failed`), and
  repaired by a silent recast. The repair decided it: an 8–6 win where the unrepaired
  ballot would have made it 7–7 — and what the cheating device actually encrypted stays
  sealed forever.
- **19 scenarios**, each cross-validated against the waist schemas and each anchored to
  documented real-world precedents (46 verified citations — the schema requires them: no
  attack without a cited precedent): 15 strain, 3 break, 1 holds. The one hold is
  `records-rewrite` — the log defeating tampering, the mechanism the design leans on
  hardest. The three breaks are the named limits meeting unaccountable power: coercion
  under live observation, an executive that ignores court orders, a remedy too weak to
  stop a majority.

</details>

## What is not solved (§12)

<details>
<summary><b>Plainly</b> <i>Five problems nobody has solved — this design included. Named, not hidden.</i></summary>

Enrolment still needs a physical ceremony. Remote voting and coercion resistance
genuinely conflict. Rights classification is judgment with a human backstop, not
computation. Credential recovery breaks pseudonym continuity. Post-quantum ballot
cryptography is not yet shipped.

</details>

---

*Every component named ships today; the composition is the contribution. The first running
code is [`proto/`](proto/): the club vote end to end — all four verbs, waist-valid artifacts,
anonymous ballots sealed to a trustee quorum and never individually opened, an independent
verifier that catches twelve tampers by their named defences — [the same checks run in any
browser](https://glassontin.github.io/civic-kernel/verifier.html) — and a manifest that
declares its own subtractions. The rest is specification, harness, and corpus — see the
[README](README.md).*
