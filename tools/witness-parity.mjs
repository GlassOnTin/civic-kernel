#!/usr/bin/env node
// Witness parity: the browser witness engine (witness.js, used by
// witness.html) must be interchangeable with `clubvote.py witness` — same
// card, same witness file, same co-signature, same refusals. A real agm
// election runs with one CLI witness and one browser witness: the committee
// must accept the browser witness's card at `agm new` and its co-signatures
// at every checkpoint, and verify.py must certify the closed election. The
// witness FILE itself is alternated between the two implementations across
// checkpoints (browser -> CLI -> browser), so the memory each keeps is
// proven to be the same memory. And THE defence must hold in the browser:
// a rewrite re-signed end to end with the genuine log key is refused on the
// witness's memory, with the same reason the Python witness gives.
import { createRequire } from "module";
import { execFileSync } from "child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const Cast = require(path.join(ROOT, "cast.js"));
const W = require(path.join(ROOT, "witness.js"));
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
const refuses = async (fn, wantRe) => {
  try { await fn(); return false; } catch (e) { return wantRe.test(e.message); }
};

if (!(await W.edSupported())) {
  console.log("  FAIL this Node lacks WebCrypto Ed25519 — the witness engine cannot run");
  process.exit(1);
}

const tmp = mkdtempSync(path.join(tmpdir(), "witnessparity-"));
const DIR = path.join(tmp, "agm"), PUB = path.join(DIR, "public");
const W1 = path.join(tmp, "w-fed");     // clubvote.py witness
const W2 = path.join(tmp, "w-meers");   // witness.js — the browser engine
const A1 = path.join(tmp, "a-star");
const REG = path.join(tmp, "register");
const T = i => path.join(tmp, "t" + i);
const REQ = path.join(DIR, "witness-request.json");
const W2STATE = path.join(W2, "witness.json");
// the page's downloads, simulated: the same files clubvote.py witness keeps
const saveState = s => writeFileSync(W2STATE, JSON.stringify(s, null, 1) + "\n");
const loadState = () => JSON.parse(readFileSync(W2STATE, "utf8"));
const browserSign = async () => {
  const { cosig, state } = await W.sign(loadState(), readFileSync(REQ, "utf8"));
  saveState(state); // the page hands back an updated witness file; "keep the new one"
  const p = path.join(W2, "cosig-" + cosig.head.size + ".json");
  writeFileSync(p, JSON.stringify(cosig, null, 1) + "\n");
  return p;
};

