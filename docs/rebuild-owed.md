# Make this page yourself — the rebuild recipe

*The honest answer to "who maintains this, and what if they stop?" is that the tool is
not the asset — the rules are. The rules are public data files, the acceptance test is
an independent program, and the page itself can be rebuilt from scratch by anyone with
access to a capable AI model, in one sitting, without reading our code. This document
is the recipe: a prompt you can paste into a leading model — Claude, ChatGPT, Kimi,
whatever is strongest when you read this — plus the test that tells you whether what
came back is right. If the rebuild agrees with the independent judge on every test
case, you never needed to trust us; if ours disappears tomorrow, yours works.*

## What you need

- The rule files (public, plain JSON — the only source of truth):
  `https://github.com/GlassOnTin/civic-kernel/tree/master/entitlements/uk`
  (eight entitlement files plus `spa.json`, the statutory pensionable-age table).
- The independent judge (for checking the result, not for building it):
  `entitlements/judge.py` in the same repository, run as
  `python3 entitlements/judge.py entitlements/uk --persona circumstances.json --json`.
- A leading AI model and one afternoon.

## The prompt

Paste the following, attaching or linking the rule files:

---

Build a single-file HTML page — one `.html`, no build step, no dependencies — that
tells a person what UK benefits they appear entitled to, computed entirely on their
device from the attached rule files. Requirements, all of them binding:

**The rules are the only authority.** Read the attached JSON rule files (eight
entitlements plus `spa.json`, a statutory pensionable-age table). Generate the input
form from what the rules demand: a question that no rule demands must not exist, and
every question must display, beneath it, the legal rule it is asked under and a link
to its source (both are in the data). Do not invent, simplify, or "improve" any rule.

**Zero network.** After the page loads, it must make no network request of any kind —
no analytics, no fonts, no APIs, nothing. A user opening the browser's network panel
must see silence. It must work opened from a local file with the internet off. It
stores nothing: no cookies, no localStorage; when the tab closes, everything is gone.

**Live and honest.** Recompute on every change, so "what if" costs nothing. Verdicts
use this vocabulary and no stronger: appears eligible / assessment-gated / different
door / appears not eligible — with weekly amounts where computable. Every amount must
expand to show its working: each step with its result and the rule it applied. Each
entitlement must also show what its rules deliberately do not encode. Include a
plainly-worded section on what the page cannot do (it does not decide claims; the
DWP decides). Read each rule file's `effective.tax_year`: state it, and if the current
date is past that year, show a loud warning that the amounts may be stale.

**The circumstances file.** One button downloads the user's answers as a small JSON
file (`circumstances.json`) they keep; a drop-zone (with a keyboard-reachable file
picker) loads one back and recomputes everything. Nothing exists unless the user
saves it.

**Accessible.** Radio groups as fieldset+legend, every input labelled, units and help
text tied to their inputs with `aria-describedby`, a debounced `role="status"` line
that announces a short summary when results change (never a full re-read), visible
focus states on everything interactive, contrast meeting WCAG AA, and the file-input
hidden accessibly (focusable), not `display:none`.

**Register.** Plain English throughout; large near-black text on white; no decoration
that carries no meaning.

---

## The test — do not skip it

The rebuild is correct only if it agrees with the independent judge. For any set of
answers, save the circumstances file from your rebuilt page and run:

```sh
python3 entitlements/judge.py entitlements/uk --persona circumstances.json --json
```

Same verdicts, same weekly amounts, for every entitlement, on every case you try —
including awkward ones: a carer over State Pension age (the overlap rule), earnings
just under and just over the Carer's Allowance limit, capital straddling the Pension
Credit thresholds. Disagreement means one of the two is wrong, and finding out which
is exactly the kind of contribution the
[open door](https://github.com/GlassOnTin/civic-kernel/issues) is for.

*Part of the [Civic Kernel](https://github.com/GlassOnTin/civic-kernel) — the same
discipline as the rest of it: the artifact is checkable, the recipe is public, and
nobody has to trust the shed.*
