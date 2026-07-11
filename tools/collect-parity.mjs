#!/usr/bin/env node
// Collect parity: the verifier page's "hand in a ballot" step (collectBallot
// in verifier.js) must reach the same outcomes as the committee's real path —
// `clubvote.py collect` followed by verify.py, the Python judge — on the same
// ballots. Four ballots cross the outcome space: a proper re-cast (counted,
// 8-6 -> 9-5), a stale attempt number (accepted but superseded, count frozen),
// an exact duplicate (refused before judging), and a forged ballot (refused by
// the ring signature on both sides). Also asserts the page's pinned demo joint
// secret matches the election key the transcript's own trustee commitments
// derive — the gate that keeps the page from ever claiming to unseal a real
// election.
import { createRequire } from "module";
import { execFileSync } from "child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const V = require(path.join(ROOT, "verifier.js"));
const Cast = require(path.join(ROOT, "cast.js"));

let failures = 0;
const say = (ok, what) => {
  console.log((ok ? "  ok   " : "  FAIL ") + what);
  if (!ok) failures++;
};

const DEREK = "d4b128310c83f38cc4f3c64ae534757c90a7719d00c1126660debc2e2a17bec6c8c4e15ff338b8837d03bcf85c289a6709434f818abeee434ea2c812029715b8";

const OUT = path.join(ROOT, "proto", "out");
const files = {};
for (const f of ["roster.json", "trustees.json", "ballot-box.json", "log.jsonl"]) {
  files[f] = readFileSync(path.join(OUT, f), "utf8");
}

// --- the page's pinned joint secret must be THE demo secret: g^x must equal
// the election key derived from the transcript's own trustee commitments
const page = readFileSync(path.join(ROOT, "verifier.html"), "utf8");
const pin = (page.match(/DEMO_JOINT_SECRET\s*=\s*"([0-9a-f]+)"/) || [])[1];
say(!!pin, "verifier.html pins a DEMO_JOINT_SECRET");
const P = BigInt("0x" + [
  "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74",
  "020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F1437",
  "4FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED",
  "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF05",
  "98DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB",
  "9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B",
  "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718",
  "3995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF"].join(""));
function modpow(b, e, m) { b %= m; let r = 1n; while (e > 0n) { if (e & 1n) r = r * b % m; b = b * b % m; e >>= 1n; } return r; }
let hKey = 1n;
for (const tr of JSON.parse(files["trustees.json"]).trustees) {
  hKey = hKey * BigInt("0x" + tr.commitments[0]) % P;
}
say(pin && modpow(2n, BigInt("0x" + pin), P) === hKey,
  "g^(pinned joint secret) equals the election key the trustee commitments derive");

// --- the gate itself: a wrong secret must be refused as not-the-demo
const ctx = await Cast.prepare(files, DEREK);
const probe = await Cast.finalize(ctx, Cast.seal(ctx, ctx.options[0]), 6);
const gated = await V.collectBallot(files, JSON.stringify(probe), "deadbeef");
say(gated.demo === false, "a transcript whose election key is not g^secret is refused: the page cannot claim to unseal it");

// --- four ballots across the outcome space; each judged by both sides
const mySeqs = JSON.parse(files["ballot-box.json"]).ballots
  .filter(b => b.nullifier === ctx.tag).map(b => b.seq);
const maxSeq = Math.max(...mySeqs);
say(mySeqs.length > 0, "Derek's tag is in the reference box (seqs " + JSON.stringify(mySeqs) + ")");

const counted = probe;                                                        // seq 6: proper re-cast
const stale = await Cast.finalize(ctx, Cast.seal(ctx, ctx.options[0]), 1);    // seq 1: superseded on arrival
const dup = await Cast.finalize(ctx, Cast.seal(ctx, ctx.options[0]), maxSeq); // exact (tag, seq) duplicate
const forged = { ...counted, seq: counted.seq + 1 };                          // seq bumped after signing

function pythonSide(ballot) {
  // clubvote.py collect + verify.py; returns { collected, verified, output }
  const tmp = mkdtempSync(path.join(tmpdir(), "collectparity-"));
  try {
    const bpath = path.join(tmp, "ballot.json");
    writeFileSync(bpath, JSON.stringify(ballot));
    const dst = path.join(tmp, "collected");
    try {
      execFileSync("python3", [path.join(ROOT, "proto", "clubvote.py"), "collect", OUT, dst, bpath], { stdio: "pipe" });
    } catch (e) {
      return { collected: false, verified: false, output: (e.stdout || "") + (e.stderr || "") };
    }
    try {
      const out = execFileSync("python3", [path.join(ROOT, "proto", "verify.py"), dst], { stdio: "pipe" }).toString();
      return { collected: true, verified: true, output: out };
    } catch (e) {
      return { collected: true, verified: false, output: (e.stdout || "").toString() + (e.stderr || "").toString() };
    }
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}
const fmt = c => Object.entries(c).map(([k, v]) => `'${k}': ${v}`).join(", ");

// 1. counted: both sides accept, both read 9-5 where the reference reads 8-6
let browser = await V.collectBallot(files, JSON.stringify(counted), pin);
let python = pythonSide(counted);
say(browser.demo && browser.accepted && browser.counted, "counted case: the page accepts and counts (seq " + counted.seq + ")");
say(browser.before.counts["Sandra Okafor"] === 8 && browser.after.counts["Sandra Okafor"] === 9,
  "counted case: the page's total moves 8-6 -> 9-5");
say(python.collected && python.verified, "counted case: clubvote.py collect + verify.py accept the same ballot");
say(python.output.includes("{" + fmt(browser.after.counts) + "}"),
  "counted case: verify.py announces the exact counts the page computed (" + fmt(browser.after.counts) + ")");

// 2. stale: both sides accept, neither moves the count (the re-vote rule)
browser = await V.collectBallot(files, JSON.stringify(stale), pin);
python = pythonSide(stale);
say(browser.accepted && !browser.counted, "stale case: the page takes the ballot but marks it superseded (seq 1 under seq " + maxSeq + ")");
say(browser.after.counts["Sandra Okafor"] === 8 && browser.after.superseded === browser.before.superseded + 1,
  "stale case: the page's total is unchanged; one more superseded");
say(python.collected && python.verified, "stale case: the Python side accepts it too");
say(python.output.includes("{" + fmt(browser.after.counts) + "}")
  && python.output.includes(browser.after.superseded + " silently superseded"),
  "stale case: verify.py agrees — same counts, same superseded tally");

// 3. duplicate: both sides refuse before judging, same reason
browser = await V.collectBallot(files, JSON.stringify(dup), pin);
python = pythonSide(dup);
say(!browser.accepted && browser.duplicate && /higher attempt number/.test(browser.why),
  "duplicate case: the page refuses an exact (tag, seq) duplicate");
say(!python.collected && /already in the box/.test(python.output),
  "duplicate case: clubvote.py collect refuses the same ballot the same way");

// 4. forged: collect takes it (verify.py is the judge), and both judges name the ring signature
browser = await V.collectBallot(files, JSON.stringify(forged), pin);
python = pythonSide(forged);
say(!browser.accepted && /ring signature does not verify/.test(browser.why),
  "forged case: the page refuses on the ring signature");
say(python.collected && !python.verified && /ring signature does not verify/.test(python.output),
  "forged case: collect takes it, verify.py convicts it on the same check");

if (failures) {
  console.log(failures + " collect-parity failure(s) — the page's hand-in step does not match the Python judge");
  process.exit(1);
}
console.log("collect parity: what the page counts, refuses or convicts, the Python judge does too");