try {
  // --- one witness per implementation, on their own "machines"
  py([CLUBVOTE, "witness", "new", W1, "did:web:sheffield-allotment-federation.example#w1"]);
  mkdirSync(W2, { recursive: true });
  say(await refuses(() => W.newWitness("did:web:no-fragment.example"), /key fragment/),
    "a key id without a fragment is refused, as in the CLI");
  const born = await W.newWitness("did:web:meersbrook-allotments.example#w1");
  saveState(born.state);
  writeFileSync(path.join(W2, "card.json"), JSON.stringify(born.card, null, 1) + "\n");
  say(/^[0-9a-f]{64}$/.test(born.state.priv) && born.card.witness.includes("#"),
    "the browser witness is born: raw-seed witness file + card, clubvote.py's own formats");

  // --- the rest of the ceremony cast: anchor, register, three trustees
  py([CLUBVOTE, "anchor", "new", A1, "did:web:sheffield-star.example#notices-1"]);
  py([CLUBVOTE, "issuer", "new", REG, "did:web:heeley-bank-allotments.example#roster-1"]);
  for (const i of [1, 2, 3]) py([CLUBVOTE, "trustee", "new", T(i), String(i)]);
  for (const [i, j] of [[1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2]]) {
    py([CLUBVOTE, "trustee", "receive", T(i),
      path.join(T(j), "deal.json"), path.join(T(j), `share-for-${i}.json`)]);
  }

  // --- the committee accepts the browser witness's card like any other
  py([CLUBVOTE, "agm", "new", DIR,
    path.join(W1, "card.json"), path.join(W2, "card.json"), path.join(A1, "card.json"),
    path.join(REG, "card.json"),
    path.join(T(1), "deal.json"), path.join(T(2), "deal.json"), path.join(T(3), "deal.json")]);
  const trust = JSON.parse(readFileSync(path.join(PUB, "trust.json"), "utf8"));
  say(trust.witnesses.includes("did:web:meersbrook-allotments.example"),
    "agm new accepted the browser witness's card into the trust anchors");
  const community = JSON.parse(readFileSync(path.join(PUB, "manifest.json"), "utf8")).community.id;
  const logPub = trust.keys[community + "#log-1"];

  // --- the ceremony: the log key arrives out of band, in both implementations
  py([CLUBVOTE, "witness", "watch", W1, community, logPub]);
  say(await refuses(() => Promise.resolve(W.watch(loadState(), community, "dG9vc2hvcnQ")), /raw Ed25519 public key/),
    "the ceremony refuses a key that is not 32 raw bytes, as in the CLI");
  saveState(W.watch(loadState(), community, logPub));
  py([CLUBVOTE, "anchor", "watch", A1, community, logPub]);

  // --- a request must not be signable before the ceremony... (fresh state, no watch)
  say(await refuses(() => W.sign(born.state, readFileSync(REQ, "utf8")), /watches nobody yet/),
    "signing before the ceremony is refused: the witness watches nobody yet");

  // --- checkpoint 1 (size 2): browser signs, committee imports
  py([CLUBVOTE, "witness", "sign", W1, REQ]);
  const c2 = await browserSign();
  say(JSON.parse(readFileSync(c2, "utf8")).sig.alg === "ed25519",
    "the browser witness co-signed head 2 from the request file alone");
  py([CLUBVOTE, "agm", "witness-import", DIR, path.join(W1, "cosig-2.json"), c2]);
  say(true, "witness-import accepted the browser co-signature next to the CLI one (head 2 published)");

  // --- enrolment and open: checkpoint 2 (size 4). The browser-written witness
  // file is handed to the CLI IMPLEMENTATION this round — same file, same memory.
  const voters = ["Asha Okonkwo", "Bill Feathers"].map(name => {
    const cred = Cast.newCredential();
    py([CLUBVOTE, "issuer", "certify", REG, name, cred.voter_pub]);
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    py([CLUBVOTE, "agm", "enrol", DIR, path.join(REG, "cert-" + slug + ".json")]);
    return { name, ...cred };
  });
  py([CLUBVOTE, "agm", "open", DIR, "2026-shadow-agm",
    "Shall the society adopt the revised water-rate schedule?", "Yes", "No"]);
  py([CLUBVOTE, "witness", "sign", W1, REQ]);
  py([CLUBVOTE, "witness", "sign", W2, REQ]); // clubvote.py, on the browser-born file
  py([CLUBVOTE, "agm", "witness-import", DIR,
    path.join(W1, "cosig-4.json"), path.join(W2, "cosig-4.json")]);
  say(loadState().last.size === 4,
    "clubvote.py signed head 4 using the browser-born witness file, and updated its memory in place");

  // --- votes, close, tally (the committee still cannot tally alone)
  const files = {};
  for (const f of ["roster.json", "trustees.json", "log.jsonl"]) {
    files[f] = readFileSync(path.join(PUB, f), "utf8");
  }
  const bpaths = [];
  const castOne = async (v, choice, seq) => {
    const ctx = await Cast.prepare(files, v.nym_secret);
    const b = await Cast.finalize(ctx, Cast.seal(ctx, choice), seq);
    const p = path.join(tmp, "ballot" + bpaths.length + ".json");
    writeFileSync(p, JSON.stringify(b));
    bpaths.push(p);
  };
  await castOne(voters[0], "Yes", 1);
  await castOne(voters[1], "No", 1);
  py([CLUBVOTE, "agm", "collect", DIR, ...bpaths]);
  py([CLUBVOTE, "agm", "close", DIR]);
  py([CLUBVOTE, "trustee", "share", T(1), path.join(DIR, "tally-request.json")]);
  py([CLUBVOTE, "trustee", "share", T(3), path.join(DIR, "tally-request.json")]);
  py([CLUBVOTE, "agm", "tally-import", DIR,
    path.join(T(1), "share-1.json"), path.join(T(3), "share-3.json")]);

  // --- THE defence, in the browser: the committee rewrites the question,
  // re-signs the entry AND a fresh head with the GENUINE log key. Every
  // signature verifies; only the witness's memory objects — and it must.
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
  say(await refuses(() => W.sign(loadState(), readFileSync(rewritten, "utf8")),
    /not an extension of the history I co-signed at size 4/),
    "THE defence holds in the browser: a re-signed rewrite is refused on the witness's memory of size 4");
  say(pyFails([CLUBVOTE, "witness", "sign", W1, rewritten], /not an extension of the history/),
    "and the CLI witness refuses the same rewrite with the same reason");

  // --- the other refusals, same reasons as the CLI
  const honest = readFileSync(REQ, "utf8");
  say(await refuses(() => W.sign(W.watch(loadState(), "did:web:someone-else.example", logPub), honest),
    /not the community I watch/),
    "a head from the wrong community is refused");
  const wrongKey = W.watch(loadState(), community, born.card.pub); // a 32-byte key that is NOT the log's
  say(await refuses(() => W.sign(wrongKey, honest), /not signed by the log key I was given at the ceremony/),
    "a head not signed by the ceremony key is refused");
  const truncated = JSON.parse(honest);
  truncated.entries = truncated.entries.slice(0, -1);
  say(await refuses(() => W.sign(loadState(), truncated), /does not root the log/),
    "a head that does not root the log it came with is refused");

  // --- checkpoint 3 (size 6, the closing head): back to the BROWSER engine,
  // reading the memory clubvote.py last wrote. Both directions now proven.
  py([CLUBVOTE, "witness", "sign", W1, REQ]);
  const c6 = await browserSign();
  const done = py([CLUBVOTE, "agm", "witness-import", DIR, path.join(W1, "cosig-6.json"), c6]);
  say(/closing head/.test(done),
    "the browser witness co-signed the closing head, reading the memory the CLI last wrote");
  say(loadState().last.size === 6, "its memory moved to size 6 — the file the page tells you to keep");

  // --- anchor, and the judge
  py([CLUBVOTE, "anchor", "lodge", A1, path.join(DIR, "anchor-request.json")]);
  py([CLUBVOTE, "agm", "anchor-import", DIR, path.join(A1, "receipt-6.json")]);
  let verdict = "", ok = true;
  try {
    verdict = py([path.join(ROOT, "proto", "verify.py"), PUB]);
  } catch (e) {
    ok = false;
    verdict = (e.stdout || "").toString();
  }
  say(ok && verdict.includes("VERIFIED") && verdict.includes("consistency, 3 heads"),
    "verify.py certifies the election: 3 heads, every one co-signed by a browser witness"
    + (ok ? "" : " :: " + (verdict.split("\n").find(l => l.includes("FAIL")) || "").trim()));
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

if (failures) {
  console.log(failures + " witness-parity failure(s) — witness.js is not interchangeable with clubvote.py witness");
  process.exit(1);
}
console.log("witness parity: the browser witness and the Python witness are the same witness");
