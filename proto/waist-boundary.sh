#!/bin/bash
# waist-boundary.sh — the shadow of test.sh.
#
# test.sh proves the twelve riggings of the BALLOT are each caught by the defence
# the design names. This proves the complementary, less comfortable fact: the
# "Yes Minister" attacks — the ones that corrupt the NARRATIVE record rather than
# the ballot — pass the ballot verifier untouched, because they live on the far
# side of the waist it defends. The verifier proves the count nobody had to trust;
# it says nothing about whether the minute told the whole story, because a machine
# that graded the honesty of an account would be the ministry of truth the kernel
# refuses to build (refusal 11).
#
# So the polarity here is inverted. A probe is GREEN when the ballot verifier still
# behaves as the boundary predicts — it certifies the count and is blind to the
# narrative attack. A probe is RED only if that behaviour has MOVED: if someone
# taught the verifier to read the account for meaning, a probe here would trip, and
# the corpus's verdict for that attack would need re-examining. Green is the
# boundary holding, not the attack winning.
#
# Each probe names the scenario it reproduces and that scenario's honest verdict.
# Nothing here writes into the repo tree: it regenerates out/ (deterministic, byte
# for byte the committed reference) and works in a temp dir otherwise.
set -u
cd "$(dirname "$0")"
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT

python3 clubvote.py run out > /dev/null 2>&1 || { echo "  the run itself failed"; exit 1; }

record() { printf '%s\t%s\n' "$1" "$2" > "$W/v.$1"; }  # name <TAB> "OK|FAIL: why"

# regen <dir> <question>: an honestly-produced election whose only difference from
# the reference is the account it records. run() reads the module-level QUESTION at
# emit time, so overriding it yields a full, witnessed, anchored transcript that is
# valid from birth — the winner writing a partial minute at the time, not rewriting
# one after. That is exactly why the anchor cannot object: nothing was altered.
regen() {
  python3 - "$1" "$2" <<'PY' > /dev/null 2>&1
import sys
from pathlib import Path
sys.path.insert(0, ".")
import clubvote
clubvote.QUESTION = sys.argv[2]
clubvote.run(Path(sys.argv[1]))
PY
}

# 1. THE ARTFUL MINUTE (minutes-written-by-the-winner, strains). The recorded
# account claims the confirmation was uncontested; the ballots it certifies split
# 8-6. The verifier recomputes the tally and says VERIFIED — it never reads the
# account against the count, so a minute that contradicts its own election passes.
artful_minute() {
  regen "$W/artful" "Confirmation of Sandra Okafor as treasurer 2026-27 — routine, carried nem con."
  if ! python3 verify.py "$W/artful" > "$W/artful.log" 2>&1; then
    record artful-minute "FAIL the verifier REJECTED a valid ballot over its account — a completeness check now exists; re-examine minutes-written-by-the-winner"
    return
  fi
  local counts
  counts=$(python3 -c "import json;print([json.loads(l) for l in open('$W/artful/log.jsonl') if json.loads(l)['type']=='decision.tally-proof'][0]['body']['counts'])")
  record artful-minute "OK   VERIFIED — the minute says 'carried nem con'; the ballots it certifies say $counts, and the verifier never notices"
}

# 2. THE DECISION OFF THE RECORD (government-by-whatsapp, BREAKS). Two halves. The
# logged vote is ratification theatre for a choice already made off-minute — and it
# VERIFIES in full. And the strongest omission defence, drop, is shown to catch only
# the omission of an ANCHORED ballot: a decision that never entered the log has no
# head to anchor and no artifact to miss.
off_record() {
  regen "$W/decoy" "Ratify the committee's off-minute choice of treasurer — formal confirmation only."
  local decoy=false drop=false
  python3 verify.py "$W/decoy" > "$W/decoy.log" 2>&1 && decoy=true
  python3 clubvote.py tamper out "$W/drop" drop > /dev/null 2>&1
  python3 verify.py "$W/drop" > "$W/drop.log" 2>&1 || drop=true
  if $decoy && $drop; then
    record off-record "OK   the ratification theatre VERIFIED; drop (an anchored ballot erased) is caught — but a decision kept off the log has no head to anchor and nothing to catch"
  else
    record off-record "FAIL boundary moved: decoy-verified=$decoy drop-caught=$drop"
  fi
}

