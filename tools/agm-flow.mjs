#!/usr/bin/env node
// The committee's half, end to end, with SEPARATE witnesses: a real election
// (persistent keys, OS randomness) run across processes — witness new/watch,
// agm new/enrol/open/collect/close, witness sign, agm witness-import — with
// cast.js playing three voters whose secrets never touch the committee's
// machine, and two witness directories playing societies whose keys never
// touch it either. The independent Python verifier must certify the closed
// transcript (Yes 2, No 1; 3 checkpointed heads), a re-vote must supersede,
// and the refusals must hold — above all the witness's own: handed a
// rewritten history with valid log signatures end to end, it must refuse,
// because its memory of the last co-signed head is the defence.
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
const W1 = path.join(tmp, "w-fed"), W2 = path.join(tmp, "w-meers"), W3 = path.join(tmp, "w-stranger");
const REQ = path.join(DIR, "witness-request.json");
try {
  // --- two witnesses are born on their own "machines"; the committee gets cards
  py([CLUBVOTE, "witness", "new", W1, "did:web:sheffield-allotment-federation.example#w1"]);
  py([CLUBVOTE, "witness", "new", W2, "did:web:meersbrook-allotments.example#w1"]);
  py([CLUBVOTE, "agm", "new", DIR, path.join(W1, "card.json"), path.join(W2, "card.json")]);
  const trust = JSON.parse(readFileSync(path.join(PUB, "trust.json"), "utf8"));
  const community = JSON.parse(readFileSync(path.join(PUB, "manifest.json"), "utf8")).community.id;
  const logPub = trust.keys[community + "#log-1"];
  const committeeKeys = JSON.parse(readFileSync(path.join(DIR, "private", "keys.json"), "utf8"));
  say(!("witness-fed" in committeeKeys.keys) && !("witness-meers" in committeeKeys.keys),
    "the committee's keys.json holds NO witness key — the separation is real");
  py([CLUBVOTE, "witness", "watch", W1, community, logPub]);
  py([CLUBVOTE, "witness", "watch", W2, community, logPub]);

  // --- history cannot advance past an unwitnessed checkpoint
  say(pyFails([CLUBVOTE, "agm", "open", DIR, "x", "q", "a", "b"], /not yet co-signed/),
    "open refuses while the first head awaits its witnesses");

  py([CLUBVOTE, "witness", "sign", W1, REQ]);
  py([CLUBVOTE, "witness", "sign", W2, REQ]);
  const partial = py([CLUBVOTE, "agm", "witness-import", DIR, path.join(W1, "cosig-2.json")]);
  say(/still waiting on did:web:meersbrook/.test(partial),
    "a partial import reports whom it is still waiting on");
  py([CLUBVOTE, "agm", "witness-import", DIR, path.join(W2, "cosig-2.json")]);

  // --- enrolment season, then open (its head witnessed in turn)
  const voters = ["Asha Okonkwo", "Bill Feathers", "Cerys Wynn"].map(name => {
    const cred = Cast.newCredential();
    py([CLUBVOTE, "agm", "enrol", DIR, name, cred.voter_pub]);
    return { name, ...cred };
  });
  py([CLUBVOTE, "agm", "open", DIR, "2026-shadow-agm",
    "Shall the society adopt the revised water-rate schedule?", "Yes", "No"]);
  py([CLUBVOTE, "witness", "sign", W1, REQ]);
  py([CLUBVOTE, "witness", "sign", W2, REQ]);
  py([CLUBVOTE, "agm", "witness-import", DIR,
    path.join(W1, "cosig-4.json"), path.join(W2, "cosig-4.json")]);
  say(true, "new, open: two checkpoints co-signed from the witnesses' own directories");

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

  // --- THE defence: the committee turns corrupt after the witnesses signed the
  // open head. It rewrites the question, re-signs every artifact with the log
  // key it genuinely holds, and asks the witnesses to co-sign the result. Every
  // signature verifies; the root matches the rewritten log. Only the witness's
  // MEMORY of the head it co-signed at size 4 objects.
  const rewritten = path.join(tmp, "rewritten-request.json");
  execFileSync("python3", ["-c", `
import json, sys
from pathlib import Path
sys.path.insert(0, ${JSON.stringify(path.join(ROOT, "proto"))})
import clubvote as cv
d = Path(${JSON.stringify(DIR)})
cv.load_secrets(d / "private" / "keys.json")
entries = [json.loads(l) for l in (d / "public" / "log.jsonl").read_text().splitlines()]
e = next(x for x in entries if x["type"] == "decision.opened")
e["body"]["question"] = "Shall the treasurer serve for life?"
del e["sig"]
e["sig"] = cv.sign_over(cv.keypair("log"), cv.ACTORS["log"][0], e)
leaves = [cv.leaf_hash(cv.canon({k: v for k, v in x.items() if k != "sig"})) for x in entries]
body = {"log_id": cv.COMMUNITY, "size": len(entries),
        "root": "sha256:" + cv.merkle_root(leaves).hex(), "timestamp": entries[-1]["timestamp"]}
req = {"head": {**body, "sigs": [cv.sign_over(cv.keypair("log"), cv.ACTORS["log"][0], body)]},
       "entries": entries}
Path(${JSON.stringify(rewritten)}).write_text(json.dumps(req))
`], { stdio: "pipe" });
  say(pyFails([CLUBVOTE, "witness", "sign", W1, rewritten], /not an extension of the history/),
    "a witness handed a re-signed REWRITE refuses: its memory of size 4 is the defence");

  // --- a stranger's co-signature is refused at import (not in the trust anchors)
  py([CLUBVOTE, "witness", "new", W3, "did:web:somewhere-else.example#w1"]);
  py([CLUBVOTE, "witness", "watch", W3, community, logPub]);
  py([CLUBVOTE, "witness", "sign", W3, REQ]);
  say(pyFails([CLUBVOTE, "agm", "witness-import", DIR, path.join(W3, "cosig-6.json")],
    /do not name/),
    "a co-signature from a key the trust anchors do not name is refused");

  // --- the real witnesses sign the honest close; the anchor follows
  py([CLUBVOTE, "witness", "sign", W1, REQ]);
  py([CLUBVOTE, "witness", "sign", W2, REQ]);
  const done = py([CLUBVOTE, "agm", "witness-import", DIR,
    path.join(W1, "cosig-6.json"), path.join(W2, "cosig-6.json")]);
  say(/fully witnessed and anchored/.test(done), "the closing head completes and the anchor follows it");

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
  say(verdict.includes("consistency, 3 heads"),
    "three checkpointed heads (new, open, close), each co-signed by both witnesses");
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
console.log("agm flow: a real election with separate witnesses, verified from its published files");
