# Own this tool

*A step-by-step guide to standing up your own copy of [Owed](https://glassontin.github.io/civic-kernel/owed.html)
— under your name, at your address, provably correct — and keeping it true each April.
One afternoon, no code knowledge, nothing to pay for hosting.*

At the end of this guide you will have:

- **your own copy of the benefits check**, at an address you control, with your
  organisation's name on it;
- **proof it is right** — not our word: two independent programs and twenty-two
  hand-worked test households that your copy must satisfy, run by you, on your machine;
- **a routine for April**, when the amounts change — about an hour, most of it checking
  rather than typing;
- **no dependence on us.** If this project vanished tomorrow, your copy keeps working
  and your April routine keeps working.

The deeper reason to do this is the one the tool itself is built on: a benefits check
that people are asked to trust should be checkable instead. That applies to us too.
This guide is how you stop needing us.

## Who this is for

Someone at a charity or advice organisation who can use a terminal a little —
copy a command, paste it, read what comes back. You will not write code. The typing
is done by an AI coding agent; **the checking stays yours**, and this guide is mostly
about the checking.

## What you need

- A [GitHub](https://github.com) account (free).
- An AI coding agent that runs in your terminal. The worked example throughout is
  **[Claude Code](https://claude.com/claude-code)**; any strong agent CLI works the
  same way (OpenAI's Codex CLI, and others) — the prompts below are the same, only
  the install step differs.
- Python 3 and Node.js (version 20 or later) on your machine — the two checking
  programs use one each. If any command below complains that something is missing,
  paste the complaint into the agent and ask it to sort it out; that is what it is for.

## Step 0 — the shape of what you are taking

The tool is deliberately small: one page (`owed.html`), one calculation engine
(`owed.js`), and a folder of **rule files** (`entitlements/uk/*.json`) — public,
readable data files in which every amount, threshold and question cites the law it
comes from. The rules are the asset; the page is just one reader of them.

Around that sit the guarantees you are about to inherit:

- `entitlements/judge.py` — an **independent judge**: a second implementation of the
  engine that shares no code with the page. If page and judge agree on every case,
  a bug would have to be made twice, independently, identically.
- `entitlements/personas/` — **twenty-two test households** with hand-worked expected
  results (verdicts and weekly amounts), including the awkward ones: a carer over
  State Pension age, earnings a penny over the limit, savings a penny over a threshold.
- `tools/validate.py` and `tools/owed-parity.mjs` — the programs that run all of it.

The repository also contains the wider Civic Kernel project this tool grew inside.
It comes along with the copy, costs nothing, and touches nothing — you can ignore it,
or ask the agent to strip the repository down to the benefits tool later. If you do,
the rule is the same rule as everywhere in this guide: any surgery is fine **if the
checks still end green**.

## Step 1 — take it

1. Sign in to GitHub, open
   [github.com/GlassOnTin/civic-kernel](https://github.com/GlassOnTin/civic-kernel),
   and press **Fork**. You now have your own copy at
   `github.com/YOUR-NAME/civic-kernel`.
2. In your terminal:

```sh
git clone https://github.com/YOUR-NAME/civic-kernel
cd civic-kernel
```

**Check:** `ls` shows `owed.html`, `owed.js`, and an `entitlements` folder.

## Step 2 — prove it before you change anything

Run the three checks. This is the moment the trust transfers: from here on, "it
works" is something you observed, not something you read.

```sh
python3 tools/validate.py
node tools/owed-parity.mjs
for p in entitlements/personas/*.json; do
  python3 entitlements/judge.py entitlements/uk --persona "$p" || break
done
```

**Check — the last lines must say, respectively:**

1. `entitlements: 8 rule files + the pensionable-age table valid; owed.html corpus rebuilt`
   — every rule file is well-formed and the page has been rebuilt from the rules
   (the page cannot drift from the rules: it is generated from them).
2. `owed parity: two engines, one corpus, identical traces — and no way to phone home`
   — page engine and independent judge agree on every household, and the test has
   verified the page contains no way to make a network request.
3. Twenty-two lines each beginning `ok`, one per household — every hand-worked
   expectation holds.

If any of the three says otherwise, stop and ask — the
[issues page](https://github.com/GlassOnTin/civic-kernel/issues) is read.

## Step 3 — make it yours

Start your agent in the repository folder (for Claude Code, type `claude`) and paste:

> In owed.html, rebrand the page for **[YOUR ORGANISATION]**: the page title, the
> heading, and the footer should carry our name, and the footer should state that
> this is our copy of an open tool, linking to the original project. Change nothing
> else: every cited rule, every question, the verdict wording ("appears eligible",
> "assessment-gated", "different door", "appears not eligible"), the working-out,
> the "what these rules do not encode" declarations, and the no-network behaviour
> must remain exactly as they are. Then run `python3 tools/validate.py` and
> `node tools/owed-parity.mjs` and show me their final lines.

Then do your half:

```sh
git diff
```

**Check:** the diff is short and touches only naming and the footer. The checks
catch arithmetic; **words are yours to review** — read every changed line. Then:

```sh
git add -A && git commit -m "Rebrand our copy" && git push
```

## Step 4 — publish

On your fork's GitHub page: **Settings → Pages → Build and deployment → Source:
Deploy from a branch → Branch: master, / (root) → Save.** A minute later your copy
is live at:

```
https://YOUR-NAME.github.io/civic-kernel/owed.html
```

Be aware this publishes the repository's pages to the open web — that is the point,
but it is worth saying plainly.

**Check:** open your address with the browser's network panel open (F12 → Network).
After the page loads: silence. No request leaves the person's device — that is the
property the whole tool is built around, now running under your name.

## Step 5 — April

This is the real job of ownership, so it gets the longest section.

Each spring, an uprating order changes the benefit amounts (for 2026–27 it was
[S.I. 2026/148](https://www.legislation.gov.uk/uksi/2026/148); Council Tax Reduction
has its own instrument). The rule files pin their amounts to a named tax year, and
when that year passes, **the page shows a loud staleness warning rather than going
quietly wrong** — so the cost of missing April is an embarrassing banner, not a
wrong number given to a carer. That is deliberate. This section is how you clear it.

**Your half first (an evening with gov.uk):** collect the year's figures — the new
uprating order on legislation.gov.uk, and the gov.uk pages for each benefit. You are
about to check the agent's work against these, so get them from the source, not from
the agent.

**Then the drill.** On a fresh branch:

```sh
git checkout -b april-uprating
```

Start the agent and paste, with the year's real figures filled in:

> The [YEAR] benefits uprating has been made by [INSTRUMENT, e.g. "The Social
> Security Benefits Up-rating Order 2027 (S.I. 2027/NNN)"]. The new weekly amounts
> are: [LIST EACH: e.g. "Pension Credit standard minimum guarantee £X single /
> £Y couple; carer addition £Z; …"]. All other amounts are unchanged. In
> `entitlements/uk/*.json`: update every file that pins one of these amounts
> (several files repeat the same figure — find them all), update each changed
> file's `effective` block to the new tax year and instrument, and update the
> amounts quoted in `plainly` texts. Then update the expected amounts in
> `entitlements/personas/*.json` to match, and for each one show me the arithmetic:
> old expectation, what changed, new expectation. Give me a table of every figure
> you changed — file, old, new, and the source I gave you for it. Then run
> `python3 tools/validate.py`, `node tools/owed-parity.mjs`, and
> `python3 entitlements/judge.py entitlements/uk --persona FILE` for every file in
> `entitlements/personas/`, and show me their final lines.

**Then your half again, the part that matters:**

1. Read the agent's table **against the instruments you collected** — every figure,
   yours to confirm. The agent does the typing; the checking is what you own.
2. Run the three checks from Step 2 yourself. All green.
3. Read `git diff` — it should touch rule files, personas, and the rebuilt
   `owed.html`, and nothing else.
4. Land it:

```sh
git checkout master && git merge april-uprating && git push
```

Budget an hour the first year. The page's staleness warning clears the moment the
new tax year is pinned.

### Rehearse it today

You do not have to wait for April to find out whether this works in your hands.
On a branch you will delete, run the April prompt with **plainly fictional figures**
(say the guarantee becomes £244.90/£373.90) and watch what happens: the checks fail
loudly until the personas' expectations are updated to match, then end green. One
thing to expect: rehearsing before the new tax year has actually started, the checks
will insist that a future-dated year is explicitly acknowledged — the corpus has a
field for exactly that, the agent will find it, and that insistence is the staleness
alarm demonstrating itself. Then throw the rehearsal away:

```sh
git checkout -- . && git checkout master && git branch -D april-uprating
```

(The first command discards anything not committed — a rehearsal leaves fictional
figures in your working copy, and they must not survive it.) Never push a rehearsal.
Its only product is your own confidence.

## If something is wrong

The rules are public and correctable. If your copy disagrees with a real case, or a
question reads badly, or an amount looks off: file it on the
[original project's issues page](https://github.com/GlassOnTin/civic-kernel/issues)
so every copy benefits, or fix your copy and offer the change back. Precedent: the
first four issues ever filed on this repository came from a fresh AI model rebuilding
the tool from the rules alone and auditing them on the way past — all four were
resolved within days.

## Beyond this tool

Everything above generalises. The pattern — rules as public data files that cite
their sources, a page that is generated from the rules, an independent judge that
shares no code with it, hand-worked test cases — will carry any body of rules you
need people to be able to check rather than trust: your grants criteria, a local
authority's discretionary scheme, another benefit entirely. The
[rebuild recipe](../rebuild-owed.md) is the seed for that: it is the prompt that
grows a fresh page from a folder of rule files.

## Has this been tried?

Yes — on 19 July 2026, in a clean-room clone, with the guide's own worked example:
Claude Code (v2.1.214, Fable 5), run headless, given only the prompts printed above.

- **Step 2 out of the box:** all three checks green on a fresh clone, final lines
  exactly as quoted in this guide.
- **Step 3, the branding prompt, verbatim** (as a fictional "Harborside Carers'
  Centre"): a three-line diff — title, heading, footer — with every invariant intact:
  verdict vocabulary unchanged, citations unchanged, network silence unchanged, all
  checks green. Verified independently by the tester, not taken from the agent's
  report.
- **Step 5, the rehearsal, verbatim** (fictional £244.90/£373.90 guarantee): the
  agent found and updated the pinned figure in all three rule files that repeat it,
  updated sixteen households' expected amounts with its arithmetic shown, and
  correctly left alone the couple whose income clears even the raised guarantee.
  It flagged, unprompted, that another test household now clears the line by ten
  pence; it discovered and used the corpus's staleness-acknowledgement field when
  pinning a future tax year (a mechanism this guide had not mentioned); and it
  named its own caveats — Council Tax Reduction is normally uprated by its own
  instrument, and the sources had not been re-checked against legislation.gov.uk —
  which is precisely the checking this guide says stays with you. All three checks
  were then re-run by the tester: green, twenty-two households of twenty-two, and
  the spot arithmetic confirmed by hand.
- The test also caught a bug in this guide's first draft — the rehearsal clean-up
  would have left uncommitted fictional figures in the working copy. Fixed above,
  which is the discipline working on its own instructions.

Not tried: the fork-and-Pages click-path on a fresh GitHub account (the original
deploys on Pages, which is standing evidence the repository works there, but the
clicks in Step 4 were not re-walked); more than one agent and one run per step; and
a person who is not this project's author following the guide cold — if that person
is you, what you find is worth an
[issue](https://github.com/GlassOnTin/civic-kernel/issues).

## What this guide does not solve

- **Your governance.** Whose name signs off that the amounts are right is your
  decision, and this guide cannot make it for you. What it changes is the cost of
  the evidence that signature rests on.
- **Accessibility beyond structure.** The page follows GDS patterns and has been
  audited structurally (labels, fieldsets, focus, status announcements), but has
  not been tested with real assistive-technology users. Commission that before you
  badge your copy as accessible.
- **The decision to own.** This guide makes owning cheap — an afternoon now, an
  honest hour each April. It cannot make owning free, and linking to a copy someone
  else stewards remains a reasonable choice.

*Part of the [Civic Kernel](https://github.com/GlassOnTin/civic-kernel) — the same
discipline as the rest of it: the artifact is checkable, the recipe is public, and
nobody has to trust the shed.*
