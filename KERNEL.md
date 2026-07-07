# The Kernel, distilled

The normative core of the Civic Kernel on one page. The
[essay](https://glassontin.github.io/civic-kernel/) argues it, the [schemas](schema/)
define it, the [harness](https://glassontin.github.io/civic-kernel/scenarios.html)
measures it, the [model](docs/functional-model.md) gives it dynamics — this page only
states it. If a requirement is not here, it is rationale, evidence, or ecosystem.

> **Fourteen threats, four services, four verbs, two formats, one floor — and twelve refusals.**

*(§N refers to the essay's sections; T-numbers to the threat register below.)*

## The problem (§1)

A democracy must produce one output — decisions that losers accept as legitimate — under
permanently adversarial conditions, for decades, while its own rules change underneath it.
That is a distributed-systems problem with a hostile threat model. The kernel is the
smallest set of guarantees that markets and communities cannot provide for themselves.

## Goals, in priority order (§1)

1. **Freedom by default** — the system knows as little as possible about each person.
2. **Capture resistance** — no state, vendor, or majority faction can seize the machinery.
3. **Rights as invariants** — the UDHR is the type system; a violating decision fails to
   type-check, whatever its majority.
4. **Evolvability** — the rules amend through the system itself: versioned, staged, reversible.
5. **Inclusion** — no smartphone, no sight, no trust in computers: still first-class.

## The threats (§2)

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

## Four services, and no fifth (§3)

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

## Four verbs (§8)

**prove · cast/challenge · verify · read** — the entire citizen surface. Payloads are
kilobytes, self-contained, valid whenever they arrive: transport-agnostic,
delay-tolerant, deliverable over mesh, radio, or sneakernet when IP dies (§4, T14).
Paper is the zero-bandwidth floor — same protocol, same tally, same audit, not a legacy
annex (T9). A surface this small has nowhere to hide burden (T12).

## Two formats — the waist (§6, [`schema/`](schema/))

Thinner than the services: a [log entry](schema/log-entry.schema.json) and a
[conformance manifest](schema/manifest.schema.json). Adoption is per-person subscription
on a lattice, not jurisdictional sovereignty. A community may sit anywhere below the full
profile — but its manifest declares every subtraction machine-readably, and the citizen's
client renders it. Dilution becomes legible, not lethal (T10); a manifest that lies is a
consistency-proof failure, not a marketing dispute.

## One floor (§5)

The goals above and the thirty UDHR invariants are pinned beneath the amendment process:
changeable only by near-consensus, while everything about mechanism stays cheap to amend —
staged, canaried, sunset-claused. Cheap to change mechanisms, nearly impossible to change
personhood: the design in one sentence. Scope, precisely: the pin binds inside a community
subscribed to the full profile; across the lattice it is the reference posture adoption
pressure pushes toward — elsewhere the kernel guarantees only that the gap is legible (§5–§6).

## Twelve refusals

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

## The dynamics ([model](docs/functional-model.md))

The OS-sense kernel induces a second, mathematical one: an operator on the space of
democracies. State is a tensor over (community × policy-domain × axis); "better" is a
partial order, per domain — subsidiarity as geometry, one attractor per domain, no global
optimum. Two declared, per-domain controls govern movement: **damping** (τ — how fast)
and **decaying hysteresis** (whether to flip at all: the setpoint is a continuous,
always-current vote; the law is a debounced actuator that moves only on durable, settled
shifts). The floor constrains; it is never the target. Status, honestly: the structure is
well-posed; the coefficients are radically underdetermined — a specification and a
research program, not a trained system.

## What is measured (July 2026)

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
- **19 scenarios**, each cross-validated against the waist schemas and each anchored to
  documented real-world precedents (46 verified citations — the schema requires them: no
  attack without a cited precedent): 15 strain, 3 break, 1 holds. The one hold is
  `records-rewrite` — the log defeating tampering, the mechanism the design leans on
  hardest. The three breaks are the named limits meeting unaccountable power: coercion
  under live observation, an executive that ignores court orders, a remedy too weak to
  stop a majority.

## What is not solved (§12)

Enrolment still needs a physical ceremony. Remote voting and coercion resistance
genuinely conflict. Rights classification is judgment with a human backstop, not
computation. Credential recovery breaks pseudonym continuity. Post-quantum ballot
cryptography is not yet shipped.

---

*Every component named ships today; the composition is the contribution. The first running
code is [`proto/`](proto/): the club vote end to end — all four verbs, waist-valid artifacts,
an independent verifier, and a manifest that declares its own subtractions. The rest is
specification, harness, and corpus — see the [README](README.md).*
