#!/bin/bash
# The success test, executable. Green means: an independent verifier confirms the
# election from the artifacts alone; every tamper is caught BY THE DEFENCE THE DESIGN
# NAMES, not merely caught; the run is byte-reproducible. Run from anywhere.
#
# Verifying an anonymous ballot is O(roster) — a ring signature per ballot — so a single
# verification is seconds and the whole suite would be minutes run end to end. But the
# honest check, the reproducibility run and all twelve tampers only READ out/, so they
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
# --real: same election under OS randomness. The verifier must pass unchanged (it works
# from the artifacts alone, so it cannot care where the secrets came from), and the
# transcript must actually differ from the seeded one (the flag did something).
real() {
  python3 clubvote.py run "$T/real" --real > /dev/null 2>&1
  if ! python3 verify.py "$T/real" > "$T/real.log" 2>&1
  then record real "FAIL the --real transcript did NOT verify"
  elif diff -q out/ballot-box.json "$T/real/ballot-box.json" > /dev/null 2>&1
  then record real "FAIL --real reproduced the seeded ballot box (the flag had no effect)"
  else record real "OK   verifies from artifacts alone; ballots differ from the seeded run"; fi
}
# The same checks ship as a browser page (../verifier.html). Its engine must reach
# the same verdicts as verify.py, and its pinned copies of the waist schemas must
# equal the repo's — tools/verify-parity.mjs asserts both. Needs node (CI has it).
parity() {
  if command -v node > /dev/null 2>&1; then
    if node ../tools/verify-parity.mjs > "$T/parity.log" 2>&1
    then record parity "OK   verifier.js reaches the same verdicts on the same checks; embedded schemas match"
    else record parity "FAIL browser-verifier parity: $(grep -m1 FAIL "$T/parity.log")"; fi
  else
    record parity "OK   SKIPPED here — node not installed; CI runs this"
  fi
}
# The casting page (../cast.html) is held to the Python verifier the same way: a
# ballot its engine builds, collected into the reference transcript, must verify
# AND count — tally 8-6 -> 9-5, one voter switched, nothing stuffed.
castpage() {
  if command -v node > /dev/null 2>&1; then
    if node ../tools/cast-parity.mjs > "$T/castpage.log" 2>&1
    then record castpage "OK   a cast.js ballot, collected, verifies in verify.py and counts (8-6 -> 9-5)"
    else record castpage "FAIL cast-page parity: $(grep -m1 FAIL "$T/castpage.log")"; fi
  else
    record castpage "OK   SKIPPED here — node not installed; CI runs this"
  fi
}
# The verifier page's hand-in step (collectBallot) is held to the committee's real
# path the same way: four ballots — a proper re-cast, a stale attempt number, an
# exact duplicate, a forged one — must meet the same outcome in the browser engine
# as in `clubvote.py collect` + verify.py, and the page's pinned demo joint secret
# must equal the election key the trustee commitments derive.
collectpage() {
  if command -v node > /dev/null 2>&1; then
    if node ../tools/collect-parity.mjs > "$T/collectpage.log" 2>&1
    then record collectpage "OK   the page's hand-in step matches collect + verify.py on all four outcomes"
    else record collectpage "FAIL collect-page parity: $(grep -m1 FAIL "$T/collectpage.log")"; fi
  else
    record collectpage "OK   SKIPPED here — node not installed; CI runs this"
  fi
}
# The entitlements page (../owed.html) is held to its independent judge: two engines
# (owed.js, entitlements/judge.py) share the rules corpus and nothing else, and must
# produce identical claim-traces over the persona battery; the corpus embedded in the
# page must equal the files; no network API may appear in the page or engine at all;
# and a stale tax year fails loudly unless acknowledged.
owedpage() {
  if command -v node > /dev/null 2>&1; then
    if node ../tools/owed-parity.mjs > "$T/owedpage.log" 2>&1
    then record owedpage "OK   two engines, one corpus, identical traces over the battery; no network API exists in the page"
    else record owedpage "FAIL owed parity: $(grep -m1 FAIL "$T/owedpage.log")"; fi
  else
    record owedpage "OK   SKIPPED here — node not installed; CI runs this"
  fi
}
# The witness page (../witness.html) is held to `clubvote.py witness` the same way:
# a real agm election runs with one witness on the browser engine — its card, its
# co-signatures and its witness FILE must be interchangeable with the Python
# witness's (the file is alternated between the two implementations), verify.py must
# certify the result, and the re-signed-rewrite refusal must hold in the browser on
# the same memory, with the same reason.
witnesspage() {
  if command -v node > /dev/null 2>&1; then
    if node ../tools/witness-parity.mjs > "$T/witnesspage.log" 2>&1
    then record witnesspage "OK   the browser witness and the Python witness are the same witness (card, cosigs, file, refusals)"
    else record witnesspage "FAIL witness-page parity: $(grep -m1 FAIL "$T/witnesspage.log")"; fi
  else
    record witnesspage "OK   SKIPPED here — node not installed; CI runs this"
  fi
}
# A REAL election, every party separated: the register (issuer new/certify), witnesses
# (new/watch/sign), trustees (new/receive/share), the anchor (new/watch/lodge), and a
# committee left holding one key — the log's (agm ... plus enrol-by-credential and the
# three imports) — across separate processes and directories, cast.js voters, verify.py
# the judge. The named defences: a phantom credential dies at enrol; a re-signed
# rewrite on the witness's memory; a corrupted cross-share on the Feldman check; a
# bogus tally share on its CP proof; a rewritten close on the anchor's memory.
agmflow() {
  if command -v node > /dev/null 2>&1; then
    if node ../tools/agm-flow.mjs > "$T/agmflow.log" 2>&1
    then record agmflow "OK   every party on its own keys; the committee holds one (the log's); every refusal holds"
    else record agmflow "FAIL agm flow: $(grep -m1 FAIL "$T/agmflow.log")"; fi
  else
    record agmflow "OK   SKIPPED here — node not installed; CI runs this"
  fi
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
honest & reproduce & real & parity & castpage & collectpage & witnesspage & owedpage & agmflow &
must_fail log        "head's root matches a strict prefix"                 &
must_fail rehead     "co-signed by the log key and all"                    &
must_fail unwitness  "manifest declares every witness"                     &
must_fail roster     "logged roster digest matches"                        &
must_fail box        "ring signature does not verify"                      &
must_fail stuff      "ring signature does not verify"                      &
must_fail doublevote "negated linking tag"                                 &
must_fail smuggle    "ciphertext component not in the prime-order subgroup" &
must_fail overvote   "validity proof"                                      &
must_fail share      "Chaum-Pedersen"                                      &
must_fail count      "announced counts match"                              &
must_fail drop       "anchored outside the collusion set"                  &
wait

declare -A desc=(
  [honest]="the independent verifier confirms the election from artifacts alone"
  [reproduce]="a second run is byte-identical (deterministic transcript)"
  [real]="the same election under OS randomness (--real) -> same verifier, different bytes"
  [log]="rewrite history in the log -> Merkle consistency"
  [rehead]="rewrite AND regenerate heads -> the missing witness co-signatures"
  [unwitness]="...and declare no witnesses -> the verifier's trust anchors"
  [roster]="rewrite the eligibility rule after the vote -> the witnessed roster digest"
  [box]="re-aim Sandra's ballot at Keith (7-7) -> the ring signature covers it"
  [stuff]="mint an extra ballot under full collusion -> no ring membership to prove"
  [doublevote]="negate a linking tag to vote twice -> the nullifier's subgroup check"
  [smuggle]="slip a malformed ciphertext in past the CDS proof -> ciphertext subgroup check"
  [overvote]="encrypt two votes, committee accepts -> the 0-or-1 validity proof"
  [share]="collude on a rigged decryption -> the Chaum-Pedersen share proof"
  [count]="collude on rigged counts -> the recount refutes itself"
  [drop]="erase the recast from history, nothing forged -> the anchored closing head"
  [parity]="the in-browser verifier (verifier.html) agrees with verify.py"
  [castpage]="a ballot built by the casting page (cast.html) -> collected, verified, counted"
  [collectpage]="the verifier page's hand-in step -> same outcomes as collect + verify.py"
  [witnesspage]="the witness page's engine -> interchangeable with clubvote.py witness, rewrite refused"
  [owedpage]="the entitlements page's engine -> identical traces to the independent judge; no network API"
  [agmflow]="a real election, every party separated (issuer + witness + trustee + anchor + agm)"
)
ORDER="honest reproduce real parity castpage collectpage witnesspage owedpage agmflow log rehead unwitness roster box stuff doublevote smuggle overvote share count drop"

echo; fails=0
for name in $ORDER; do
  [ -f "$T/v.$name" ] || { echo "  FAIL $name — task produced no verdict (it crashed)"; fails=$((fails+1)); continue; }
  verdict=$(cut -f2 "$T/v.$name")
  printf '  %-11s %s\n             %s\n' "$name" "${desc[$name]}" "$verdict"
  [[ $verdict == OK* ]] || fails=$((fails+1))
done

echo
if [ "$fails" -eq 0 ]; then
  echo "ALL GREEN: verified honest run, 12/12 tampers caught by their named defence, reproducible."
else
  echo "$fails FAILURE(S) — the reason is on each failing line above."
  exit 1
fi
