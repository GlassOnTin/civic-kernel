#!/bin/bash
# The success test, executable. Green means: an independent verifier confirms the
# election from the artifacts alone; every tamper mode is caught; the run is
# byte-reproducible. Run from anywhere.
set -e
cd "$(dirname "$0")"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

echo "=== run: deterministic election -> out/"
python3 clubvote.py run out

echo; echo "=== verify: the honest transcript passes"
python3 verify.py out

echo; echo "=== reproducibility: a second run is byte-identical"
python3 clubvote.py run "$T/out2" > /dev/null
diff -r out "$T/out2"
echo "  ok   byte-identical"

echo; echo "=== tamper 1: rewrite history in the log (must FAIL)"
python3 clubvote.py tamper out "$T/log" log > /dev/null
if python3 verify.py "$T/log" > "$T/log.txt" 2>&1; then echo "MISSED TAMPER"; exit 1; fi
grep -m1 FAIL "$T/log.txt"

echo; echo "=== tamper 2: flip a counted ballot in the box (must FAIL)"
python3 clubvote.py tamper out "$T/box" box > /dev/null
if python3 verify.py "$T/box" > "$T/box.txt" 2>&1; then echo "MISSED TAMPER"; exit 1; fi
grep -m1 FAIL "$T/box.txt"

echo; echo "=== tamper 3: stuff the box with an unenrolled ballot (must FAIL)"
python3 clubvote.py tamper out "$T/forge" forge > /dev/null
if python3 verify.py "$T/forge" > "$T/forge.txt" 2>&1; then echo "MISSED TAMPER"; exit 1; fi
grep -m1 FAIL "$T/forge.txt"

echo; echo "=== tamper 4: flip a revealed choice at close time (must FAIL)"
python3 clubvote.py tamper out "$T/reveal" reveal > /dev/null
if python3 verify.py "$T/reveal" > "$T/reveal.txt" 2>&1; then echo "MISSED TAMPER"; exit 1; fi
grep -m1 FAIL "$T/reveal.txt"

echo; echo "ALL GREEN: verified honest run, 4/4 tampers caught, reproducible."
