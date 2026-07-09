#!/usr/bin/env node
// Parity test: verifier.js (the in-browser verifier) must reach the same
// verdicts as proto/verify.py, whose behaviour test.sh already pins tamper by
// tamper. Three cases cross the gate structure — honest (VERIFIED), a cheap
// log rewrite (NOT VERIFIED in section 3, ballots never checked), and the
// erased-ballot drop (internally flawless, NOT VERIFIED by section 8 alone).
// Also asserts the schemas embedded in verifier.js equal schema/*.schema.json
// — the page pins its standards, and this is what stops them drifting.
import { createRequire } from "module";
import { execFileSync } from "child_process";
import { mkdtempSync, readdirSync, readFileSync, rmSync } from "fs";
import { tmpdir } from "os";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const V = require(path.join(ROOT, "verifier.js"));

let failures = 0;
const say = (ok, what) => {
  console.log((ok ? "  ok   " : "  FAIL ") + what);
  if (!ok) failures++;
};

// --- the pinned schemas cannot drift from the repo's
const canon = V._internals.canonStr;
for (const name of ["log-entry", "manifest"]) {
  const onDisk = JSON.parse(readFileSync(path.join(ROOT, "schema", name + ".schema.json"), "utf8"));
  say(canon(V._internals.SCHEMAS[name]) === canon(onDisk),
    "embedded " + name + " schema equals schema/" + name + ".schema.json");
}

// --- verdict parity across the gate structure
function loadDir(dir) {
  const files = {};
  for (const f of readdirSync(dir)) files[f] = readFileSync(path.join(dir, f), "utf8");
  return files;
}
const tmp = mkdtempSync(path.join(tmpdir(), "parity-"));
try {
  const cases = [
    ["out", path.join(ROOT, "proto", "out"), "VERIFIED", null],
    ["log", null, "NOT VERIFIED", "3"],
    ["drop", null, "NOT VERIFIED", "8"],
  ];
  for (const [mode, fixed, wantVerdict, wantSection] of cases) {
    let dir = fixed;
    if (!dir) {
      dir = path.join(tmp, mode);
      execFileSync("python3", [path.join(ROOT, "proto", "clubvote.py"),
        "tamper", path.join(ROOT, "proto", "out"), dir, mode], { stdio: "pipe" });
    }
    const r = await V.verify(loadDir(dir));
    const badSections = [...new Set(r.checks.filter(c => !c.ok).map(c => c.section))];
    const sectionOk = wantSection === null
      ? badSections.length === 0
      : badSections.length === 1 && badSections[0] === wantSection;
    say(r.verdict === wantVerdict && sectionOk,
      mode + ": " + r.verdict + (badSections.length ? " (failing section " + badSections.join(",") + ")" : "")
      + " — expected " + wantVerdict + (wantSection ? " via section " + wantSection + " alone" : "")
      + " [" + (r.elapsedMs / 1000).toFixed(1) + "s]");
  }
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

if (failures) {
  console.log(failures + " parity failure(s) — verifier.js does not match the repo");
  process.exit(1);
}
console.log("parity: the browser verifier reaches the same verdicts, on the same checks");
