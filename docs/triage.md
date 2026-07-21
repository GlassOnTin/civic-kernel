# Triaging harms: which the kernel can touch, and which it must refuse

**What this page is for:** it describes how we choose which real-world wrong to
test against the protocol next — and, one day, how a machine could scan a whole
archive of harms and hand back a ranked shortlist of the ones a checkable record
would most cheaply shift. It borrows a habit called *triage* — invented in
battlefield medicine and emergency nursing, borrowed from there by software
engineering, and here returned to something near its original use: sorting
social and legal harms the way a clinician sorts patients. It is written for
litigators, campaigners, lawmakers, and anyone deciding where scarce effort
should go.

<details>
<summary><b>Plainly</b> <i>Triage began in battlefield medicine: when you cannot treat everyone, sort by how urgent and how treatable, and name honestly whom you cannot help. Software borrowed it for bugs; we return it to public harms. The refusals matter as much as the picks — most wrongs are not ours to touch, and saying so is half the value.</i></summary>

The scenario corpus answers a question one case at a time — *does a thin,
checkable protocol help with this wrong, and where does it stop?* Each answer is
expensive: a few hundred lines of researched, machine-validated argument. So the
prior question — *which wrong next?* — deserves a cheap, honest, repeatable
answer of its own. That is triage.

</details>

## The idea, borrowed twice

The word comes from the French *trier*, to sort, and its method was worked out on
battlefields and in emergency wards. When you cannot treat everyone at once you
sort by two things — how urgent the case is, and how much your treatment would
actually change its outcome — and then you do the hardest thing in the practice:
you name, honestly, whom you cannot help. Software teams borrowed the habit for
bugs. Turning it on legal and social harms brings it most of the way home.

An engineering team faced with a thousand open bug reports does not work through
them in the order they arrived. It **triages**: for each report it asks whether
the bug is real and reproducible, whether it is in scope for this system at all,
how much damage it does, and how cheap it is to fix — and only then decides what
to pick up. The reports it *closes* — "not a bug", "won't fix", "out of scope" —
matter as much as the ones it accepts, because a clear reason for closing saves
everyone from re-litigating it.

A democratic harm can be triaged the same way, and the discipline transfers
almost unchanged. The one adaptation: our "won't fix" is a matter of principle,
not laziness. A great many wrongs are real, serious, and simply *not ours to
touch* — and the protocol is built to refuse them on purpose.

## The pipeline

Four stages. A case that fails an early one never reaches the later ones.

