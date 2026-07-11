# The Civic Kernel

[![test](https://github.com/GlassOnTin/civic-kernel/actions/workflows/test.yml/badge.svg)](https://github.com/GlassOnTin/civic-kernel/actions/workflows/test.yml)

**Rules for running a vote that nobody can rig and anybody can check — too small for
anyone to own.**

Technically: a thin, capture-resistant protocol for democratic decision-making —
fourteen threats, four services, four verbs, two message formats, one floor, twelve
refusals. The floor is the Universal Declaration of Human Rights, measured rather than
recited. The whole core fits on one page: [`KERNEL.md`](KERNEL.md).

## What's here for you

- **You want to know what you are owed.**
  [What are you owed? →](https://glassontin.github.io/civic-kernel/owed.html)
  Pension Credit, Attendance Allowance and what they open — worked out on your device,
  from rules that cite the law they encode, with nothing sent anywhere. Change an
  answer and watch the amounts move. An estimated £24 billion of support goes
  unclaimed in Great Britain each year; find out if some of it is yours, without
  telling anyone you asked.
- **You have a vote coming — a club, a co-op, a society.** Run a shadow ballot beside
  the show of hands: members cast sealed ballots from their phones, the hands still
  decide, and afterwards anyone can check from the published record that nobody could
  have rigged it. [The invitation a committee receives](docs/shadow-agm-invitation.md)
  says what it would look like, honest limits included; the committee's runbook is
  [`proto/README.md`](proto/README.md).
- **You'd rather check than believe.**
  [Check the election in your browser →](https://glassontin.github.io/civic-kernel/verifier.html)
  No install. Every check runs on your machine, against the committed election
  transcript or any transcript you drop on the page. Look up a ballot by its tag.
- **You want to try it.**
  [Cast a ballot of your own →](https://glassontin.github.io/civic-kernel/cast.html)
  The voter's side, in the browser: generate an enrolment secret, seal a choice,
  challenge the device that sealed it, build the anonymous ballot file — then
  [hand it in on the verifier page](https://glassontin.github.io/civic-kernel/verifier.html#handpanel)
  and watch the count move, no committee needed. What the pages build and count, the
  independent Python verifier must accept and match — CI holds them to that.
- **A club asked you to witness its election.**
  [The witness page →](https://glassontin.github.io/civic-kernel/witness.html)
  Your five minutes, in the browser: co-sign the club's checkpoint only if the history
  you are shown extends the history you remember — that is what stops a rewrite. One
  small file holds your key and your memory, and the command-line witness reads the
  same file.
- **You met a word.** *Receipt-free*, *ring signature*, *linking tag* —
  [every term in this repo, one plain line each](#the-words-in-plain-speech).
- **You want to know where your rights stand.**
  [The same 30 rights across the UK, Germany, the US, the EU Charter, and the PRC →](https://glassontin.github.io/civic-kernel/scenarios.html#corpus)
- **You want the argument.**
  [The architecture →](https://glassontin.github.io/civic-kernel/)
  Democracy restated as an engineering problem, and the smallest honest answer to it.
  Every section opens as one plain line; expand for the full argument. Then watch
  [real life run against the protocol →](https://glassontin.github.io/civic-kernel/scenarios.html)
  — 24 stress-test stories, each machine-validated against the schemas.

Or run everything locally — the election, its verification, and twelve attempts to rig
it — in about a minute: [`proto/test.sh`](proto/).

## What it is

The claim: **anyone can check the process that governs them, from the published record
alone.** No trust in the server. No trust in the committee. No trust in the software
that produced the record.

The running prototype is a sixty-member allotment society electing its treasurer.
Every ballot is anonymous, yet provably cast by an enrolled member. No ballot is ever
opened: ballots are added up while still encrypted, and only that sum is decrypted. An
independent verifier — sharing no code with the election software — confirms the
result from the published files alone. Then it catches all twelve of the ways we tried
to rig it, up to a committee and both witnesses colluding to rewrite history, and
finally to erase one inconvenient ballot from it. When everything holds, the
verifier's closing line is: *"nobody had to trust the shed."*

Who it's for: the member who can see her own ballot counted without anyone learning
her vote. The club or co-op whose election nobody can rig. One day — the long game —
the household that learns what it is owed without telling anyone it asked.

Today it is a research prototype at village scale, and it says so. Every deployment
publishes a machine-readable manifest of what it upholds **and what it leaves out** —
weakness is permitted; hiding it is not.

## What it is not

Not a product, not a platform, not a blockchain — no token in any citizen's path,
ever. And not finished, by design: this repo treats its own documents the way the
kernel treats law. The architecture essay is at rev. 4 because evidence already
revised it three times — most recently with what the prototype proved — and what the
first real communities teach will revise it again.

## Next

A shadow-mode run alongside one real club's AGM, with the official result still decided
by the show of hands. Every part now exists — `cast.html` for the voter,
[`witness.html`](https://glassontin.github.io/civic-kernel/witness.html) for the
neighbouring societies (the same witness as `clubvote.py witness`: one file, either
tool), `issuer` for the club register, `trustee` for the key-holders, `anchor` for the
newspaper, and `clubvote.py agm` for a committee left holding exactly one key, the
log's: it publishes, gates and assembles, and can vouch for nothing by itself (the
runbook is in [`proto/README.md`](proto/README.md)). What remains is not code: a real
club, a real season, and what it teaches. The invitation a club actually receives is
drafted, in the open, honest limits included:
[`docs/shadow-agm-invitation.md`](docs/shadow-agm-invitation.md).

And behind it, the wedge the essay itself calls the bigger want — *find out what you
are owed, without telling anyone you asked*. The club vote is the entry point; it
proves the machinery on a group's count, but it borrows its members' standing from
the club register rather than giving anyone new standing. The first rung of the
bigger wedge now runs:
[`owed.html`](https://glassontin.github.io/civic-kernel/owed.html) works out Pension
Credit, Attendance Allowance and what they open, on your device, every question
citing its rule, held to an independent judge in CI — implementing
[`docs/wedge-one-v0.md`](docs/wedge-one-v0.md), which was drafted success-test-first
and remains the plan of record. Next on that road: more corpus (Housing Benefit,
Winter Fuel), the circumstances file, and — when the attestation ecosystem ships —
proving without revealing.

## The words, in plain speech

Every term of art in this repo, one line each. Jargon elsewhere in these documents
links back to this list.

- <a id="w-transparency-log"></a>**Transparency log** — the public record: append-only,
  each entry hash-chained to the one before, so changing yesterday breaks every copy
  of today.
- <a id="w-witness"></a>**Witness** — an independent party that co-signs the log's
  published fingerprints (its *heads*); rewriting history means getting every witness
  to re-sign the lie.
- <a id="w-anchor"></a>**Anchor** — a copy of the log's closing fingerprint lodged
  beyond everyone who signs things (think a newspaper's public notices), so history
  cannot quietly shorten after the close.
- <a id="w-manifest"></a>**Manifest** — a deployment's signed, machine-readable
  declaration of what it upholds and what it leaves out.
- <a id="w-subtraction"></a>**Subtraction** — anything in the full design a deployment
  doesn't do. Allowed — but only out loud, in the manifest.
- <a id="w-waist"></a>**The waist** — the narrow middle of the hourglass, in the sense
  the internet has one (the IP packet): the two formats every deployment must share
  (a log entry and a manifest), kept deliberately thin so anything can be compared
  with anything.
- <a id="w-lattice"></a>**The lattice** — the ladder of honest partial versions: the
  full design at the top, every weaker deployment below it, each manifest saying
  exactly where on the ladder it sits.
- <a id="w-ring-signature"></a>**Ring signature** — proof that *some member of a
  published list* signed, without revealing which one. How a ballot proves
  eligibility without a name.
- <a id="w-linking-tag"></a>**Linking tag** (the literature says *nullifier*) — a
  per-election tag derived from the voter's secret: vote twice and the tags match, so
  double votes show — but names never do. Also how you find your own ballot in the
  public box.
- <a id="w-zero-knowledge"></a>**Zero-knowledge proof** — a proof that a statement is
  true which reveals nothing beyond that: the system learns you are on the roster,
  never which name you are.
- <a id="w-homomorphic-tally"></a>**Homomorphic tally** — ballots are added up while
  still encrypted; only the total is ever decrypted, never a ballot.
- <a id="w-receipt-free"></a>**Receipt-free** — you can check that your vote counted,
  but you cannot prove to anyone else how you voted. Nothing to sell; nothing a
  coercer can demand afterwards.
- <a id="w-cast-or-audit"></a>**Cast-or-audit** — before casting, you may challenge
  the device to open the encryption it just made. A cheating device cannot tell a
  test from a real cast, so cheating gets caught.
- <a id="w-risk-limiting-audit"></a>**Risk-limiting audit** — hand-count enough
  randomly chosen paper ballots to confirm the announced winner — or, failing that,
  force a full recount.
- <a id="w-sortition"></a>**Sortition** — choosing decision-makers by lottery, the way
  juries are chosen: a random, representative panel of citizens deliberates on behalf
  of everyone.
- <a id="w-sybil"></a>**Sybil attack** — one person pretending to be many people, to
  multiply their voice. *Sybil resistance* is how hard the system makes that.
- <a id="w-floor"></a>**The floor** — the thirty rights of the Universal Declaration
  of Human Rights, treated as constraints no decision may cross, whatever its
  majority.

## Layout

- **`KERNEL.md`** — the distilled normative core: goals, threats, services, verbs,
  waist, refusals, measured status.
- **`index.html`** — the architecture document.
- **`proto/`** — the first running code: the club-vote election end to end (all four
  verbs, real signatures, real Merkle log, independent verifier, committed reference
  transcript). `proto/test.sh` is the success test.
- **`verifier.html`** + **`verifier.js`** — the same checks in the browser: load or
  drop a transcript, watch every check run, look up a ballot by its linking tag — and,
  on the demo election only, hand in a ballot and watch the count move (the demo
  publishes its unsealing secret; a real election's page can judge, never count). The
  engine is held to `proto/verify.py`'s verdicts by `tools/verify-parity.mjs` and
  `tools/collect-parity.mjs`, which CI runs; its standards (the ballot group, the two
  schemas) are pinned inside the file, never fetched.
- **`cast.html`** + **`cast.js`** — the voter's side in the browser: generate an
  enrolment secret (it never leaves the device; the issuer certifies only the public
  key), seal a choice, challenge the device before casting (Benaloh), sign the ballot
  over the roster ring. `tools/cast-parity.mjs` (CI) asserts a page-built ballot,
  fed through `clubvote.py collect`, is accepted by `verify.py` — and moves the tally.
- **`owed.html`** + **`owed.js`** — wedge one, v0: what you are owed, computed on
  your device. The form is generated from the rules corpus, so a question that cannot
  cite its authorizing rule cannot exist; the answer is a claim-trace — every step
  with its rule, what was demanded, what was deliberately not asked. No network API
  exists in the page or its engine, asserted in CI.
- **`entitlements/`** — the rules corpus behind it: `rules.schema.json` (the record
  format), `uk/` (Pension Credit Guarantee Credit, Attendance Allowance, the over-75
  TV licence, a Council Tax Reduction signpost — and the statutory pensionable-age
  table as data), `personas/` (13 hand-checked households, sources dated), and
  `judge.py`, the independent second engine. `tools/owed-parity.mjs` (CI) holds the
  page and the judge to identical claim-traces over the battery.
- **`witness.html`** + **`witness.js`** — the witnessing society's side in the
  browser: make a witness key, pin whom you watch (the ceremony — the log key arrives
  out of band, never from a request), co-sign checkpoints, and refuse any history that
  does not extend the one your memory pins. Interchangeable with `clubvote.py witness`
  — same witness file, same card, same co-signature, same refusals —
  `tools/witness-parity.mjs` (CI) proves it across a whole election, alternating the
  file between the two implementations.
- **`docs/`** — the functional (dynamics) model and the UK-trajectory worked example.
- **`schema/`** — the waist: the two universal formats, as JSON Schema (Draft 2020-12).
  - `log-entry.schema.json` — one transparency-log event (includes the `coercive.act`
    type, whose body must cite its authorizing rule).
  - `manifest.schema.json` — a community's conformance manifest: which services and
    which of the 30 UDHR invariants it upholds, its `decisions.coercion_resistance`,
    and its `rights_guard.remedy`.
- **`scenarios/`** — imagined human situations, each walked through the four verbs.
  Every embedded manifest and log entry is validated against the waist schemas, and
  every scenario must cite documented real-world precedents for its attack pattern
  (a required `precedents` field, 46 citations verified July 2026).
  `scenario.schema.json` is the record format.
- **`corpus/`** — real legal systems captured under the same schema, sharing the
  30-invariant spine:
  - `uk/` — Human Rights Act 1998 (via legislation.gov.uk) + real Commons divisions
    as `decision.closed` entries.
  - `de/` — Grundgesetz (via gesetze-im-internet.de).
  - `us/` — US Constitution and Bill of Rights.
  - `eu/` — EU Charter of Fundamental Rights (scope conditional under Art 51).
- **`scenarios.html`** — a self-contained browsable site rendering the scenarios and
  the comparative corpus. Data is inlined, so it serves as static files (GitHub
  Pages-ready); no runtime network calls.
- **`tools/`** — validators that also rebuild the inlined data in `scenarios.html`.

## Build / validate

Requires Python 3 and `jsonschema`:

```sh
pip install -r requirements.txt
python tools/validate.py         # validate scenarios; rebuild scenario-data in scenarios.html
python tools/validate-corpus.py  # validate corpus;    rebuild corpus-data in scenarios.html
```

Both exit non-zero on any validation failure. The site is pre-built (data already
inlined), so it deploys without running these — running them is how you regenerate it
after editing a scenario or corpus file.

## Honest caveats

- The scenarios are **fiction anchored to fact**. The people and places are invented;
  every attack pattern cites documented real-world precedents (each checked against
  its source when added, July 2026). They are plausibility tests of the architecture,
  not records of real events, and the verdicts (`holds` / `strains` / `breaks`) are
  the harness's reading of the architecture document's own claims and limits — not
  endorsements.
- The comparative rights-map is **coarse**: UDHR articles mapped to domestic
  constitutional provisions from public legal sources. It points to where systems
  differ. It is not legal advice or authoritative comparative-law scholarship, and
  some cells are debatable.
- `proto/` is the first and only running code: a deliberately minimal four-verb loop
  whose manifest declares its own subtractions — see [`proto/README.md`](proto/README.md)
  for the list, including the one that matters most: the anonymity set is the roster
  and the proof is linear in it, which is a village, not a nation. Everything else is
  specification, test suite, and corpus; signatures inside the *scenarios'* embedded
  artifacts remain placeholders.

## License

See [`LICENSE`](LICENSE).
