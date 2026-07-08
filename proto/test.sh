#!/bin/bash
# The success test, executable. Green means: an independent verifier confirms the
# election from the artifacts alone; every tamper is caught BY THE DEFENCE THE DESIGN
# NAMES, not merely caught; the run is byte-reproducible. Run from anywhere.
#
# Verifying an anonymous ballot is O(roster) — a ring signature per ballot — so a single
# verification is seconds and the whole suite would be minutes run end to end. But the
# honest check, the reproducibility run and all eleven tampers only READ out/, so they
# are independent: this script fans them across cores and aggregates the verdicts. The
# assertions are unchanged; only the scheduling is parallel.
set -u
cd "$(dirname "$0")"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

echo "=== run: deterministic election -> out/"
python3 clubvote.py run out || { echo "  the run itself failed"; exit 1; }

record() { printf '%s\t%s\n' "$1" "$2" > "$T/v.$1"; }  # name <TAB> "OK|FAIL: why"

honest() {
  if python3 verify.py out > "$T/honest.log" 2>&1
  then record honest "OK   the honest transcript verifies"
  else record honest "FAIL the honest transcript did NOT verify"; fi
}
reproduce() {
  python3 clubvote.py run "$T/out2" > /dev/null 2>&1
  if diff -rq out "$T/out2" > "$T/repro.log" 2>&1
  then record reproduce "OK   a second run is byte-identical"
  else record reproduce "FAIL a second run is not byte-reproducible"; fi
}
# must_fail: the verifier must REJECT the tamper, and a FAIL line must match the defence
# the design names. A tamper caught by the wrong check is a test that passes for the wrong
# reason and would stay green if the named defence rotted.
must_fail() { # mode  want
  local mode=$1 want=$2 line
  python3 clubvote.py tamper out "$T/$mode" "$mode" > /dev/null 2>&1
  if python3 verify.py "$T/$mode" > "$T/$mode.log" 2>&1; then
    record "$mode" "FAIL MISSED TAMPER: the verifier certified a corrupted transcript"
  elif line=$(grep -m1 "FAIL.*$want" "$T/$mode.log"); then
    record "$mode" "OK   ${line#*FAIL }"
  else
    record "$mode" "FAIL WRONG DEFENCE: expected a FAIL matching '$want', got: $(grep -m1 FAIL "$T/$mode.log")"
  fi
}

# Everything below reads out/ and nothing else — launch it all at once (one verify per
# core) and wait. `desc` is printed in a fixed order afterwards, so the output is
# deterministic however the jobs interleave.
honest & reproduce &
must_fail log        "head's root matches a strict prefix"                 &
must_fail rehead     "co-signed by the log key and all"                    &
must_fail unwitness  "manifest declares every witness"                     &
must_fail roster     "logged roster digest matches"                        &
must_fail box        "ring signature does not verify"                      &
must_fail stuff      "ring signature does not verify"                      &
must_fail doublevote "negated linking tag"                                 &
must_fail negate     "ciphertext component not in the prime-order subgroup" &
must_fail overvote   "validity proof"                                      &
must_fail share      "Chaum-Pedersen"                                      &
must_fail count      "announced counts match"                             &
wait

declare -A desc=(
  [honest]="the independent verifier confirms the election from artifacts alone"
  [reproduce]="a second run is byte-identical (deterministic transcript)"
  [log]="rewrite history in the log -> Merkle consistency"
  [rehead]="rewrite AND regenerate heads -> the missing witness co-signatures"
  [unwitness]="...and declare no witnesses -> the verifier's trust anchors"
  [roster]="rewrite the eligibility rule after the vote -> the witnessed roster digest"
  [box]="re-aim Sandra's ballot at Keith (7-7) -> the ring signature covers it"
  [stuff]="mint an extra ballot under full collusion -> no ring membership to prove"
  [doublevote]="negate a linking tag to vote twice -> the nullifier's subgroup check"
  [negate]="warp a ciphertext out of the group -> per-ballot subgroup membership"
  [overvote]="encrypt two votes, committee accepts -> the 0-or-1 validity proof"
  [share]="collude on a rigged decryption -> the Chaum-Pedersen share proof"
  [count]="collude on rigged counts -> the recount refutes itself"
)
ORDER="honest reproduce log rehead unwitness roster box stuff doublevote negate overvote share count"

echo; fails=0
for name in $ORDER; do
  [ -f "$T/v.$name" ] || { echo "  FAIL $name — task produced no verdict (it crashed)"; fails=$((fails+1)); continue; }
  verdict=$(cut -f2 "$T/v.$name")
  printf '  %-11s %s\n             %s\n' "$name" "${desc[$name]}" "$verdict"
  [[ $verdict == OK* ]] || fails=$((fails+1))
done

echo
if [ "$fails" -eq 0 ]; then
  echo "ALL GREEN: verified honest run, 11/11 tampers caught by their named defence, reproducible."
else
  echo "$fails FAILURE(S) — the reason is on each failing line above."
  exit 1
fi