1. **Intake, with a citation.** Restate the harm in one line, and name a real
   source for it. No case enters triage without a documented precedent — the
   same rule the scenario schema enforces ("no attack without a cited
   precedent"), applied at the door.

2. **The scope sort — the load-bearing filter.** Ask one question: is the wrong
   a matter of *substantive judgment* (who is right, what is fair, what is true)
   or of *process integrity* (was the record made, was the rule cited, is the
   pattern visible)?
   - **Substantive → refused, out of scope**, with the reason stated. A child's
     best interests under Article 8, whether a claim is misinformation, whether a
     policy was wise — the kernel refuses to decide these (refusal 11), because a
     machine that adjudicated them would be a machine worth capturing. In the
     clinical metaphor these are the cases triage cannot save — and naming them,
     rather than pretending otherwise, is the oldest discipline in the practice.
     This is not a gap to apologise for; it is the design.
   - **Process integrity → accepted.** On to prioritise.
   - One more close, borrowed from bug triage's *duplicate*: a real process wrong
     the corpus **already answers** is **closed as covered**, naming the encoded
     scenarios that carry it. A covered case is not refused — the record can touch
     it; other cases already do — and the pointer is on the page so nobody
     re-litigates it.

3. **The signature check.** Every case that has ever *worked* shared a shape.
   Does this one carry it? (The catalogue is below.) If it does, the same cheap
   lever — a contemporaneous, checkable record — is a candidate.

4. **Priority — reach × leverage: the clinician's calculus.** Severity and
   treatability — how bad is it, and how much would a checkable record actually
   change the outcome.
   - **Reach**: how many people, how much public money, how central to the
     democratic function (1 low – 3 high).
   - **Leverage**: how much a cheap, checkable record would shift the *cost* of
     the wrong (1–3). Note the word: *cost*, not *existence*. A record rarely
     cures a wrong; it makes it visible in time, destroys deniability, and feeds
     the courts and elections that can. Where even that changes little, leverage
     is low, and the score says so.

## The recurring signature

The wrongs the protocol can touch are not a random set. Across the corpus they
keep the same few fingerprints — the "bug categories" of public harm:

- **`pattern_of_lawful_acts`** — the wrong lives in an aggregate of
  individually-lawful acts (a procurement lane, a stop-and-search pattern, a
  regulator's forbearance). Unreachable one act at a time; visible only in the
  aggregate.
- **`record_absent`** — the act was never recorded contemporaneously, so
  accountability means reconstructing it, late and by force.
- **`record_destroyed`** — the record was made, then destroyed at source.
- **`access_gated`** — the record exists, but access is by-permission and can be
  slow-walked until the answer no longer matters.
- **`inaction_no_artifact`** — the wrong is a *non-decision*, which produces
  nothing to appeal or review.
- **`documentary_gate`** — a document requirement excludes people from a right.
- **`record_single_authored`** — the record exists, contemporaneous and signed —
  and its only author is an interested party, with no place for a competing
  account to attach. The artful minute, the self-graded harm. The shape had to be
  named structurally: to file it under absence you must first judge the present
  record dishonest, which is a truth call the vocabulary itself refuses.

## What the scorer will and will not do

This is the part that keeps triage honest, and it is worth stating plainly to a
non-engineering reader.

- **It is a scout, not a judge.** It ranks; a person decides. This is not
  timidity — it is the kernel's own first principle. A protocol that refuses to
  let a machine adjudicate substance cannot then build a machine that adjudicates
  which injustices deserve attention. The scout flags "this wrong has the shape
  of one a checkable record could reach — a human should look." Nothing more.
- **Every score shows its inputs.** There is no hidden weighting: a score is
  `reach × leverage`, both set by a person's reading and both on the page. The
  same discipline the kernel demands of a form field — every demand cites its
  rule — applied to the triage itself.
- **Legibility is a lever, not a cure.** Cases marked ⚠ are ones where making the
  wrong visible changed little: the court voided the procurement lane and
  returned nothing; the watchdog found the regulator failed and the river stayed
  dirty. They still rank — deniability destroyed is worth something — but the
  caveat is shown, never buried.
- **Precedents are verified at encode, not at triage.** Triage runs on
  institution-level leads and is deliberately cheap and provisional — like
  confirming a bug reproduces only when you pick it up, not when you file it. The
  full cited-precedent rigour happens later, when a candidate is promoted to a
  full scenario.

## The current run

Auto-filled by `python3 tools/triage.py --write` — regenerate it rather than
editing by hand; the block below is generated from `triage/cases.json`.

The ranking doubles as a check on the rubric, not just an output: the encoded
cases land where their verdicts predict — the ones that *break* sink to the
bottom on leverage, the rubric admitting it — and the strongest candidates
surface at the top by the process, not by an author's hunch.

<!--TRIAGE-START-->

_Generated by `tools/triage.py` over `triage/cases.json` (49 cases: 37 accepted, 2 closed as covered, 10 refused)._

### Accepted — ranked by leverage

| # | case | score | reach × leverage | signature | status |
|--:|------|:-----:|:----------------:|-----------|--------|
| 1 | foi-slow-walking | 9 | 3 × 3 | access_gated, record_absent | **encoded** (`foi-slow-walking`) |
| 2 | horizon-unauditable-evidence | 9 | 3 × 3 | record_absent, pattern_of_lawful_acts | **encoded** (`horizon-unauditable-evidence`) |
| 3 | party-finance-dark-money | 9 | 3 × 3 | pattern_of_lawful_acts, record_absent | **encoded** (`party-finance-dark-money`) |
| 4 | revolving-door-lobbying ⚠ legible-not-remedied | 9 | 3 × 3 | pattern_of_lawful_acts, record_absent | **encoded** (`revolving-door-lobbying`) |
| 5 | shareholder-vote-plumbing | 9 | 3 × 3 | record_absent, pattern_of_lawful_acts | **encoded** (`shareholder-vote-plumbing`) |
| 6 | automated-welfare-reasons | 6 | 3 × 2 | record_absent | **encoded** (`automated-welfare-reasons`) |
| 7 | exam-algorithm-downgrade ⚠ legible-not-remedied | 6 | 3 × 2 | record_absent, pattern_of_lawful_acts | **encoded** (`exam-algorithm-downgrade`) |
| 8 | family-contact-order-unenforced ⚠ legible-not-remedied | 6 | 3 × 2 | pattern_of_lawful_acts, inaction_no_artifact | **encoded** (`family-contact-order-unenforced`) |
| 9 | family-court-secrecy ⚠ legible-not-remedied | 6 | 3 × 2 | access_gated, pattern_of_lawful_acts | **encoded** (`family-court-secrecy`) |
| 10 | gig-deactivation-no-reasons | 6 | 3 × 2 | record_absent | **encoded** (`gig-deactivation-no-reasons`) |
| 11 | grenfell-warnings-ignored ⚠ legible-not-remedied | 6 | 3 × 2 | inaction_no_artifact, record_absent | **encoded** (`grenfell-warnings-ignored`) |
| 12 | maternity-harm-downgraded ⚠ legible-not-remedied | 6 | 3 × 2 | pattern_of_lawful_acts, inaction_no_artifact, record_single_authored | **encoded** (`maternity-harm-downgraded`) |
| 13 | minutes-written-by-the-winner ⚠ legible-not-remedied | 6 | 3 × 2 | record_single_authored | **encoded** (`minutes-written-by-the-winner`) |
| 14 | nhs-data-access-opaque | 6 | 3 × 2 | access_gated, record_absent | **encoded** (`nhs-data-access-opaque`) |
| 15 | procurement-vip-lane ⚠ legible-not-remedied | 6 | 3 × 2 | pattern_of_lawful_acts, record_absent | **encoded** (`procurement-vip-lane`) |
| 16 | regulator-inaction ⚠ legible-not-remedied | 6 | 3 × 2 | pattern_of_lawful_acts, inaction_no_artifact | **encoded** (`regulator-inaction`) |
| 17 | single-justice-procedure-opaque ⚠ legible-not-remedied | 6 | 3 × 2 | documentary_gate, record_absent | **encoded** (`single-justice-procedure-opaque`) |
| 18 | who-told-the-minister ⚠ legible-not-remedied | 6 | 3 × 2 | record_absent, record_single_authored | **encoded** (`who-told-the-minister`) |
| 19 | carers-allowance-overpayment ⚠ legible-not-remedied | 4 | 2 × 2 | inaction_no_artifact, record_absent | **encoded** (`carers-allowance-overpayment`) |
| 20 | citizenship-deprivation-basis ⚠ legible-not-remedied | 4 | 2 × 2 | record_absent | **encoded** (`citizenship-deprivation-basis`) |
| 21 | coop-governance-opaque | 4 | 2 × 2 | pattern_of_lawful_acts, record_absent | **encoded** (`coop-governance-opaque`) |
| 22 | criminal-disclosure-failure ⚠ legible-not-remedied | 4 | 2 × 2 | access_gated, record_absent | **encoded** (`criminal-disclosure-failure`) |
| 23 | dwp-death-reviews-secret ⚠ legible-not-remedied | 4 | 2 × 2 | access_gated, record_absent | **encoded** (`dwp-death-reviews-secret`) |
| 24 | facial-recognition-no-basis | 4 | 2 × 2 | record_absent | **encoded** (`facial-recognition-no-basis`) |
| 25 | marketplace-delisting-no-rule | 4 | 2 × 2 | record_absent | **encoded** (`marketplace-delisting-no-rule`) |
| 26 | ministerial-standards-unenforced ⚠ legible-not-remedied | 4 | 2 × 2 | inaction_no_artifact | **encoded** (`ministerial-standards-unenforced`) |
| 27 | ofsted-single-word-judgment ⚠ legible-not-remedied | 4 | 2 × 2 | record_absent | **encoded** (`ofsted-single-word-judgment`) |
| 28 | police-vetting-ignored ⚠ legible-not-remedied | 4 | 2 × 2 | inaction_no_artifact, record_absent | **encoded** (`police-vetting-ignored`) |
| 29 | protest-conditions-no-basis | 4 | 2 × 2 | record_absent | **encoded** (`protest-conditions-no-basis`) |
| 30 | removal-without-legible-warrant | 4 | 2 × 2 | record_absent | **encoded** (`removal-without-legible-warrant`) |
| 31 | send-ehcp-refusals ⚠ legible-not-remedied | 4 | 2 × 2 | pattern_of_lawful_acts, inaction_no_artifact | **encoded** (`send-ehcp-refusals`) |
| 32 | union-ballot-employer-interference ⚠ legible-not-remedied | 4 | 2 × 2 | pattern_of_lawful_acts | **encoded** (`union-ballot-employer-interference`) |
| 33 | us-civil-asset-forfeiture ⚠ legible-not-remedied | 4 | 2 × 2 | record_absent, documentary_gate | **encoded** (`us-civil-asset-forfeiture`) |
| 34 | voter-id | 4 | 2 × 2 | documentary_gate | **encoded** (`voter-id`) |
| 35 | drc-medical-detention ⚠ legible-not-remedied | 3 | 3 × 1 | record_absent | **encoded** (`drc-medical-detention`) |
| 36 | government-by-whatsapp ⚠ legible-not-remedied | 3 | 3 × 1 | record_destroyed | **encoded** (`government-by-whatsapp`) |
| 37 | infected-blood-coverup ⚠ legible-not-remedied | 3 | 3 × 1 | record_destroyed | **encoded** (`infected-blood-coverup`) |

### Recommended to encode next

The highest-leverage cases not yet built as scenarios:


### Closed as covered — already on the map

Real process wrongs a checkable record does touch — through scenarios already encoded. Bug triage calls this close *duplicate*; each names the cases that carry it.

| case | covered by | reason |
|------|------------|--------|
| consultation-long-grass | `foi-slow-walking`, `dwp-death-reviews-secret`, `regulator-inaction`, `family-contact-order-unenforced`, `send-ehcp-refusals` | The long grass is the clock family, already encoded four ways: the holder running the clock (foi-slow-walking), time quietly becoming the ruling (family-contact-order-unenforced), the review that learns nothing (dwp-death-reviews-secret), forbearance with no artifact (regulator-inaction), rationing by attrition (send-ehcp-refusals). The one new sliver — an inquiry owing its own deadline — is the timed-inbound-duty extension the corpus has already named and deferred. A sixth scenario would re-walk the five. |
| safe-pair-of-hands | `revolving-door-lobbying`, `procurement-vip-lane`, `ministerial-standards-unenforced` | The checkable part — who appointed, on whose referral, under what terms — is the executive.act appointment with provenance the corpus already carries (revolving-door-lobbying, procurement-vip-lane), and the judge-is-the-defendant shape is ministerial-standards-unenforced. Whether the chair is the wrong chair is substance, refused (refusal 11). |

### Refused — out of scope

Not defects a checkable record can touch; each is closed with its reason.

| case | why refused |
|------|-------------|
| child-surname-article8 | A substantive judgment about a child's best interests under Article 8 — who is right. The kernel refuses to decide substance (refusal 11); this belongs to a court, and the protocol has no business weighing it. |
| doctor-misinformation-gmc | Deciding whether a claim is misinformation is a judgment of truth — a ministry of truth is exactly what the kernel refuses to build (T11, refusal 11). Whether the GMC then acts is its substantive professional judgment. |
| policy-wisdom | Whether a policy is wise is a political judgment, not a process defect. There is no record to make, rule to cite, or pattern to surface — only a disagreement, which elections and argument settle, not infrastructure. |
| planning-merits | The merits of a planning decision are substantive and political — whether this was the right call — for the planning system and the courts, not a process defect a record can settle. The kernel can make the decision and its reasons legible; it cannot decide whether the decision was right. |
| assisted-dying-question | A substantive moral and political question the kernel refuses on principle (refusal 11). It can run a fair, verifiable, receipt-free vote on the matter and hold the rights floor around it; it must never decide the answer — the line that keeps it from becoming a machine worth capturing. |
| clinical-best-interests | The best interests of a critically ill patient are a substantive medical and ethical judgment for clinicians and a court, weighing evidence the protocol cannot and must not adjudicate. The kernel can make the decision and its reasons legible; it has no business deciding whether treatment should continue. |
| statue-removal | Whether a monument should stand is a substantive question of values and history a community must argue and decide, not a process defect. The kernel can run a fair, verifiable vote on it and record the outcome; it must never decide the answer. |
| online-safety-content-takedown | Deciding whether a particular post is harmful or unlawful is a judgment of truth and speech — the ministry of truth the kernel refuses to build (refusal 11, T11). The legibility of a takedown process (was a rule cited, is there an appeal) is a separate, onstage question; the merits are not the kernel's. |
| family-custody-bias | A substantive judgment about a child's best interests and how judicial discretion should fall — who is right. The kernel refuses to decide substance (refusal 11), exactly as it refused the child-surname Article 8 case. What it can reach is the process around the judgment: the unpublished pattern (family-court-secrecy) and the unenforced order (family-contact-order-unenforced) — the two onstage halves of this campaign. |
| the-misleading-brief | Whether advice was fair, complete or honest is a judgment of substance and truth — grading the quality of counsel is the ministry of truth refused outright (refusal 11). The kernel can make the advice-trail's existence checkable — who-told-the-minister carries that onstage sliver — but it must never mark a brief misleading, and the deeper harm, officials who stop writing candid advice at all, is a culture no schema field reaches. |

<!--TRIAGE-END-->

## Running it, and adding a case

```
python3 tools/triage.py            # print this report
python3 tools/triage.py --check    # validate the corpus only
```

To add a case, append it to `triage/cases.json` with its harm, a lead, the scope
(`onstage`/`offstage`), any signatures, and — for onstage cases — a `reach` and
`leverage` from 1 to 3. Offstage cases must state why they are refused; a case
the corpus already answers takes `status: "covered"` with a `covered_by` list and
a `covered_reason` naming the scenarios that carry it. That is the whole method:
cheap enough to run over a large archive, honest enough that the refusals and
the duplicates are on the page next to the picks.