# 3. WHO TOLD THE MINISTER (who-told-the-minister, strains). There is no advice,
# submission, or reason artifact in what the prototype emits, and the verifier binds
# no outcome to one. Hidden advice has nothing to hide behind because nothing was
# ever bound: the attack has no artifact to attack.
who_told() {
  local types advice
  types=$(python3 -c "import json;print(sorted({json.loads(l)['type'] for l in open('out/log.jsonl')}))")
  advice=$(grep -ciE 'advice|rationale|reason|provenance|referred_by|submission|brief' verify.py)
  if ! printf '%s' "$types" | grep -qiE 'advice|submission|reason' && [ "$advice" -eq 0 ]; then
    record who-told "OK   no advice/reason entry is emitted and the verifier reads none ($advice checks) — an outcome is bound to no advice trail at all"
  else
    record who-told "FAIL an advice concept has appeared — types=$types advice-checks=$advice; re-examine who-told-the-minister"
  fi
}

# 4. THE LONG GRASS (the clock family, covered). The verifier checks timestamps for
# ORDER only; it enforces no deadline, window, or resolution. A decision deferred
# forever or resolved years late leaves it nothing to object to — it only ever
# judges an election that finished.
long_grass() {
  local order punctual
  order=$(grep -c 'non-decreasing' verify.py)
  punctual=$(grep -ciE 'deadline|overdue|punctual|elapsed|cast_ends|deliberation_ends|expired|too late' verify.py)
  if [ "$order" -ge 1 ] && [ "$punctual" -eq 0 ]; then
    record long-grass "OK   timestamps are checked for order only ('non-decreasing'); no deadline is enforced — a vote deferred forever or closed years late is invisible"
  else
    record long-grass "FAIL boundary moved: order-check=$order punctuality-checks=$punctual; re-examine the clock family"
  fi
}

artful_minute
off_record
who_told
long_grass

declare -A desc=(
  [artful-minute]="a partial account over a contested vote -> the verifier certifies the count, not the account (minutes-written-by-the-winner, strains)"
  [off-record]="the real decision taken off the log, the ballot a ratification -> only anchored omissions are caught (government-by-whatsapp, breaks)"
  [who-told]="the advice that shaped the outcome, unrecorded -> no artifact binds an outcome to advice (who-told-the-minister, strains)"
  [long-grass]="the decision deferred past the point of mattering -> order is checked, punctuality is not (the clock family, covered)"
)
ORDER="artful-minute off-record who-told long-grass"

echo
for name in $ORDER; do
  [ -f "$W/v.$name" ] || { echo "  FAIL $name — probe produced no verdict (it crashed)"; continue; }
done
reds=0
for name in $ORDER; do
  [ -f "$W/v.$name" ] || { reds=$((reds+1)); continue; }
  verdict=$(cut -f2 "$W/v.$name")
  printf '  %-13s %s\n               %s\n' "$name" "${desc[$name]}" "$verdict"
  [[ $verdict == OK* ]] || reds=$((reds+1))
done

echo
if [ "$reds" -eq 0 ]; then
  echo "BOUNDARY HOLDS: the ballot verifier certifies the count and is blind to all 4"
  echo "narrative-record attacks — exactly where the corpus places the waist. test.sh"
  echo "proves the ballot is defended; this proves the account is the reader's to judge."
else
  echo "$reds PROBE(S) MOVED — a narrative attack no longer passes the ballot verifier."
  echo "That is not a failure to fix here: it means the boundary shifted, and the named"
  echo "scenario's verdict should be revisited. The reason is on each moved line above."
  exit 1
fi
