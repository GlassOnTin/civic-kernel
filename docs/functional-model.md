# The Civic Kernel as a Functional Operator

**Status: v0, exploratory — a speculative companion to the deployed thesis.** Plainly:
this document tries to write the kernel's politics as mathematics — where a democracy
stands, which way is better, how fast its law should move — and names every place the
maths runs out. The deployed argument is [`index.html`](../index.html); the one-page
statement of both is [`KERNEL.md`](../KERNEL.md). What follows writes down, as precisely
as honesty allows, what it would mean to treat the Civic Kernel not only as a thin
service core but as a *mathematical operator* that maps a starting democracy toward an
empirically more-likely-better one — and, just as important, exactly where that model is
solid and where it is underdetermined.

*(Throughout, **§N** refers to a section of the architecture essay; **Part N** to a section
of this document.)*

## 0 · Two senses of "kernel"

<details>
<summary><b>Plainly</b> <i>One word, two meanings: the small core that runs things, and a rule for how a democracy moves. The claim is that building the first gives you the second.</i></summary>

The architecture uses *kernel* in the operating-systems sense: a thin, boring, invariant
core (four services, one waist). This document uses it in a second, mathematical sense:
an operator on the space of possible democracies. The claim is that **the first generates
the second** — the thin core supplies a state space, an order, a set of legal transitions,
and an invariant floor, and the induced dynamics *is* the operator. The pun is
load-bearing, not decorative.

</details>

## 1 · State

<details>
<summary><b>Plainly</b> <i>Where a democracy stands, written as numbers: for each community and each area of law, which rights are backed, what a court can do about a breach, on what terms, when the remedy can arrive, and what holds it in place. Five real systems are measured so far.</i></summary>

A polity's configuration is a tensor **S** indexed by **(community × policy-domain × axis)**:

