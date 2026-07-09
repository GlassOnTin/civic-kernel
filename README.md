# The Civic Kernel

**Rules for running a vote that nobody can rig and anybody can check — too small for
anyone to own.** Technically: a thin, capture-resistant protocol for democratic
decision-making — four services, four verbs, two message formats, and the UDHR as a
measured floor. Small enough to state on one page ([`KERNEL.md`](KERNEL.md)).

The claim: **anyone can check the process that governs them from the published record
alone** — no trust in the server, the committee, or the software that produced it. The
running prototype is a sixty-member allotment society electing its treasurer: every
ballot anonymous yet provably cast by an enrolled member, no ballot ever opened — only
the encrypted sum is decrypted — and an independent verifier that confirms the election
from the artifacts alone, then rejects all twelve ways we tried to rig it, up to a
committee and both witnesses colluding to rewrite history, and finally to erase one
inconvenient ballot from it. When everything holds, the verifier's closing line is:
*"nobody had to trust the shed."* (`proto/test.sh` runs the lot in about a minute.)

Who it's for, in the end: the member who can see her own ballot counted without anyone
learning her vote; the club or co-op whose election nobody can rig; one day — the long
game — the household that learns what it is owed without telling anyone it asked. Today
it is a research prototype at village scale, and says so: every deployment declares in
a machine-readable manifest what it upholds *and what it subtracts* — subtraction
declared, never silent.

What it is not: not a product, not a platform, not a blockchain — no token in any
citizen's path, ever. And not finished, by design: this repo treats its own documents
the way the kernel treats law — the architecture essay is at rev. 3 because evidence
already revised it twice, and what the code and the first real communities teach will
revise it again.

**Next:** an in-browser verifier — drop a transcript on a static page, watch every
check run, find your own ballot by its tag. Then: a shadow-mode run alongside one real
club's AGM; the essay's rev. 4 (fold in what the prototype proved, and give every
claim a plain-speech line).

### Read it live

- **[The architecture →](https://glassontin.github.io/civic-kernel/)**  the proposal: a thin waist, four services, rights as invariants
- **[Real life against the protocol →](https://glassontin.github.io/civic-kernel/scenarios.html)**  19 stress-test stories, each machine-validated against the schemas
- **[Real legal systems, compared →](https://glassontin.github.io/civic-kernel/scenarios.html#corpus)**  the same 30 rights across the UK, Germany, the US, and the EU Charter

## Layout

- **`KERNEL.md`** — the distilled normative core: goals, threats, services, verbs, waist, refusals, measured status.
- **`index.html`** — the architecture document.
- **`proto/`** — the first running code: the club-vote election end to end (all four verbs, real
  signatures, real Merkle log, independent verifier, committed reference transcript). `proto/test.sh` is the success test.
- **`docs/`** — the functional (dynamics) model and the UK-trajectory worked example.
- **`schema/`** — the "waist": the two universal formats, as JSON Schema (Draft 2020-12).
  - `log-entry.schema.json` — one transparency-log event (includes the `coercive.act` type,
    whose body must cite its authorizing rule).
  - `manifest.schema.json` — a community's conformance manifest: which services and which of the
    30 UDHR invariants it upholds, its `decisions.coercion_resistance`, and its `rights_guard.remedy`.
- **`scenarios/`** — imagined human situations, each walked through the four verbs. Every embedded
  manifest and log entry is validated against the waist schemas, and every scenario must cite
  documented real-world precedents for its attack pattern (a required `precedents` field, 46
  citations verified July 2026). `scenario.schema.json` is the record format.
- **`corpus/`** — real legal systems captured under the same schema, sharing the 30-invariant spine:
  - `uk/` — Human Rights Act 1998 (via legislation.gov.uk) + real Commons divisions as `decision.closed` entries.
  - `de/` — Grundgesetz (via gesetze-im-internet.de).
  - `us/` — US Constitution and Bill of Rights.
  - `eu/` — EU Charter of Fundamental Rights (scope conditional under Art 51).
- **`scenarios.html`** — a self-contained browsable site rendering the scenarios and the comparative
  corpus. Data is inlined, so it serves as static files (GitHub Pages-ready); no runtime network calls.
- **`tools/`** — validators that also rebuild the inlined data in `scenarios.html`.

## Build / validate

Requires Python 3 and `jsonschema`:

```sh
pip install -r requirements.txt
python tools/validate.py         # validate scenarios; rebuild scenario-data in scenarios.html
python tools/validate-corpus.py  # validate corpus;    rebuild corpus-data in scenarios.html
```

Both exit non-zero on any validation failure. The site is pre-built (data already inlined), so it
deploys without running these — running them is how you regenerate it after editing a scenario or corpus file.

## Honest caveats

- The scenarios are **fiction anchored to fact**: the people and places are invented, but every
  attack pattern cites documented real-world precedents (each checked against its source when
  added, July 2026). They are plausibility tests of the architecture, not records of real events;
  the verdicts (`holds` / `strains` / `breaks`) are the harness's reading of the architecture
  document's own claims and limits, not endorsements.
- The comparative rights-map is a **coarse** mapping of UDHR articles to domestic constitutional
  provisions from public legal sources. It points to where systems differ; it is not legal advice
  or authoritative comparative-law scholarship, and some cells are debatable.
- `proto/` is the first and only running code: a deliberately minimal four-verb loop whose manifest
  declares its own subtractions (anonymous ballots proving roster membership by ring signature,
  sealed to a distributively-generated 2-of-3 trustee key and never individually opened,
  cast-or-audit challenges — see `proto/README.md` for what remains declared, including the one
  that matters most: the anonymity set is the roster and the proof is linear in it, which is a
  village, not a nation). Everything else is specification, test suite, and corpus; signatures
  inside the *scenarios'* embedded artifacts remain placeholders.

## License

See [`LICENSE`](LICENSE).
