#!/usr/bin/env node
// The full separation, end to end: a REAL election run across processes and
// SEVEN machines' worth of directories — the committee (agm), two witnesses
// (witness new/watch/sign), three trustees (trustee new/receive/share), the
// anchor (anchor new/watch/lodge), the register (issuer new/certify) — with
// cast.js playing three voters whose secrets never touch any of them. The
// committee holds ONE key, the log's: it cannot enrol, cannot tally, cannot
// anchor, cannot get a rewrite witnessed. The independent Python verifier
// must certify the closed transcript (Yes 2, No 1; 3 checkpointed heads),
// and the refusals must hold: a phantom credential dies at enrol, a witness
// handed a re-signed rewrite refuses on its memory, a corrupted cross-share
// on the Feldman check, a bogus tally share on its own CP proof — and the
// anchor, asked to reprint a rewritten close, refuses on the one thing it
// remembers: what it already printed.
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
const A1 = path.join(tmp, "a-star"), A2 = path.join(tmp, "a-stranger");
const REG = path.join(tmp, "register");
const T = i => path.join(tmp, "t" + i);
const REQ = path.join(DIR, "witness-request.json");
const AREQ = path.join(DIR, "anchor-request.json");
try {
  // --- two witnesses, three trustees, an anchor and the register: their own "machines"
  py([CLUBVOTE, "witness", "new", W1, "did:web:sheffield-allotment-federation.example#w1"]);
  py([CLUBVOTE, "witness", "new", W2, "did:web:meersbrook-allotments.example#w1"]);
  py([CLUBVOTE, "anchor", "new", A1, "did:web:sheffield-star.example#notices-1"]);
  py([CLUBVOTE, "issuer", "new", REG, "did:web:heeley-bank-allotments.example#roster-1"]);
  for (const i of [1, 2, 3]) py([CLUBVOTE, "trustee", "new", T(i), String(i)]);

  // cross-shares travel trustee-to-trustee, never via the committee; each is
  // Feldman-verified on receipt — and a corrupted one is refused
  const corrupted = path.join(tmp, "corrupted-share.json");
  const s21 = JSON.parse(readFileSync(path.join(T(2), "share-for-1.json"), "utf8"));
  writeFileSync(corrupted, JSON.stringify({ ...s21, value: s21.value.replace(/^./, c => c === "0" ? "1" : "0") }));
  say(pyFails([CLUBVOTE, "trustee", "receive", T(1), path.join(T(2), "deal.json"), corrupted],
    /Feldman/),
    "a corrupted cross-share is refused: it does not match the dealer's own commitments");
  for (const [i, j] of [[1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2]]) {
    py([CLUBVOTE, "trustee", "receive", T(i),
      path.join(T(j), "deal.json"), path.join(T(j), `share-for-${i}.json`)]);
  }
  say(true, "3 trustees dealt their own polynomials; 6 cross-shares exchanged directly, all Feldman-verified");

  // --- the committee opens shop holding only public halves
  py([CLUBVOTE, "agm", "new", DIR,
    path.join(W1, "card.json"), path.join(W2, "card.json"), path.join(A1, "card.json"),
    path.join(REG, "card.json"),
    path.join(T(1), "deal.json"), path.join(T(2), "deal.json"), path.join(T(3), "deal.json")]);
  const trust = JSON.parse(readFileSync(path.join(PUB, "trust.json"), "utf8"));
  const community = JSON.parse(readFileSync(path.join(PUB, "manifest.json"), "utf8")).community.id;
  const logPub = trust.keys[community + "#log-1"];
  const committeeKeys = JSON.parse(readFileSync(path.join(DIR, "private", "keys.json"), "utf8"));
  say(Object.keys(committeeKeys.keys).join(",") === "log"
    && Object.keys(committeeKeys.scalars).length === 0,
    "the committee's keys.json holds ONE key — the log's; even the enrolment pen is someone else's");
  py([CLUBVOTE, "witness", "watch", W1, community, logPub]);
  py([CLUBVOTE, "witness", "watch", W2, community, logPub]);
  py([CLUBVOTE, "anchor", "watch", A1, community, logPub]);

  // --- history cannot advance past an unwitnessed checkpoint
  say(pyFails([CLUBVOTE, "agm", "open", DIR, "x", "q", "a", "b"], /not yet co-signed/),
    "open refuses while the first head awaits its witnesses");

  py([CLUBVOTE, "witness", "sign", W1, REQ]);
  py([CLUBVOTE, "witness", "sign", W2, REQ]);
  const partial = py([CLUBVOTE, "agm", "witness-import", DIR, path.join(W1, "cosig-2.json")]);
  say(/still waiting on did:web:meersbrook/.test(partial),
    "a partial witness-import reports whom it is still waiting on");
  py([CLUBVOTE, "agm", "witness-import", DIR, path.join(W2, "cosig-2.json")]);

  // --- enrolment season: the member's device makes the key, the REGISTER certifies
  // it on its own machine, the committee can only verify and file
  const voters = ["Asha Okonkwo", "Bill Feathers", "Cerys Wynn"].map(name => {
    const cred = Cast.newCredential();
    py([CLUBVOTE, "issuer", "certify", REG, name, cred.voter_pub]);
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    py([CLUBVOTE, "agm", "enrol", DIR, path.join(REG, "cert-" + slug + ".json")]);
    return { name, ...cred };
  });
  // a phantom member needs the registrar's pen: a credential the register did not
  // sign — here a real one with the name swapped — is refused at the door
  const phantom = path.join(tmp, "cert-phantom.json");
  const realCert = JSON.parse(readFileSync(path.join(REG, "cert-asha-okonkwo.json"), "utf8"));
  writeFileSync(phantom, JSON.stringify({ ...realCert, member: "Phantom Pete" }));
  say(pyFails([CLUBVOTE, "agm", "enrol", DIR, phantom], /does not verify/),
    "a phantom member is refused: the committee cannot enrol anyone the register did not certify");
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
  py([CLUBVOTE, "issuer", "certify", REG, "Late Larry", Cast.newCredential().voter_pub]);
  say(pyFails([CLUBVOTE, "agm", "enrol", DIR, path.join(REG, "cert-late-larry.json")],
    /enrolment is closed/),
    "enrolment after open is refused even certified: the logged digest pinned the roster");

  // --- close commits the box and asks the trustees; it cannot tally alone
  const closeOut = py([CLUBVOTE, "agm", "close", DIR]);
  say(/No tally yet/.test(closeOut), "close commits digests but cannot tally — it holds no trustee secret");
  say(pyFails([CLUBVOTE, "agm", "close", DIR], /already closed/), "a second close is refused");
  say(pyFails([CLUBVOTE, "agm", "collect", DIR, bpaths[0]], /cannot enter/),
    "a ballot after close is refused: the box is committed by digest");

  // trustees 1 and 3 answer from their own machines (2's secretary is in
  // Whitby with the key card in a drawer — the threshold is the point)
  const TREQ = path.join(DIR, "tally-request.json");
  py([CLUBVOTE, "trustee", "share", T(1), TREQ]);
  py([CLUBVOTE, "trustee", "share", T(3), TREQ]);
  const bogus = path.join(tmp, "bogus-share.json");
  const s1 = JSON.parse(readFileSync(path.join(T(1), "share-1.json"), "utf8"));
  writeFileSync(bogus, JSON.stringify({ ...s1, share: s1.share.replace(/^./, c => c === "0" ? "1" : "0") }));
  say(pyFails([CLUBVOTE, "agm", "tally-import", DIR, bogus], /proof does not verify/),
    "a bogus tally share convicts itself at import: the Chaum-Pedersen proof cannot be faked");
  const tpartial = py([CLUBVOTE, "agm", "tally-import", DIR, path.join(T(1), "share-1.json")]);
  say(/quorum is not yet met/.test(tpartial),
    "a partial tally-import holds the share and waits for the quorum");
  const tallied = py([CLUBVOTE, "agm", "tally-import", DIR, path.join(T(3), "share-3.json")]);
  say(/Yes 2, No 1/.test(tallied),
    "2-of-3 trustees answered from their own machines: Yes 2, No 1 (the re-vote superseded)");

  // --- THE witness defence: the committee turns corrupt after the witnesses
  // signed the open head; every signature genuine, only the memory objects.
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

  // --- the real witnesses sign the honest close; the closing head goes to the anchor
  py([CLUBVOTE, "witness", "sign", W1, REQ]);
  py([CLUBVOTE, "witness", "sign", W2, REQ]);
  const done = py([CLUBVOTE, "agm", "witness-import", DIR,
    path.join(W1, "cosig-6.json"), path.join(W2, "cosig-6.json")]);
  say(/closing head/.test(done) && /anchor lodge/.test(done),
    "the closing head completes and is handed to the anchor — the committee cannot anchor it itself");

  py([CLUBVOTE, "anchor", "lodge", A1, AREQ]);
  const reprint = py([CLUBVOTE, "anchor", "lodge", A1, AREQ]);
  say(/reprinted/.test(reprint), "re-lodging the SAME head is a reprint, not a refusal (receipts are additive)");

  // --- THE anchor defence: after lodging, the committee rewrites history end to
  // end (every signature genuine) and asks the anchor for a fresh receipt. The
  // anchor's memory of what it printed is the drop defence, relocated to its owner.
  const rewrittenClose = path.join(tmp, "rewritten-anchor-request.json");
  execFileSync("python3", ["-c", `
import json, sys
from pathlib import Path
sys.path.insert(0, ${JSON.stringify(path.join(ROOT, "proto"))})
import clubvote as cv
d = Path(${JSON.stringify(DIR)})
cv.load_secrets(d / "private" / "keys.json")
entries = [json.loads(l) for l in (d / "public" / "log.jsonl").read_text().splitlines()]
e = next(x for x in entries if x["type"] == "decision.tally-proof")
e["body"]["counts"] = {"Yes": 1, "No": 2}
del e["sig"]
e["sig"] = cv.sign_over(cv.keypair("log"), cv.ACTORS["log"][0], e)
leaves = [cv.leaf_hash(cv.canon({k: v for k, v in x.items() if k != "sig"})) for x in entries]
body = {"log_id": cv.COMMUNITY, "size": len(entries),
        "root": "sha256:" + cv.merkle_root(leaves).hex(), "timestamp": entries[-1]["timestamp"]}
req = {"head": {**body, "sigs": [cv.sign_over(cv.keypair("log"), cv.ACTORS["log"][0], body)]}}
Path(${JSON.stringify(rewrittenClose)}).write_text(json.dumps(req))
`], { stdio: "pipe" });
  say(pyFails([CLUBVOTE, "anchor", "lodge", A1, rewrittenClose], /DIFFERENT|refusing to reprint/),
    "the anchor handed a rewritten closing head refuses: it already lodged this log, once, forever");

  // --- a stranger's receipt is refused at import (not in the trust anchors)
  py([CLUBVOTE, "anchor", "new", A2, "did:web:somewhere-else.example#notices-1"]);
  py([CLUBVOTE, "anchor", "watch", A2, community, logPub]);
  py([CLUBVOTE, "anchor", "lodge", A2, AREQ]);
  say(pyFails([CLUBVOTE, "agm", "anchor-import", DIR, path.join(A2, "receipt-6.json")],
    /do not name/),
    "a receipt from a key the trust anchors do not name is refused");

  const complete = py([CLUBVOTE, "agm", "anchor-import", DIR, path.join(A1, "receipt-6.json")]);
  say(/election is complete/.test(complete),
    "the Star's receipt lands and the election is complete");

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
    "verified counts match the tally: {'Yes': 2, 'No': 1}");
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
  console.log(failures + " agm-flow failure(s) — the separation does not hold");
  process.exit(1);
}
console.log("agm flow: register, witnesses, trustees, anchor — and a committee with one key — verified from the published files");