- **community** — the fractal units of [§6](https://glassontin.github.io/civic-kernel/#s6 "Nobody has to adopt all of it. Any group may take the parts it wants — but must publish, in a form anyone's phone can read, exactly what it left out.") (household … nation), nesting.
- **policy-domain** — trade, family, criminal, environmental, … . *This index is the key
  upgrade.* The earlier sketch flattened it, and flattening is what makes "the EU is good
  for X" a category error: good configurations are domain-relative.
- **axis** — the measurable dimensions of a rights/decision regime. So far: **coverage**
  (which of the 30 UDHR invariants are backed), **remedy** (none / declaration / escalate /
  strike), **scope** (unconditional / conditional), **entrenchment** (what holds the
  remedy in place — the process that could remove it: none / statute / doctrine /
  constitutional text / treaty / eternity clause; motivated by the DE–US pair, whose
  identical `strike` is held by an eternity clause in one and by precedent in the other),
  **timing** (when the remedy can arrive relative to the harm: pre-enactment /
  pre-enforcement / post-enforcement; measured by `majority-vs-minority-us-abstract`,
  whose moved variable turned out to have no waist field at all), and — extending —
  **interaction-cost /
  sludge** ([§8](https://glassontin.github.io/civic-kernel/#s8 "Paperwork can quietly take a right away. So: four verbs, nowhere to hide an extra step, and every demanded field must name the rule that lets it ask.")), **inclusion** ([§4](https://glassontin.github.io/civic-kernel/#s4 "The phone in your pocket is a polling booth that can also keep checking, all year, that nobody has touched the record. No phone? Your vote counts identically — the same maths checks it on your behalf.")), **capture-resistance** ([§1](https://glassontin.github.io/civic-kernel/#s1 "The job: keep producing decisions the losers still accept, while everyone — the operators included — has a reason to cheat.")).

We have **S** measured at five real coordinates (UK, US, Germany, EU, PRC) on the rights axes —
coarsely, and domain-agnostically; the PRC point is the first at the remedy axis's floor
(`none`). Five points in a high-dimensional space: enough to see
structure, nowhere near enough to fit dynamics (see [Part 8](#8--empirical-status--solid-specification-underdetermined-predictor "The skeleton is sound; the numbers to run it do not exist. Five measured systems, one run of history, a model that changes what it measures: a research programme, not a trained system.")).

On the two newest axes, the five coordinates (plus the reference kernel) read from the
same instruments and runs that measured the first three:

| coordinate | entrenchment — what holds the remedy | timing — when it arrives |
|---|---|---|
| UK | **statute** — the HRA is an ordinary Act, one Parliament from repeal: the weak remedy is also weakly held | post-enforcement — and the arrival binds nothing (s.4(6)) |
| Germany | **eternity clause** — Art 79(3); the court's own structure entrenched since 2024 | pre-enforcement — abstract review; the measured statute never operated |
| US | **doctrine** — Marbury applied through Lukumi, held by whoever holds the bench | post-enforcement, measured (injury is the price of standing); pre-enforcement measured counterfactually at 152 vs 439 days |
| EU | **treaty** — unanimity in both directions | post-enforcement — the ban ran the fourteen months the Art 51 fight took |
| PRC | vacuous — no remedy to hold; what Art 1 entrenches is the other thing | vacuous — nothing arrives |
| reference kernel | the amendment process itself — [§5](https://glassontin.github.io/civic-kernel/#s5 "The rules can change — in stages, with expiry dates unless renewed. The one thing nearly impossible to change: each member's standing as a free and equal person.")'s pin | pre-enactment — the guard routes the proposal before the decision closes |

Two riders keep these honest. Neither axis is totally ordered — kinds, not ranks: US
doctrine has outlived every statute in the table and can be re-read by one bench without
a vote, so "stronger" is exactly the partial-order judgment the model refuses to make
globally. And both are now **waist fields as well**: `rights_guard.entrenchment` and
`rights_guard.timing` entered the manifest schema by the same run-motivated lifecycle
that added `scope` — the corpus columns declare them, the validator enforces both the
values and their vacuousness where remedy is `none`, and the measuring run's two
Americas, byte-identical when it ran, now differ by exactly one declared field. The
legibility gap the counterfactual exposed is closed by what it motivated.

</details>

## 2 · Order — partial, and per-domain

<details>
<summary><b>Plainly</b> <i>“Better” is not one number. Two democracies can each beat the other in different ways, and better-in-trade-law is not better-in-family-law. There is no single best democracy, by design.</i></summary>

"Better" is not a scalar.

- **Partial, not total.** On the axes, states form a partial order — the [§6](https://glassontin.github.io/civic-kernel/#s6 "Nobody has to adopt all of it. Any group may take the parts it wants — but must publish, in a form anyone's phone can read, exactly what it left out.") [*lattice*](../README.md#w-lattice),
  literally. A state dominates another only if it is ≥ on every axis. The UK (higher
  coverage, weak remedy) and the US (lower coverage, strike) are **incomparable**; there is
  no global ranking, by design.
- **Domain-relative.** The improvement direction in trade-law space is not the improvement
  direction in family-law space. This is not a wrinkle to smooth away — it is the
  **principle of subsidiarity** (TEU Art 5: act centrally only where the objective is
  better achieved there), expressed as geometry. The operator therefore has **one attractor
  per domain**, never one global optimum.

</details>

## 3 · The operator — a subsidiarity vector field

<details>
<summary><b>Plainly</b> <i>Each area of law looks at the real systems most relevant to it and is pulled toward the best of them. Crucially, people — not the maths — declare what counts as relevant and better.</i></summary>

The operator is a **vector field** `v(S, domain)` giving the local improvement direction per
domain, plus a stochastic transition kernel that moves along it. It has the shape of
attention:

> for a domain *d*: `pull(d) = Σ_r softmax( sim(S_d, reference_r) ) · direction(reference_r)`

— each domain "attends" to the reference regimes most relevant *to that domain's objective*
and is pulled toward a weighted blend. Trade attends to the EU regime; family attends to a
low-sludge, local one. This is the tensor structure borrowed from transformer attention,
and it is genuinely apt.

**But the weights are not learned; they are declared.** In an LLM, attention weights are fit
to a loss by gradient descent. Here, `direction(reference_r)` and the per-domain objective
inside `sim` are **democratic inputs** — chosen, per domain, per community, revisably. That
is the entire safety property ([Part 7](#7--the-safety-property--what-the-math-must-never-do "The rule above all the others: the maths may describe, steady, and illuminate; it may never decide what “better” means. People choose the direction — the model only makes the ground visible.")), and the load-bearing difference between this model
and a technocracy.

</details>

## 4 · Damping — the control-theory core (rate)

<details>
<summary><b>Plainly</b> <i>How fast should law respond to opinion? Too fast and policy see-saws; too slow and nothing can be repaired. The right speed differs by area — the UK's flaw is one speed for everything.</i></summary>

A polity is a feedback loop: preference − state → error → institutions → law → society →
sensors (elections, press, the harness) → back. Institutional friction — supermajorities,
deliberation windows, parliamentary sovereignty — is a **damping coefficient**.

- **Under-damped:** policy oscillates (repeal-and-replace every cycle).
- **Over-damped:** sclerosis — the UK self-lock, where the rights remedy cannot be
  strengthened because that requires the sovereign to bind itself.
- **Critically damped:** the fastest response that does not overshoot — exactly "**as
  quickly as possible, or as slowly as needed**."

Good damping is **domain-specific**: heavy on the constitutional core ([§5](https://glassontin.github.io/civic-kernel/#s5 "The rules can change — in stages, with expiry dates unless renewed. The one thing nearly impossible to change: each member's standing as a free and equal person.")'s near-consensus
pin), light on reversible policy. The UK's pathology is *uniform* damping — parliamentary
sovereignty damps everything equally, so it over-damps rights-repair while under-damping
ordinary law. [§5](https://glassontin.github.io/civic-kernel/#s5 "The rules can change — in stages, with expiry dates unless renewed. The one thing nearly impossible to change: each member's standing as a free and equal person.")'s layered amendment speeds are this field in embryo; the model generalizes
it to a tunable damping tensor and hands it the standard tools of control theory (stability,
phase margin, pole placement) as the language for tuning it.

Damping governs *how fast* the state moves. It does nothing to stop a system flipping back
and forth across a threshold — a distinct failure that needs a distinct tool ([Part 5](#5--hysteresis-continuous-voting-and-the-oscillation-attack "Anyone may change their vote at any moment; the law moves only on a settled, lasting shift. One narrow Thursday cannot flip a nation — and the stickiness must fade with time, or it protects the last change instead of stability.")).

</details>

## 5 · Hysteresis, continuous voting, and the oscillation attack

<details>
<summary><b>Plainly</b> <i>Anyone may change their vote at any moment; the law moves only on a settled, lasting shift. One narrow Thursday cannot flip a nation — and the stickiness must fade with time, or it protects the last change instead of stability.</i></summary>

**Hysteresis** is a dead-band with memory: the threshold to reverse a decision differs from
the threshold that made it, so the state holds against noise near the margin. The canonical
device is the **Schmitt trigger** — flip *out* at 55%, flip *back* only at 55% the other
way; in the 45–55% band, nothing moves. It changes not *how fast* you flip but *whether you
flip at all* near the boundary, and it is the piece the kernel lacks for decisions that are
cheap to vote on but expensive to actuate. (Version control already uses it: a change
matures on a branch — an isolated dead-band — before it may touch the shared trunk.
Branch-then-merge is hysteresis for a codebase; a force-push that rewrites the trunk is the
T8 record-tampering attack, and the distributed clones that would detect it are [§3.4](https://glassontin.github.io/civic-kernel/#s3-4 "Every act lands in a public record that can only grow. Rewrite yesterday and the sums stop matching in every copy of today — and any phone can tell.")'s
witnesses. The tool we build the kernel with is a working miniature of it.)

**The mechanism: continuous vote, debounced actuator.** Split the system in two.

- The **setpoint** P(t) is the electorate's preference, held *continuously and
  always-current* — any citizen may change their vote at any moment. This is not new: it is
  the `recast_policy` "any later ballot supersedes an earlier one" already in the decisions
  service ([§3.2](https://glassontin.github.io/civic-kernel/#s3-2 "Your ballot is sealed before it leaves your hand and counted without being opened. You can check it was counted; you cannot prove to anyone how you voted.")), the same continuity that gives the coerced voter her escape. It must stay
  unrestricted — restrict it and you trade away coercion-resistance and responsiveness at
  once.
- The **plant** L(t) is the *implemented* law. It does not track P(t) directly; it tracks a
  **low-pass-filtered, hysteresis-gated** P, moving only when settled preference clears the
  dead-band *and* persists past the domain's time-constant τ.

This is, precisely, **debouncing a referendum** — the operation that turns one noisy
switch-press into one clean signal. The vote may wobble; the law moves only on a durable,
settled shift.

Brexit is the worked case. Under a continuous setpoint with a debounced actuator, a one-off
52% does not flip a high-switching-cost, economy-and-rights-touching state, because that
domain carries heavy damping (long τ) and a wide Schmitt band: Leave would have to be
*durable*, not a single Thursday's mood. And the property one actually wants falls out for
free — if preference later shifts durably back toward rejoin, the continuous setpoint tracks
it; there is no permanent lock-in from one vote. Responsive to real shifts, immune to
transient thrash.

**The oscillation / decision-thrashing attack** — a candidate for the threat register (not
in the current T1–T14). A coordinated bloc drives the setpoint back and forth *not to win a
position but to make the actuator thrash* — leave / rejoin / leave — burning enormous real
cost though no position durably holds; in control terms, high-frequency injection into the
setpoint to wear the actuator, or driving it at resonance. The debounced actuator defeats it
structurally: a transient flip never clears the dead-band or outlasts τ, so L does not move.
And the attacker's cost to oscillate is **time and margin, never money** — the
no-token-in-the-citizen's-path red line ([§6](https://glassontin.github.io/civic-kernel/#s6 "Nobody has to adopt all of it. Any group may take the parts it wants — but must publish, in a form anyone's phone can read, exactly what it left out.")) holds; stability is bought with cooling-off and
supermajority-to-reverse, not gas.

**Two dangers, because hysteresis cuts both ways.**

1. **The one-way ratchet.** The stickiness that stops oscillation also entrenches a *first*
   change: an actor who flips something *once* then shelters behind the hysteresis meant to
   prevent oscillation, which now protects *their* change from being undone. Anti-oscillation
   silently becomes pro-incumbent-change. So **hysteresis must decay** — stickier for a
   cooling period, then the band relaxing back to symmetric, so the decision can be revisited
   on the merits. A permanent dead-band is a capture tool; a decaying one is a stabiliser.
2. **Over-damping is the self-lock again.** Damping plus hysteresis trade responsiveness for
   stability, and too much is exactly the sclerosis of [Part 4](#4--damping--the-control-theory-core-rate "How fast should law respond to opinion? Too fast and policy see-saws; too slow and nothing can be repaired. The right speed differs by area — the UK's flaw is one speed for everything."). So band-width and τ are
   **per-domain** (the subsidiarity of [Part 2](#2--order--partial-and-per-domain "“Better” is not one number. Two democracies can each beat the other in different ways, and better-in-trade-law is not better-in-family-law. There is no single best democracy, by design.") — narrow and fast for reversible policy, wide
   and slow for the constitutional core), and *who sets them* is itself a capture surface
   that must be declared and legible ([§6](https://glassontin.github.io/civic-kernel/#s6 "Nobody has to adopt all of it. Any group may take the parts it wants — but must publish, in a form anyone's phone can read, exactly what it left out.") of the architecture), or the dead-band becomes a
   silent instrument of whoever tuned it.

</details>

## 6 · Attractors

<details>
<summary><b>Plainly</b> <i>Each area of law settles toward its own good-enough frontier and stops. Rights are the floor the system must never sink through — not a summit it climbs toward.</i></summary>

Multiple, local, context-dependent. The dynamics does not converge to one Best Democracy; it
converges, per domain, toward the local Pareto frontier of the axes — the states where no axis can improve without another giving way — given that domain's
declared objective — then stops, and leaves incomparable choices (adopt proportional
representation? write a constitution?) to politics. The invariant [floor](../README.md#w-floor) — the [§1](https://glassontin.github.io/civic-kernel/#s1 "The job: keep producing decisions the losers still accept, while everyone — the operators included — has a reason to cheat.") goals and
the UDHR — is the operator's fixed constraint, never its target. Its scope is the [§5](https://glassontin.github.io/civic-kernel/#s5 "The rules can change — in stages, with expiry dates unless renewed. The one thing nearly impossible to change: each member's standing as a free and equal person.")–[§6](https://glassontin.github.io/civic-kernel/#s6 "Nobody has to adopt all of it. Any group may take the parts it wants — but must publish, in a form anyone's phone can read, exactly what it left out.")
settlement, stated exactly: inside a community subscribed to the full profile the floor is
near-consensus-locked; across the lattice a decrease is never *prevented* — the kernel has
no army — but always *witnessed*, a legible manifest-diff. **Never silently decreased** is
the enforceable form of the constraint.

</details>

## 7 · The safety property — what the math must never do

<details>
<summary><b>Plainly</b> <i>The rule above all the others: the maths may describe, steady, and illuminate; it may never decide what “better” means. People choose the direction — the model only makes the ground visible.</i></summary>

The most important section, and the reason this is not the technocratic optimizer of "good
governance" it superficially resembles.

> **The math may carry the representation, the dynamics, the damping, and the legibility.
> It may never carry the objective.**

An LLM works because it has a *given, cheap, objective loss* (next-token prediction) over a
*frozen* dataset. A polity has neither: **its loss is the contested political object
itself.** "EU-thoroughness is good for trade and bad for family law" is a reasonable value
judgment — but a *judgment*, a choice. Put that choice inside the optimizer and whoever set
it holds exactly the power the kernel exists to distribute. This is the failure mode with a
graveyard behind it (Cybersyn; "social physics"; every over-mathematized governance scheme).

So the objective is **exogenous**: declared per domain, per community, revisably, legibly —
which is to say it stays [§6](https://glassontin.github.io/civic-kernel/#s6 "Nobody has to adopt all of it. Any group may take the parts it wants — but must publish, in a form anyone's phone can read, exactly what it left out.") of the architecture. The operator's job is not to choose the
heading but to **make the local field visible and the uphill moves cheap, reversible, and
local**, so exit, comparison, and adoption do the moving. Gardener, not pilot.

**Floor, not telos.** The sharp objection is: *but the UDHR is already in the model — isn't
that an objective?* The distinction has to be exact. The UDHR enters as two legitimate things
— the **coordinate frame** (the 30-axis spine every state is measured against) and the
**floor** (the invariant never decreased, [Part 6](#6--attractors "Each area of law settles toward its own good-enough frontier and stops. Rights are the floor the system must never sink through — not a summit it climbs toward.")) — and never as a **telos**, a target to be
maximized. "Maximise match to the charter" fails twice over: it re-flattens the per-domain
partial order ([Part 2](#2--order--partial-and-per-domain "“Better” is not one number. Two democracies can each beat the other in different ways, and better-in-trade-law is not better-in-family-law. There is no single best democracy, by design.")) back into a scalar, and it is empirically wrong — the UK backs the
right at issue and still `breaks`; the win was remedy, not coverage. Above the floor there is
no summit to climb toward: "an agreed optimal human state" is the contested political object
itself, and asserting one hands whoever asserted it the capture-power the design exists to
distribute. The operator measures distance in this frame and holds the floor; it does not
optimise toward a maximum.

</details>

## 8 · Empirical status — solid specification, underdetermined predictor

<details>
<summary><b>Plainly</b> <i>The skeleton is sound; the numbers to run it do not exist. Five measured systems, one run of history, a model that changes what it measures: a research programme, not a trained system.</i></summary>

Elegance blurs two claims that must stay separate.

- **The structure is solid.** State tensor, partial order, subsidiarity vector field,
  control-theoretic damping, hysteresis — well-posed, and three of them (subsidiarity,
  control theory, hysteresis) are battle-tested elsewhere.
- **The coefficients are radically underdetermined.** A five-point, coarse, domain-agnostic
  corpus; **one non-i.i.d. sample path** of history (one run, each step leaning on the last — nothing like the independent draws learning needs); no way to backprop through counterfactual
  polities; and **reflexivity** — the model changes the thing it models, which no frozen
  training set does. Any scalar proxy for "better" becomes a Goodhart target the moment it is optimized — Goodhart's law: when a measure becomes a target, it ceases to be a good measure.

So this is a **model specification and a research program with a rigorous skeleton — not a
trained system**, and must not be presented as one. The empirical instrument we do have is
the [stress-test harness](../scenarios.html): expensive and sparse, but real — it evaluates a
*proposed* move rather than pretending to have learned the whole field.

</details>

## 9 · What "engineering it" means next

<details>
<summary><b>Plainly</b> <i>The buildable next steps, all with a human in the loop — richer measurement, declared preferences, declared speeds, and a hard no-autopilot rule. First test: walk the UK toward repair and watch where it jams.</i></summary>

The honest, buildable path — each step inside the [Part 7](#7--the-safety-property--what-the-math-must-never-do "The rule above all the others: the maths may describe, steady, and illuminate; it may never decide what “better” means. People choose the direction — the model only makes the ground visible.") safety property:

1. **Make the state multi-dimensional.** Index the corpus by policy-domain, not just
   jurisdiction: a trade-law regime and a family-law regime get their own coordinates. (Undo
   the flattening of [Part 1](#1--state "Where a democracy stands, written as numbers: for each community and each area of law, which rights are backed, what a court can do about a breach, on what terms, when the remedy can arrive, and what holds it in place. Five real systems are measured so far.").)
2. **Represent the objective as declared, per-domain preference** in the [manifest](../README.md#w-manifest) —
   subsidiarity as a schema field ("toward thorough/central" vs "toward simple/local"), never
   a global loss.
3. **Add the dynamics fields** the model needs and the [waist](../README.md#w-waist) lacks: per-domain damping
   (τ) and hysteresis (dead-band + decay), declared and legible, so a citizen can see how
   stable each of their community's domains is and why.
4. **Keep the harness as the evaluator** of any proposed move.
5. **Make the operator decision-support, human-in-the-loop:** it shows the local vector field
   and recommends dominated-improving or preference-aligned steps for approval, with
   control-theory tuning of per-domain damping. **Autopilot optimizing a global objective is
   excluded** — on safety and [§1](https://glassontin.github.io/civic-kernel/#s1 "The job: keep producing decisions the losers still accept, while everyone — the operators included — has a reason to cheat.") grounds both.

The first concrete proof would be the **UK trajectory**: from its measured coordinate
(`declaration / unconditional / 17-of-30 / breaks`) along the smallest individually-adoptable,
reversible moves, harness re-run at each step — expected, honestly, to *stall* at the remedy
step (the self-lock of [Part 4](#4--damping--the-control-theory-core-rate "How fast should law respond to opinion? Too fast and policy see-saws; too slow and nothing can be repaired. The right speed differs by area — the UK's flaw is one speed for everything.") above), which is the interesting result.

</details>
