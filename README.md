# The Civic Kernel

**A thin, capture-resistant protocol for democratic decision-making** — with a
machine-checked stress-test suite and a comparative-law corpus that hold the design
against real situations and real legal systems.

### Read it live

- **[The architecture →](https://glassontin.github.io/civic-kernel/)**  the proposal: a thin waist, four services, rights as invariants
- **[The protocol against real life →](https://glassontin.github.io/civic-kernel/scenarios.html)**  17 stress-test stories, each machine-validated against the schemas
- **[Real legal systems, compared →](https://glassontin.github.io/civic-kernel/scenarios.html#corpus)**  the same 30 rights across the UK, Germany, and the US

## Layout

- **`index.html`** — the architecture document.
- **`schema/`** — the "waist": the two universal formats, as JSON Schema (Draft 2020-12).
  - `log-entry.schema.json` — one transparency-log event (includes the `coercive.act` type,
    whose body must cite its authorizing rule).
  - `manifest.schema.json` — a community's conformance manifest: which services and which of the
    30 UDHR invariants it upholds, its `decisions.coercion_resistance`, and its `rights_guard.remedy`.
- **`scenarios/`** — imagined human situations, each walked through the four verbs. Every embedded
  manifest and log entry is validated against the waist schemas. `scenario.schema.json` is the record format.
- **`corpus/`** — real legal systems captured under the same schema, sharing the 30-invariant spine:
  - `uk/` — Human Rights Act 1998 (via legislation.gov.uk) + real Commons divisions as `decision.closed` entries.
  - `de/` — Grundgesetz (via gesetze-im-internet.de).
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

- The scenarios are **AI-generated fiction** — plausibility tests of the architecture, not records
  of real events. The verdicts (`holds` / `strains` / `breaks`) are the harness's reading of the
  architecture document's own claims and limits, not endorsements.
- The comparative rights-map is a **coarse** mapping of UDHR articles to domestic constitutional
  provisions from public legal sources. It points to where systems differ; it is not legal advice
  or authoritative comparative-law scholarship, and some cells are debatable.
- Nothing here is running software: it is a specification, a test suite, and a corpus. No cryptography
  is implemented — signatures in the artifacts are placeholders.

## License

See [`LICENSE`](LICENSE).
