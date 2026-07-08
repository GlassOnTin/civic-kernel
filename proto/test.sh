#!/bin/bash
# The success test, executable. Green means: an independent verifier confirms the
# election from the artifacts alone; every tamper is caught BY THE DEFENCE THE DESIGN
# NAMES, not merely caught; the run is byte-reproducible. Run from anywhere.
set -e
cd "$(dirname "$0")"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

# must_fail <mode> <substring of the FAIL line that defence must produce>
# Asserting the SPECIFIC failure matters: a tamper caught by the wrong check is a test
# that passes for the wrong reason, and would stay green if the named defence rotted.
must_fail() {
  local mode=$1 want=$2
  python3 clubvote.py tamper out "$T/$mode" "$mode" > /dev/null
  if python3 verify.py "$T/$mode" > "$T/$mode.txt" 2>&1; then
    echo "  MISSED TAMPER ($mode): the verifier certified a corrupted transcript"; exit 1
  fi
  if ! grep -q "FAIL.*$want" "$T/$mode.txt"; then
    echo "  WRONG DEFENCE ($mode): expected a FAIL matching '$want', but got:"
    grep FAIL "$T/$mode.txt"; exit 1
  fi
  grep -m1 "FAIL.*$want" "$T/$mode.txt"
}

echo "=== run: deterministic election -> out/"
python3 clubvote.py run out

echo; echo "=== verify: the honest transcript passes"
python3 verify.py out

echo; echo "=== reproducibility: a second run is byte-identical"
python3 clubvote.py run "$T/out2" > /dev/null
diff -r out "$T/out2"
echo "  ok   byte-identical"

echo; echo "=== tamper 1: rewrite history in the log (caught by Merkle consistency)"
must_fail log "head's root matches a strict prefix"

echo; echo "=== tamper 2: rewrite history AND regenerate the heads to match"
echo "===           (consistency now passes; caught only by the missing witnesses)"
must_fail rehead "co-signed by the log key and all"

echo; echo "=== tamper 3: ...and rewrite the manifest to declare it never had witnesses"
echo "===           (nothing inside the transcript disagrees; caught by the trust anchors)"
must_fail unwitness "manifest declares every witness"

echo; echo "=== tamper 4: flip a counted ballot in the box"
echo "===           (the voter's own signature covers the commitment; the shed cannot re-sign it)"
must_fail box "voter signature invalid"

echo; echo "=== tamper 5: stuff the box with an unenrolled ballot (caught by the roster)"
must_fail forge "voter not on roster"

echo; echo "=== tamper 6: flip a revealed choice at close time"
echo "===           (caught by the commitment it was cast under, sealed before the window shut)"
must_fail reveal "reveal does not open the cast commitment"

echo; echo "ALL GREEN: verified honest run, 6/6 tampers caught by their named defence, reproducible."
