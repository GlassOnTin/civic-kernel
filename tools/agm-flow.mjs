#!/usr/bin/env node
// The committee's half, end to end: a REAL election (persistent keys, OS
// randomness) run across separate processes — new, enrol, open, collect,
// close — with cast.js playing three voters whose secrets never touch the
// committee's machine. The independent Python verifier must certify the
// closed transcript, the counts must be right (Yes 2, No 1), a re-vote must
// supersede — and the demo-only tools (tamper, demo-collect) must REFUSE the
// real transcript, because its insiders' keys are nobody's to hold.
import { createRequire } from "module";
import { execFileSync } from "child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const Cast = require(path.join(ROOT, "cast.js"));
const CLUBVOTE = path.join(ROOT, "proto", "clubvote.py");

let failures = 0;
const say = (ok, what) => {
  console.log((ok ? "  ok   " : "  FAIL ") + what);
  if (!ok) failures++;
};
const py = args => execFileSync("python3", args, { stdio: "pipe" }).toString();
const pyFails = (args, wantRe) => {
  try { execFileSync("python3", args, { stdio: "pipe" }); return false; }
  catch (e) { return wantRe.test((e.stdout || "").toString() + (e.stderr || "").toString()); }
};

const tmp = mkdtempSync(path.join(tmpdir(), "agmflow-"));
const DIR = path.join(tmp, "agm"), PUB = path.join(DIR, "public");
try {
  // --- the committee opens shop; each step is its own process, so the keys
  // in private/keys.json are what carries the election between them
  py([CLUBVOTE, "agm", "new", DIR]);
  const voters = ["Asha Okonkwo", "Bill Feathers", "Cerys Wynn"].map(name => {
    const cred = Cast.newCredential();
    py([CLUBVOTE, "agm", "enrol", DIR, name, cred.voter_pub]);
    return { name, ...cred };
  });
  say(true, "new + 3 page-style enrolments across 4 separate processes (secrets stayed with the voters)");

  py([CLUBVOTE, "agm", "open", DIR, "2026-shadow-agm",
    "Shall the society adopt the revised water-rate schedule?", "Yes", "No"]);

  // --- the voters cast with cast.js against the published files alone
  const files = {};
  for (const f of ["roster.json", "trustees.json", "log.jsonl"]) {
    files[f] = readFileSync(path.join(PUB, f), "utf8");
  }
  const ballots = [];
  const castOne = async (v, choice, seq) => {
    const ctx = await Cast.prepare(files, v.nym_secret);
    ballots.push(await Cast.finalize(ctx, Cast.seal(ctx, choice), seq));
  };
  await castOne(voters[0], "Yes", 1);
  await castOne(voters[1], "No", 1);
  await castOne(voters[1], "Yes", 2); // Bill thinks overnight and re-votes
  await castOne(voters[2], "No", 1);
  const bpaths = ballots.map((b, i) => {
    const p = path.join(tmp, "ballot" + i + ".json");
    writeFileSync(p, JSON.stringify(b));
    return p;
  });
  say(true, "4 ballots cast from the published files alone (one is Bill's silent re-vote)");

  py([CLUBVOTE, "agm", "collect", DIR, ...bpaths]);
  say(pyFails([CLUBVOTE, "agm", "collect", DIR, bpaths[0]], /already in the box/),
    "re-collecting the same (tag, seq) is refused");
  say(pyFails([CLUBVOTE, "agm", "enrol", DIR, "Late Larry", Cast.newCredential().voter_pub],
    /enrolment is closed/),
    "enrolment after open is refused: the logged digest pinned the roster");

  const closeOut = py([CLUBVOTE, "agm", "close", DIR]);
  say(/Yes 2, No 1/.test(closeOut), "close tallies Yes 2, No 1 (the re-vote superseded)");
  say(pyFails([CLUBVOTE, "agm", "close", DIR], /already closed/), "a second close is refused");
  say(pyFails([CLUBVOTE, "agm", "collect", DIR, bpaths[0]], /cannot enter/),
    "a ballot after close is refused: the box is committed by digest");

  // --- the judge: verify.py, from the published directory alone
  let verdict = "", ok = true;
  try {
    verdict = py([path.join(ROOT, "proto", "verify.py"), PUB]);
  } catch (e) {
    ok = false;
    verdict = (e.stdout || "").toString();
  }
  say(ok && verdict.includes("VERIFIED"),
    "verify.py certifies the shadow AGM from public/ alone"
    + (ok ? "" : " :: " + (verdict.split("\n").find(l => l.includes("FAIL")) || "").trim()));
  say(verdict.includes("{'Yes': 2, 'No': 1}"),
    "verified counts match the close: {'Yes': 2, 'No': 1}");
  say(verdict.includes("4 valid ballots, 3 distinct linking tags counted, 1 silently superseded"),
    "recast policy verified: 4 ballots, 3 voters, 1 superseded");

  // --- the demo-only tools must refuse a real transcript
  say(pyFails([CLUBVOTE, "tamper", PUB, path.join(tmp, "t"), "log"], /not a demo-seed transcript/),
    "tamper refuses the real transcript: there is no insider to play");
  say(pyFails([CLUBVOTE, "collect", PUB, path.join(tmp, "c"), bpaths[0]], /not a demo-seed transcript/),
    "demo-collect refuses too: it would have to reforge history it holds no keys for");
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

if (failures) {
  console.log(failures + " agm-flow failure(s) — the committee's half does not hold");
  process.exit(1);
}
console.log("agm flow: a real election, run across processes, verified from its published files");
