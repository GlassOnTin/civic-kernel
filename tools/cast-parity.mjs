#!/usr/bin/env node
// Cast parity: a ballot built by cast.js (the browser casting engine) must be
// accepted by proto/verify.py (the independent Python verifier) inside a real
// transcript — and must actually COUNT. Derek's demo secret re-casts for
// Sandra; after `clubvote.py collect` the verified tally must read 9-5 where
// the reference reads 8-6: one voter switched, nothing was stuffed.
//
// This test also plays the "other device" of cast-or-audit: it re-encrypts a
// challenged envelope's opened (choice, r) with its own arithmetic and checks
// the ciphertext matches — the check a voter would do away from the page.
import { createRequire } from "module";
import { execFileSync } from "child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const Cast = require(path.join(ROOT, "cast.js"));

let failures = 0;
const say = (ok, what) => {
  console.log((ok ? "  ok   " : "  FAIL ") + what);
  if (!ok) failures++;
};

// Derek's nym secret is derivable from the public demo seed — the declared
// zero-privacy property of the reference run (and a button on verifier.html).
const DEREK = "d4b128310c83f38cc4f3c64ae534757c90a7719d00c1126660debc2e2a17bec6c8c4e15ff338b8837d03bcf85c289a6709434f818abeee434ea2c812029715b8";

const OUT = path.join(ROOT, "proto", "out");
const files = {};
for (const f of ["roster.json", "trustees.json", "log.jsonl"]) {
  files[f] = readFileSync(path.join(OUT, f), "utf8");
}

// --- an unenrolled key must be refused: no membership, no ballot
const fresh = Cast.newCredential(files);
let refused = false;
try { await Cast.prepare(files, fresh.nym_secret); } catch (e) { refused = /not on the roster/.test(e.message); }
say(refused, "a fresh (unenrolled) credential is refused: no membership to prove");

// --- Derek prepares; the page must find him on the roster
const ctx = await Cast.prepare(files, DEREK);
say(ctx.member === "Derek Wainwright", "the demo secret resolves to Derek's roster entry");

// --- cast-or-audit, with THIS test as the other device: the opened record
// must re-encrypt to the challenged ciphertext under independent arithmetic
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

const testEnv = Cast.seal(ctx, ctx.options[1]);
const opened = Cast.challengeOpen(ctx, testEnv);
const m = opened.opened_choice === ctx.options[0] ? 1n : 0n;
const r = BigInt("0x" + opened.opened_r);
const h = ctx.h;
say(BigInt("0x" + opened.ciphertext.c1) === modpow(2n, r, P)
  && BigInt("0x" + opened.ciphertext.c2) === (modpow(2n, m, P) * modpow(h, r, P)) % P,
  "a challenged envelope's opened (choice, r) re-encrypts to its ciphertext on this, a different device");
let spoiled = false;
try { await Cast.finalize(ctx, testEnv, 99); } catch (e) { spoiled = /receipt/.test(e.message); }
say(spoiled, "an opened envelope refuses to cast: a receipt can never become a ballot");

// --- the real cast: Derek re-votes Sandra, one seq above his own last ballot
const box = JSON.parse(files["ballot-box.json"] = readFileSync(path.join(OUT, "ballot-box.json"), "utf8"));
const mine = box.ballots.filter(b => b.nullifier === ctx.tag);
say(mine.length > 0, "Derek's linking tag is in the reference box (" + mine.length + " ballot(s))");
const seq = Math.max(...mine.map(b => b.seq)) + 1;

const t0 = Date.now();
const ballot = await Cast.finalize(ctx, Cast.seal(ctx, ctx.options[0]), seq);
say(true, "ballot built in " + ((Date.now() - t0) / 1000).toFixed(1) + "s (LSAG over the "
  + ctx.ring.length + "-key ring, CDS proof, tag, seq " + seq + ")");

// --- the committee collects it and the independent Python verifier judges
const tmp = mkdtempSync(path.join(tmpdir(), "castparity-"));
try {
  const bpath = path.join(tmp, "ballot.json");
  writeFileSync(bpath, JSON.stringify(ballot));
  const dst = path.join(tmp, "collected");
  execFileSync("python3", [path.join(ROOT, "proto", "clubvote.py"), "collect", OUT, dst, bpath],
    { stdio: "pipe" });
  let verdict = "";
  let ok = true;
  try {
    verdict = execFileSync("python3", [path.join(ROOT, "proto", "verify.py"), dst],
      { stdio: "pipe" }).toString();
  } catch (e) {
    ok = false;
    verdict = (e.stdout || "").toString() + (e.stderr || "").toString();
  }
  say(ok, "verify.py accepts the transcript containing the page-built ballot"
    + (ok ? "" : " :: " + (verdict.split("\n").find(l => l.includes("FAIL")) || verdict.slice(0, 200))));
  say(verdict.includes("{'Sandra Okafor': 9, 'Keith Bramall': 5}"),
    "and the verified tally moved 8-6 -> 9-5: the page ballot superseded Derek's old vote and counted");
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

if (failures) {
  console.log(failures + " cast-parity failure(s) — cast.js does not produce what verify.py accepts");
  process.exit(1);
}
console.log("cast parity: what the page builds, the independent verifier counts");
