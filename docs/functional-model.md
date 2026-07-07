# The Civic Kernel as a Functional Operator

**Status: v0, exploratory — a speculative companion to the deployed thesis.** The
deployed argument is [`index.html`](../index.html); the distilled statement of both is
[`KERNEL.md`](../KERNEL.md). This document writes down, as precisely as honesty
allows, what it would mean to treat the Civic Kernel not only as a thin service core but
as a *mathematical operator* that maps a starting democracy toward an empirically
more-likely-better one — and, just as important, exactly where that model is solid and
where it is underdetermined.

*(Throughout, **§N** refers to a section of the architecture essay; **Part N** to a section
of this document.)*

## 0 · Two senses of "kernel"

The architecture uses *kernel* in the operating-systems sense: a thin, boring, invariant
core (four services, one waist). This document uses it in a second, mathematical sense:
an operator on the space of possible democracies. The claim is that **the first generates
the second** — the thin core supplies a state space, an order, a set of legal transitions,
and an invariant floor, and the induced dynamics *is* the operator. The pun is
load-bearing, not decorative.

## 1 · State

A polity's configuration is a tensor **S** indexed by **(community × policy-domain × axis)**:

- **community** — the fractal units of §6 (household … nation), nesting.
- **policy-domain** — trade, family, criminal, environmental, … . *This index is the key
  upgrade.* The earlier sketch flattened it, and flattening is what makes "the EU is good
  for X" a category error: good configurations are domain-relative.
- **axis** — the measurable dimensions of a rights/decision regime. So far: **coverage**
  (which of the 30 UDHR invariants are backed), **remedy** (none / declaration / escalate /
  strike), **scope** (unconditional / conditional), and — extending — **interaction-cost /
  sludge** (§8), **inclusion** (§4), **capture-resistance** (§1).

We have **S** measured at four real coordinates (UK, US, Germany, EU) on the rights axes —
coarsely, and domain-agnostically. Four points in a high-dimensional space: enough to see
structure, nowhere near enough to fit dynamics (see Part 8).

## 2 · Order — partial, and per-domain

"Better" is not a scalar.

- **Partial, not total.** On the axes, states form a partial order — the §6 *lattice*,
  literally. A state dominates another only if it is ≥ on every axis. The UK (higher
  coverage, weak remedy) and the US (lower coverage, strike) are **incomparable**; there is
  no global ranking, by design.
- **Domain-relative.** The improvement direction in trade-law space is not the improvement
  direction in family-law space. This is not a wrinkle to smooth away — it is the
  **principle of subsidiarity** (TEU Art 5: act centrally only where the objective is
  better achieved there), expressed as geometry. The operator therefore has **one attractor
  per domain**, never one global optimum.

## 3 · The operator — a subsidiarity vector field

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
is the entire safety property (Part 7), and the load-bearing difference between this model
and a technocracy.

## 4 · Damping — the control-theory core (rate)

A polity is a feedback loop: preference − state → error → institutions → law → society →
sensors (elections, press, the harness) → back. Institutional friction — supermajorities,
deliberation windows, parliamentary sovereignty — is a **damping coefficient**.

- **Under-damped:** policy oscillates (repeal-and-replace every cycle).
- **Over-damped:** sclerosis — the UK self-lock, where the rights remedy cannot be
  strengthened because that requires the sovereign to bind itself.
- **Critically damped:** the fastest response that does not overshoot — exactly "**as
  quickly as possible, or as slowly as needed**."

Good damping is **domain-specific**: heavy on the constitutional core (§5's near-consensus
pin), light on reversible policy. The UK's pathology is *uniform* damping — parliamentary
sovereignty damps everything equally, so it over-damps rights-repair while under-damping
ordinary law. §5's layered amendment speeds are this field in embryo; the model generalizes
it to a tunable damping tensor and hands it the standard tools of control theory (stability,
phase margin, pole placement) as the language for tuning it.

Damping governs *how fast* the state moves. It does nothing to stop a system flipping back
and forth across a threshold — a distinct failure that needs a distinct tool (Part 5).

## 5 · Hysteresis, continuous voting, and the oscillation attack

**Hysteresis** is a dead-band with memory: the threshold to reverse a decision differs from
the threshold that made it, so the state holds against noise near the margin. The canonical
device is the **Schmitt trigger** — flip *out* at 55%, flip *back* only at 55% the other
way; in the 45–55% band, nothing moves. It changes not *how fast* you flip but *whether you
flip at all* near the boundary, and it is the piece the kernel lacks for decisions that are
cheap to vote on but expensive to actuate. (Version control already uses it: a change
matures on a branch — an isolated dead-band — before it may touch the shared trunk.
Branch-then-merge is hysteresis for a codebase; a force-push that rewrites the trunk is the
T8 record-tampering attack, and the distributed clones that would detect it are §3.4's
witnesses. The tool we build the kernel with is a working miniature of it.)

**The mechanism: continuous vote, debounced actuator.** Split the system in two.

