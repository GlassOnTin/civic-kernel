# The EU trajectory

What this page is for: the [UK trajectory](uk-trajectory.md) asked whether small,
reversible steps could carry one real polity to where a majority cannot strip a minority's
rights, and found the path stalls at the one step the sovereign will not take. This page
asks the same question of the European Union — and gets a different shape of answer. The
EU's remedy is already the strongest kind; **no move on the lattice improves its verdict at
all**. Its two soft spots — the Charter's reach, and a member state's obedience — are not
rungs it has declined to climb; they are locked at treaty unanimity, and one of them is not
on the ladder in the first place. The UK stalls one step short. The EU is already at the
ceiling of what its kind of protection can give, and the ceiling is `strains`.

The attack is fixed throughout: a 61% majority banning a minority's worship (the
[`majority-vs-minority`](../scenarios.html) series). Only the EU's configuration changes.

| # | Move | remedy | scope | coverage | verdict | source |
|---|------|--------|-------|----------|---------|--------|
| S0 | **The EU today** — Charter of Fundamental Rights, binding since Lisbon | strike | conditional | 25/30 | **strains** | measured (`majority-vs-minority-eu`) |
| S1 | + adopt the transparency log ([§3.4](https://glassontin.github.io/civic-kernel/#s3-4 "Every act lands in a public record that can only grow. Rewrite yesterday and the sums stop matching in every copy of today — and any phone can tell.")) | strike | conditional | 25/30 | strains | inferred |
| S2 | + verifiable ballots for EP elections and the ECI ([§3.2](https://glassontin.github.io/civic-kernel/#s3-2 "Your ballot is sealed before it leaves your hand and counted without being opened. You can check it was counted; you cannot prove to anyone how you voted.")) | strike | conditional | 25/30 | strains | inferred |
| S3 | **+ widen scope: conditional → unconditional** (unwind Art 51's gate) | strike | unconditional | 25/30 | **strains** — the verdict does not move | measured in-context (`majority-vs-minority-eu-unconditional`) — **and locked at treaty unanimity** |
| S4 | + make a member state obey the judgment it has decided to ignore | — | — | — | the `executive-ignores` residue | **not a lattice move at all** |

**Why S1 and S2 don't flip it, and are worth taking anyway.** As in the UK, the cheap,
sovereignty-free moves don't touch the gating axis. After S1 the ban, its classification,
the Art 51 scope fight and the fourteen months the ban ran as valid law are unrewritable
and public in every member state's copy; after S2 the counts on the next European
Parliament election — currently twenty-seven national systems with twenty-seven audit
postures — and the signature-verification of a [European Citizens' Initiative](https://citizens-initiative.europa.eu/)
become checkable from the published record. Real improvements, no treaty cost, verdict
unchanged. The ECI is worth naming precisely: an existing EU-level instrument whose whole
problem — a million signatories, each provably an eligible citizen, none counted twice,
currently solved by collecting identity documents — is SVC-1's job description
([§3.1](https://glassontin.github.io/civic-kernel/#s3-1 "Prove you are on the list and have not already spoken — without saying which name on the list you are. No file on anyone is ever built.")).

**Why S3 doesn't flip it either — the EU's distinctive result, now measured.** The UK had
one move that flips its verdict, and won't take it. The EU has no such move, because it
already took it: the remedy is `strike`, the strongest measured. S3 is run as a
byte-identical counterfactual (`majority-vs-minority-eu-unconditional`, the same
discipline as the UK's strike run): hold Valmiria constant to the byte and move only
`rights_guard.scope` — the verdict stays `strains`, because a strike is only as strong as
an uncaptured court, and relief is eventual while the harm is immediate. What the moved
field buys is real and now measured: disapplication in 82 days instead of 425, the
fourteen-month interim window cut to nine weeks, and — the least visible gain — the end
of the ethnicity lottery, since the conditional run's protection worked only because the
Tatars happen to be an ethnic as well as a religious minority. A gain in reach, speed and
equality of protection; no gain in verdict. And even that non-flipping move is the
constitutional maximum: Art 51 is Treaty text, amendable only by unanimity of the member
states plus twenty-seven ratifications — the same self-binding problem as the UK's S3,
multiplied by twenty-seven vetoes, spent on a change that improves no verdict. Which is
why it never gets made.

**S4 is the real exposure, and it is not on the ladder.** The measured EU strain assumed
what the `executive-ignores` run showed cannot be assumed: that the member state obeys the
court. The documented pattern — judgments ignored, daily fines accruing unpaid, an Art 7
procedure that requires the unanimity of the other governments and therefore never
completes — is an enforcement gap no manifest field expresses. The kernel's honest offer
here is the same as everywhere: it can make the defiance perfectly legible — the judgment,
the non-compliance, the fine ledger, witnessed across every member state's copy — and it
cannot make anyone obey ([§12](https://glassontin.github.io/civic-kernel/#s12 "What is excluded on purpose, and the six problems not yet solved — by this design or anyone's. Both lists in full.")).
A decision binds only where power obeys the record.

**One collision worth stating while it is still cheap.** The EU is currently building the
other half of this machinery itself: eIDAS 2.0 and the EUDI wallet will put a
state-issued digital identity in every pocket, built on device attestation and
wallet-provider gatekeeping. The kernel's refusals 2 and 3 (no population database, no
remote attestation) name that exact posture, and the [manifest](../README.md#w-manifest)
schema already models it — its own annotation says an EUDI-wallet deployment today would
declare `personhood.unlinkable: false`, the legible degradation
[§6](https://glassontin.github.io/civic-kernel/#s6 "Nobody has to adopt all of it. Any group may take the parts it wants — but must publish, in a form anyone's phone can read, exactly what it left out.")
exists to express ([§13](https://glassontin.github.io/civic-kernel/#s13 "Every piece of this already exists somewhere, well funded. Nobody is joining the pieces up, and no one has built the citizen's side — the phone that checks. That gap sets the plan.")).
Whether the wallet ships with unlinkable presentations or with a phone-home attestation
is being decided now, in the Architecture Reference Framework's revisions — the one
current legislative process anywhere that could move a whole column's personhood posture
in either direction.

That is the shape of the EU's stall, part of a set the UK page opened — five now: the
UK's path stalls at the **remedy** (a sovereign that will not bind itself), the EU's at
**scope and obedience** (a treaty that cannot cheaply widen, a judgment that cannot
compel), the [PRC's](cn-trajectory.md) at the **record itself**,
[Germany's](de-trajectory.md) at **nothing** — the measured ceiling held, the bench the
residue — and the [US's](us-trajectory.md) at its **founding text** (Articles III and V).
Same ladder, five different jams — and the jam tells you what kind of polity you are
looking at.

---

*Honesty note: S1–S2 are inferred from the measured remedy- and scope-gating, not re-run.
S3 is measured in-context (`majority-vs-minority-eu-unconditional`): byte-identical to
the measured EU run except `rights_guard.scope`, the same discipline as
`majority-vs-minority-uk-strike` — and, like it, a modelled counterfactual (a Union that
amended Art 51 by unanimity), not history. S4 has no manifest field to counterfactual at
all, which is itself the finding: obedience is not on the waist. Coverage 25/30
throughout is the measured EU column; nothing on this page changes it.*
