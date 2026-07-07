# The Civic Kernel as a Functional Operator

**Status: v0, exploratory — on the `dynamic-kernel-model` branch, not the deployed
thesis.** The deployed argument is [`index.html`](../index.html); this is a separate,
speculative model kept off `master` on purpose. It writes down, as precisely as honesty
allows, what it would mean to treat the Civic Kernel not only as a thin service core but
as a *mathematical operator* that maps a starting democracy toward an empirically
more-likely-better one — and, just as important, exactly where that model is solid and
where it is underdetermined.

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
structure, nowhere near enough to fit dynamics (see §7).

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
is the entire safety property (§6), and the load-bearing difference between this model and a
technocracy.

## 4 · Damping and rate — the control-theory core

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

## 5 · Attractors

Multiple, local, context-dependent. The dynamics does not converge to one Best Democracy; it
converges, per domain, toward the local Pareto frontier of the axes given that domain's
declared objective — then stops, and leaves incomparable choices (adopt proportional
representation? write a constitution?) to politics. The invariant floor — the §1 goals and
the UDHR — is never decreased: it is the operator's fixed constraint, not its target.

## 6 · The safety property — what the math must never do

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

## 7 · Empirical status — solid specification, underdetermined predictor

Elegance blurs two claims that must stay separate.

- **The structure is solid.** State tensor, partial order, subsidiarity vector field,
  control-theoretic damping, local attractors — well-posed, and two of them (subsidiarity,
  control theory) are battle-tested elsewhere.
- **The coefficients are radically underdetermined.** A four-point, coarse, domain-agnostic
  corpus; **one non-i.i.d. sample path** of history; no way to backprop through counterfactual
  polities; and **reflexivity** — the model changes the thing it models, which no frozen
  training set does. Any scalar proxy for "better" becomes a Goodhart target the moment it is
  optimized.

So this is a **model specification and a research program with a rigorous skeleton — not a
trained system**, and must not be presented as one. The empirical instrument we do have is
the [stress-test harness](../scenarios.html): expensive and sparse, but real — it evaluates a
*proposed* move rather than pretending to have learned the whole field.

## 8 · What "engineering it" means next

The honest, buildable path — each step inside the §6 safety property:

1. **Make the state multi-dimensional.** Index the corpus by policy-domain, not just
   jurisdiction: a trade-law regime and a family-law regime get their own coordinates. (Undo
   the flattening of §1.)
2. **Represent the objective as declared, per-domain preference** in the manifest —
   subsidiarity as a schema field ("toward thorough/central" vs "toward simple/local"), never
   a global loss.
3. **Keep the harness as the evaluator** of any proposed move.
4. **Make the operator decision-support, human-in-the-loop:** it shows the local vector field
   and recommends dominated-improving or preference-aligned steps for approval, with
   control-theory tuning of per-domain damping. **Autopilot optimizing a global objective is
   excluded** — on safety and §1 grounds both.

The first concrete proof would be the **UK trajectory**: from its measured coordinate
(`declaration / unconditional / 17-of-30 / breaks`) along the smallest individually-adoptable,
reversible moves, harness re-run at each step — expected, honestly, to *stall* at the remedy
step (the self-lock of §4 above), which is the interesting result.
