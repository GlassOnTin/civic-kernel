# Owed, v0 — the wedge-one plan

**What this page is for:** the build plan for the first rung of
[§15](https://glassontin.github.io/civic-kernel/#s15 "Nobody installs an app out of civic virtue. Two things people already want: money they are owed and cannot find, and a club vote nobody can rig.")'s
wedge one — a page that tells you what you are owed, computed on your device,
where every question cites the rule that lets it ask. Drafted before the code,
like everything here: the success test first, the subtractions declared up front.

**Status (2026-07-12): built.** [`owed.html`](https://glassontin.github.io/civic-kernel/owed.html)
implements this plan; `entitlements/` is the corpus; the done-bar below runs in CI as
test.sh's `owedpage` job. This document remains the plan of record for what v0 is and
is not.

The sentence the page must earn: **find out what you are owed, without telling
anyone you asked.** In Great Britain an estimated £24 billion of income-related
support goes unclaimed each year — over seven million households missing at
least one entitlement — for the reasons
[§8](https://glassontin.github.io/civic-kernel/#s8 "Paperwork can quietly take a right away. So: four verbs, nowhere to hide an extra step, and every demanded field must name the rule that lets it ask.")
names: opacity, complexity, stigma. The club vote proves the machinery on a
group's count; this is the first artifact about a *person's standing* — and per
[§11](https://glassontin.github.io/civic-kernel/#s11 "The machinery that runs a vote can run a benefit claim: your phone works out what you are owed, proves it without handing over your life, and any refusal must show its working.")
they are the same primitives pointed at a different subject.

## What v0 is

[§11](https://glassontin.github.io/civic-kernel/#s11 "The machinery that runs a vote can run a benefit claim: your phone works out what you are owed, proves it without handing over your life, and any refusal must show its working.")'s
worked example, with everything unshipped subtracted. It keeps four of the
essay's claims and makes them run:

1. **The rules exist as code before any claim.** A small rules corpus, each
   rule carrying its citation into legislation.gov.uk. No secret decision
   tree: the corpus is the page's whole logic, and anyone can run it.
2. **Discovery happens on the citizen's device.** A static page, like the
   verifier: no account, no server, no network request after load. The state —
   and this repo — never sees a speculative query.
3. **The form is generated from the rules.** A question that cannot cite the
   rule demanding it *cannot exist on the page*, because the page builds its
   questions from the corpus — T12 enforced by construction, not review.
4. **The answer is a trace, not a verdict.** Which rules fired, which
   threshold bound, what was asked and under what authority — a
   machine-readable *why* you can carry into a real claim, plus the list of
   things a real claim demands that this page deliberately did not ask.

And one thing §11 calls quietly radical, which costs nothing once the engine
is local: **simulation**. Change one answer — "if my savings were £2,000
less…", "if I claimed Attendance Allowance first…" — and watch the award move,
on-device, invisible to everyone.

## Scope: three entitlements, three kinds

Chosen so that each demonstrates a different honesty the corpus schema must
support, and all three chain into one story:

- **Pension Credit (Guarantee Credit)** — `kind: computable`. The
  famously unclaimed one. Means-tested arithmetic: qualifying age, income
  aggregation, tariff income from capital, severe-disability and carer
  additions. State Pension Credit Act 2002 and the SPC Regulations 2002, rates
  pinned to a named tax year by citation of that year's uprating order.
- **Attendance Allowance** — `kind: assessment-gated`. Not means-tested;
  age and care-needs based (SSCBA 1992 ss. 64–67). The computable parts
  compute; the care-needs judgment is a human decision-maker's, and the page
  says so instead of pretending — the
  [§9](https://glassontin.github.io/civic-kernel/#s9 "The defences watch at machine speed but act only at the speed of law. AI gets a microscope, never a pen — and emergency powers expire on their own.")
  discipline at citizen scale: the tool gets a microscope, never the pen.
  Output: "likely eligible, subject to assessment — here is the trace of what
  *is* computable, and what the assessor will judge."
- **Free over-75 TV licence** — `kind: passported`. Trivial on purpose:
  75+ *and* Pension Credit. It exists to make the graph visible — one
  entitlement unlocking another is the shape of the whole domain, and the
  page should render the chain ("Pension Credit would also passport you
  to…").

Named but out of scope, so the schema is honest about them from day one:
**Council Tax Reduction** (`kind: local` — every authority its own scheme;
v0 says so and links the citizen's council rather than guessing) and **Winter
Fuel Payment** (passported, but its rules have moved twice in two years —
a volatility the corpus's tax-year pinning is designed for, and a reason to
add it second, not first). Scotland's replacement of Attendance Allowance
(Pension Age Disability Payment) is declared as a jurisdiction caveat:
v0 is England-and-Wales-first and says so.

## The corpus

New directory `entitlements/`:

- `rules.schema.json` — the record format. Every rule:
  `{id, entitlement, kind, citation, uri, effective: {tax_year, uprating_order},
  demands: [fields], logic, text_digest}`. `kind` is the honesty enum:
  `computable | assessment-gated | passported | local`.
- `uk/…` — the rules themselves, one file per entitlement.
- `personas/` — the test battery: ~10 committed households with expected
  outcomes, each hand-checked at authoring time against the official
  calculator and the Age UK / Citizens Advice guidance, with the check dated
  and cited — the same discipline as the scenarios' 46 verified precedents.
- `judge.py` — the independent second engine (below).

Provenance is pinned, not trusted: each rule carries its legislation.gov.uk
URI and a digest of the section text it encodes, fetched at authoring time.
Rates never float free — they cite the uprating order for a named tax year,
the corpus declares that year, and the page shows it ("rates: 2026–27") with
a staleness warning once the year turns.

## The trace

A new small format, versioned like everything else — `claim-trace/v0`:

```json
{
  "v": "civic-kernel/claim-trace/v0",
  "corpus": { "tax_year": "2026-27", "digest": "sha256:…" },
  "entitlement": "pension-credit-guarantee",
  "verdict": "eligible",
  "weekly": "…",
  "demanded": [
    { "field": "capital_total",
      "rule": "SPC Regs 2002, reg 15 (tariff income)",
      "uri": "https://www.legislation.gov.uk/uksi/2002/1792/regulation/15" }
  ],
  "steps": [ { "rule": "…", "bound": "…", "result": "…" } ],
  "not_asked": [ "name", "national insurance number", "address", "bank details" ]
}
```

`not_asked` is the kernel talking: the trace declares what it refused to
demand. The human rendering reads as a letter you could take to the claim
line: *what you told it, what rule asked, what fired, what it concluded.*

Deliberately **not** a waist artifact. The waist carries a community's log
entries and manifests; this is a tool's output about one person, published
nowhere. If institutions ever consume claim-traces, waist candidacy is that
day's decision — the format is versioned so that day has something to point
at.

## Privacy, said plainly

Same shape as the verifier, same sentence on the page: nothing you type is
sent anywhere; no network request after the page loads; works saved to disk
and opened offline; no query parameters, ever; nothing is stored unless you
download the trace. What it cannot hide, listed on the page: that your
browser fetched the page once (save it and it can't even see that), your
browser history, and a shoulder. The claim it must never make: anonymity.
The claim it makes: **no speculative query ever leaves the device.**

## The done-bar, before any code

The success test is written first, in the house pattern:

1. **Two engines, one corpus.** `owed.js` (the page's engine, browser + Node)
   and `entitlements/judge.py` (independent, shares no code). A new test.sh
   job runs both over the persona battery: same verdicts, same weekly
   amounts, same demanded-fields lists, or red.
2. **The form is the corpus.** A validator asserts the page's rendered
   questions are exactly the union of `demands` across the corpus — a field
   with no citation cannot appear, a citation with no field is dead weight.
   Generated, never trusted.
3. **No network after load.** The existing headless-harness pattern asserts
   the page makes zero requests after initial load while a full computation
   runs.
4. **Persona parity with the real world.** The battery's expected outcomes
   are hand-checked against the official calculator at authoring, dated, and
   re-checked when the corpus's tax year changes — the check is a documented
   ritual, like the precedent citations.
5. **Staleness is loud.** CI fails if the corpus tax year is older than the
   current one at build time without an explicit `stale-acknowledged` note.

## What v0 is not, declared

- **Not advice, not a decision.** The decision is DWP's; the page routes you
  to the claim line and Citizens Advice / Age UK, and its verdict vocabulary
  says "appears" out loud.
- **No credentials, no wallet, no submission.** Inputs are self-declared and
  vanish on tab close; §11's attestation ecosystem is the named unbuilt
  dependency, and v0 does not pretend at it.
- **No pseudonyms, no log, no proofs.** Nothing is claimed, so nothing needs
  proving or witnessing. The kernel content of v0 is the rules-with-authority
  discipline and the trace — SVC-3's habits, not its machinery.
- **England and Wales first,** one tax year at a time, three entitlements —
  a corpus that a person can read in an afternoon, because auditability of
  the rules *is* the product.

And [§15](https://glassontin.github.io/civic-kernel/#s15 "Nobody installs an app out of civic virtue. Two things people already want: money they are owed and cannot find, and a club vote nobody can rig.")'s
own tension, restated so it binds this plan: the page is a reference
implementation of a corpus anyone can run, never *the* door. The corpus is
the product; the page is one client of it; both are abandonable by design.

## The ladder up (not v0)

- **v1 — the circumstances file.** Your answers as a small file you keep and
  re-drop (the witness.json pattern: a file, not an account), so re-checking
  after a rule change is one drop. This is the first personhood artifact: a
  person's own portable state.
- **v2 — attestations, when the ecosystem ships.** Real issuers (council,
  GP, employer) replacing self-declaration field by field; prove-without-
  revealing arrives here, not before.
- **The bridge from wedge two:** the club credential's second use. A season's
  enrolment secret that can also hold an attestation is the moment the two
  wedges become one wallet — personhood arriving, as §15 says it must, as a
  side effect and never as an ask.

## Naming

`owed.html` + `owed.js` at the repo root, beside the election pages —
"find out what you are owed" is the whole interface. Provisional, like
everything in a v0.