- The **setpoint** P(t) is the electorate's preference, held *continuously and
  always-current* — any citizen may change their vote at any moment. This is not new: it is
  the `recast_policy` "any later ballot supersedes an earlier one" already in the decisions
  service (§3.2), the same continuity that gives the coerced voter her escape. It must stay
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
no-token-in-the-citizen's-path red line (§6) holds; stability is bought with cooling-off and
supermajority-to-reverse, not gas.

**Two dangers, because hysteresis cuts both ways.**

1. **The one-way ratchet.** The stickiness that stops oscillation also entrenches a *first*
   change: an actor who flips something *once* then shelters behind the hysteresis meant to
   prevent oscillation, which now protects *their* change from being undone. Anti-oscillation
   silently becomes pro-incumbent-change. So **hysteresis must decay** — stickier for a
   cooling period, then the band relaxing back to symmetric, so the decision can be revisited
   on the merits. A permanent dead-band is a capture tool; a decaying one is a stabiliser.
2. **Over-damping is the self-lock again.** Damping plus hysteresis trade responsiveness for
   stability, and too much is exactly the sclerosis of Part 4. So band-width and τ are
   **per-domain** (the subsidiarity of Part 2 — narrow and fast for reversible policy, wide
   and slow for the constitutional core), and *who sets them* is itself a capture surface
   that must be declared and legible (§6 of the architecture), or the dead-band becomes a
   silent instrument of whoever tuned it.

## 6 · Attractors

Multiple, local, context-dependent. The dynamics does not converge to one Best Democracy; it
converges, per domain, toward the local Pareto frontier of the axes given that domain's
declared objective — then stops, and leaves incomparable choices (adopt proportional
representation? write a constitution?) to politics. The invariant floor — the §1 goals and
the UDHR — is never decreased: it is the operator's fixed constraint, not its target.

## 7 · The safety property — what the math must never do

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
which is to say it stays §6 of the architecture. The operator's job is not to choose the
heading but to **make the local field visible and the uphill moves cheap, reversible, and
local**, so exit, comparison, and adoption do the moving. Gardener, not pilot.

**Floor, not telos.** The sharp objection is: *but the UDHR is already in the model — isn't
that an objective?* The distinction has to be exact. The UDHR enters as two legitimate things
— the **coordinate frame** (the 30-axis spine every state is measured against) and the
**floor** (the invariant never decreased, Part 6) — and never as a **telos**, a target to be
maximized. "Maximise match to the charter" fails twice over: it re-flattens the per-domain
partial order (Part 2) back into a scalar, and it is empirically wrong — the UK backs the
right at issue and still `breaks`; the win was remedy, not coverage. Above the floor there is
no summit to climb toward: "an agreed optimal human state" is the contested political object
itself, and asserting one hands whoever asserted it the capture-power the design exists to
distribute. The operator measures distance in this frame and holds the floor; it does not
optimise toward a maximum.

## 8 · Empirical status — solid specification, underdetermined predictor

Elegance blurs two claims that must stay separate.

- **The structure is solid.** State tensor, partial order, subsidiarity vector field,
  control-theoretic damping, hysteresis — well-posed, and three of them (subsidiarity,
  control theory, hysteresis) are battle-tested elsewhere.
- **The coefficients are radically underdetermined.** A four-point, coarse, domain-agnostic
  corpus; **one non-i.i.d. sample path** of history; no way to backprop through counterfactual
  polities; and **reflexivity** — the model changes the thing it models, which no frozen
  training set does. Any scalar proxy for "better" becomes a Goodhart target the moment it is
  optimized.

So this is a **model specification and a research program with a rigorous skeleton — not a
trained system**, and must not be presented as one. The empirical instrument we do have is
the [stress-test harness](../scenarios.html): expensive and sparse, but real — it evaluates a
*proposed* move rather than pretending to have learned the whole field.

## 9 · What "engineering it" means next

The honest, buildable path — each step inside the Part 7 safety property:

1. **Make the state multi-dimensional.** Index the corpus by policy-domain, not just
   jurisdiction: a trade-law regime and a family-law regime get their own coordinates. (Undo
   the flattening of Part 1.)
2. **Represent the objective as declared, per-domain preference** in the manifest —
   subsidiarity as a schema field ("toward thorough/central" vs "toward simple/local"), never
   a global loss.
3. **Add the dynamics fields** the model needs and the waist lacks: per-domain damping
   (τ) and hysteresis (dead-band + decay), declared and legible, so a citizen can see how
   stable each of their community's domains is and why.
4. **Keep the harness as the evaluator** of any proposed move.
5. **Make the operator decision-support, human-in-the-loop:** it shows the local vector field
   and recommends dominated-improving or preference-aligned steps for approval, with
   control-theory tuning of per-domain damping. **Autopilot optimizing a global objective is
   excluded** — on safety and §1 grounds both.

The first concrete proof would be the **UK trajectory**: from its measured coordinate
(`declaration / unconditional / 17-of-30 / breaks`) along the smallest individually-adoptable,
reversible moves, harness re-run at each step — expected, honestly, to *stall* at the remedy
step (the self-lock of Part 4 above), which is the interesting result.
