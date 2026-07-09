/* Civic Kernel — the clubvote casting engine, in JavaScript.
 *
 * The voter's half of the protocol, in the browser: generate an enrolment
 * secret, and build a ballot — exponential-ElGamal encryption to the election
 * key, a CDS 0-or-1 validity proof, a per-decision linking tag, and an LSAG
 * ring signature over the published roster. Runs in a browser (script tag,
 * used by cast.html) or in Node >= 20 (used by tools/cast-parity.mjs, which
 * asserts in CI that a ballot built here verifies in proto/verify.py).
 *
 * Shares no code with verifier.js or verify.py — the same discipline as the
 * Python pair: the thing that builds artifacts and the things that judge them
 * must not be able to agree by accident.
 *
 * Every scalar comes from crypto.getRandomValues — there is no demo-seed mode
 * in this file; a page that could be seeded could be replayed. The encryption
 * randomness r lives only inside the sealed-envelope object, and finalize()
 * deletes it before the ballot leaves: nothing this engine returns can prove
 * what a cast ballot says.
 *
 * The ballot group is pinned here by name, the verifier's rule: a roster or
 * trustee file never gets to choose its own arithmetic.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CivicCast = factory();
})(typeof self !== "undefined" ? self : globalThis, function () {
  "use strict";

  // ---------------------------------------------------------------- pinned
  const KNOWN_GROUPS = {
    "rfc3526-modp-2048": BigInt(
      "0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74" +
      "020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F1437" +
      "4FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED" +
      "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF05" +
      "98DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB" +
      "9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B" +
      "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718" +
      "3995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF"),
  };

  // ---------------------------------------------------------------- bigint
  const B0 = 0n, B1 = 1n, B2 = 2n;

  function modpow(base, exp, mod) {
    base %= mod; if (base < B0) base += mod;
    let r = B1;
    while (exp > B0) {
      if (exp & B1) r = (r * base) % mod;
      base = (base * base) % mod;
      exp >>= B1;
    }
    return r;
  }
  function modinv(a, mod) { // mod prime
    a %= mod; if (a < B0) a += mod;
    if (a === B0) throw new Error("no inverse of 0");
    return modpow(a, mod - B2, mod);
  }
  function fromHex(s) {
    if (typeof s !== "string" || !/^[0-9a-fA-F]+$/.test(s)) throw new Error("bad hex: " + String(s).slice(0, 40));
    return BigInt("0x" + s);
  }
  function hx(n) { return n.toString(16); }
  function mod(a, m) { const r = a % m; return r < B0 ? r + m : r; }

  // ---------------------------------------------------------------- bytes
  const te = new TextEncoder();

  function bytesToHex(b) {
    let s = "";
    for (const x of b) s += x.toString(16).padStart(2, "0");
    return s;
  }
  function bytesToBig(b) {
    let n = B0;
    for (const x of b) n = (n << 8n) | BigInt(x);
    return n;
  }

  // ------------------------------------------------------------ canonical JSON
  function canon(obj) { return te.encode(canonStr(obj)); }
  function canonStr(o) {
    if (o === null) return "null";
    if (typeof o === "boolean" || typeof o === "number") return JSON.stringify(o);
    if (typeof o === "string") return JSON.stringify(o);
    if (Array.isArray(o)) return "[" + o.map(canonStr).join(",") + "]";
    if (typeof o === "object") {
      const keys = Object.keys(o).sort();
      return "{" + keys.map(k => JSON.stringify(k) + ":" + canonStr(o[k])).join(",") + "}";
    }
    throw new Error("cannot canonicalize " + typeof o);
  }

  // ---------------------------------------------------------------- crypto
  const subtle = (typeof crypto !== "undefined" && crypto.subtle) ? crypto.subtle : null;

  async function sha256(bytes) {
    if (!subtle) throw new Error("WebCrypto unavailable");
    return new Uint8Array(await subtle.digest("SHA-256", bytes));
  }
  async function sha256hex(bytes) { return "sha256:" + bytesToHex(await sha256(bytes)); }

  // Uniform scalar in [0, Q): 272 random bytes >> 2176 bits against a 2047-bit
  // modulus, so the reduction bias is < 2^-128. The OS is the only source.
  function randScalar(Q) {
    const b = new Uint8Array(272);
    crypto.getRandomValues(b);
    return bytesToBig(b) % Q;
  }

  // ---------------------------------------------------------------- protocol
  async function fsChallenge(stmt, Q) {
    return bytesToBig(await sha256(canon(stmt))) % Q;
  }
  async function contextGen(ctx, P) {
    for (let i = 0; i < 64; i++) {
      const c = bytesToBig(await sha256(te.encode("civic-kernel/ctx|" + ctx + "|" + i))) % P;
      if (c > B1 && modpow(c, B2, P) !== B1) return modpow(c, B2, P);
    }
    throw new Error("no context generator");
  }

  /* Read the three published files a voter needs — roster.json, trustees.json,
   * log.jsonl — and return everything casting requires: the ring, the election
   * key derived from the trustees' own Feldman commitments (asserted by
   * nobody), and the open decision. Throws if this secret's public key is not
   * on the roster: an unenrolled key has nothing to sign with, so there is no
   * ballot to build — the same refusal Cousin Ray meets in clubvote.py. */
  async function prepare(files, secretHex) {
    const rosterDoc = JSON.parse(files["roster.json"]);
    const trusteesDoc = JSON.parse(files["trustees.json"]);
    const entries = files["log.jsonl"].split("\n").filter(l => l.trim()).map(l => JSON.parse(l));

    if (!(trusteesDoc.group in KNOWN_GROUPS)) {
      throw new Error("ballot group '" + trusteesDoc.group + "' is not one this page pins — refusing to cast into unknown arithmetic");
    }
    const P = KNOWN_GROUPS[trusteesDoc.group];
    const Q = (P - B1) / B2, G = B2;

    const byType = {};
    for (const e of entries) byType[e.type] = e;
    const opened = (byType["decision.opened"] || {}).body;
    if (!opened) throw new Error("the log has no decision.opened entry — nothing to vote on");

    const x = mod(fromHex(secretHex), Q);
    const pub = hx(modpow(G, x, P));
    const idx = rosterDoc.members.findIndex(c => c.voter_pub === pub);
    if (idx < 0) {
      throw new Error("this secret's public key is not on the roster — an unenrolled key has no membership to prove, so no ballot exists for it");
    }

    // The election key: the product of the per-trustee commitments' constant
    // terms — derived, never taken on assertion.
    let h = B1;
    for (const tr of trusteesDoc.trustees) h = (h * fromHex(tr.commitments[0])) % P;

    const ring = rosterDoc.members.map(c => fromHex(c.voter_pub));
    const ringDigest = await sha256hex(canon(rosterDoc.members.map(c => c.voter_pub)));
    const hl = await contextGen(opened.decision_id, P);

    return {
      P, Q, G, h, hl, ring, ringDigest, x, idx,
      member: rosterDoc.members[idx].member,
      decisionId: opened.decision_id,
      question: opened.question,
      options: opened.options,
      window: opened.window,
      tag: hx(modpow(hl, x, P)),
    };
  }

  /* Seal a choice: the commitment step of cast-or-audit. The envelope holds
   * (m, r) privately; the caller shows its ciphertext to the voter BEFORE
   * asking cast-or-challenge, so this engine cannot tell which is coming. */
  function seal(ctx, choice) {
    const m = choice === ctx.options[0] ? B1 : B0;
    if (choice !== ctx.options[0] && choice !== ctx.options[1]) {
      throw new Error("'" + choice + "' is not one of this decision's options");
    }
    const r = randScalar(ctx.Q);
    const ciphertext = {
      c1: hx(modpow(ctx.G, r, ctx.P)),
      c2: hx((modpow(ctx.G, m, ctx.P) * modpow(ctx.h, r, ctx.P)) % ctx.P),
    };
    return { ciphertext, choice, m, r, spoiled: false };
  }

  /* Benaloh challenge: open the envelope. Once opened it is a receipt by
   * construction, so it is spoiled here and can never be cast. The record
   * matches audits.json's shape; the OUTCOME line is the other device's to
   * judge — a page that graded its own honesty would be theatre. */
  function challengeOpen(ctx, env) {
    if (env.m === undefined) throw new Error("this envelope was already cast — opening it now would mint a receipt");
    env.spoiled = true;
    return {
      ciphertext: env.ciphertext,
      claimed_choice: env.choice,
      opened_choice: env.m === B1 ? ctx.options[0] : ctx.options[1],
      opened_r: hx(env.r),
    };
  }

  /* Prove and sign: the CDS 0-or-1 validity proof, then the LSAG ring
   * signature binding tag and contents to "some roster key, this ballot".
   * Deletes the envelope's randomness before returning — after this, nothing
   * in this engine can prove what the ballot says. */
  async function finalize(ctx, env, seq, onStep) {
    if (env.spoiled) throw new Error("this envelope was opened by a challenge — it is a receipt, not a ballot; seal again");
    if (!Number.isInteger(seq) || seq < 0) throw new Error("seq must be a non-negative integer");
    const { P, Q, G, h, hl, ring, ringDigest, x, idx } = ctx;
    const step = onStep || (() => {});

    // --- CDS: simulate the false branch, answer the true one, split the challenge
    step("proving the sealed choice is a valid 0-or-1");
    const m = env.m, r = env.r, f = B1 - m;
    const c1 = fromHex(env.ciphertext.c1), c2 = fromHex(env.ciphertext.c2);
    const zf = randScalar(Q), cf = randScalar(Q), w = randScalar(Q);
    const uf = (c2 * modinv(modpow(G, f, P), P)) % P;
    const af = (modpow(G, zf, P) * modpow(modinv(c1, P), cf, P)) % P;
    const bf = (modpow(h, zf, P) * modpow(modinv(uf, P), cf, P)) % P;
    const a = {};
    a[hx(m)] = [modpow(G, w, P), modpow(h, w, P)];
    a[hx(f)] = [af, bf];
    const stmt = { t: "cds01", ctx: ctx.decisionId, h: hx(h), c1: env.ciphertext.c1, c2: env.ciphertext.c2,
                   a0: hx(a["0"][0]), b0: hx(a["0"][1]), a1: hx(a["1"][0]), b1: hx(a["1"][1]) };
    const c = await fsChallenge(stmt, Q);
    const ct_ = mod(c - cf, Q);
    const zt = mod(w + ct_ * r, Q);
    const cc = {}, zz = {};
    cc[hx(m)] = ct_; cc[hx(f)] = cf;
    zz[hx(m)] = zt; zz[hx(f)] = zf;
    const proof = { a0: stmt.a0, b0: stmt.b0, a1: stmt.a1, b1: stmt.b1,
                    c0: hx(cc["0"]), c1: hx(cc["1"]), z0: hx(zz["0"]), z1: hx(zz["1"]) };

    const tag = modpow(hl, x, P);
    const ballot = { decision_id: ctx.decisionId, seq, nullifier: hx(tag),
                     ciphertext: env.ciphertext, proof };

    // --- LSAG over the whole roster: simulate every position but ours,
    // answer ours for real, close the chain back onto itself.
    const n = ring.length;
    const msg = await sha256hex(canon(ballot));
    async function ringChallenge(z1, z2) {
      return bytesToBig(await sha256(canon(
        { t: "lsag", ring: ringDigest, ctx: ctx.decisionId, msg, tag: hx(tag), z1: hx(z1), z2: hx(z2) })));
    }
    const u = randScalar(Q);
    const cs = new Array(n).fill(B0), s = new Array(n).fill(B0);
    cs[(idx + 1) % n] = await ringChallenge(modpow(G, u, P), modpow(hl, u, P));
    let i = (idx + 1) % n, done = 1;
    while (i !== idx) {
      s[i] = randScalar(Q);
      const z1 = (modpow(G, s[i], P) * modpow(ring[i], cs[i], P)) % P;
      const z2 = (modpow(hl, s[i], P) * modpow(tag, cs[i], P)) % P;
      cs[(i + 1) % n] = await ringChallenge(z1, z2);
      i = (i + 1) % n;
      step("signing as one of " + n + " enrolled keys — ring position " + (++done) + " of " + n);
    }
    s[idx] = mod(u - x * cs[idx], Q);
    ballot.ring_sig = { c0: hx(cs[0]), s: s.map(hx) };

    delete env.m; delete env.r; env.spoiled = true; // nothing left to receipt
    return ballot;
  }

  // ---------------------------------------------------------------- enrolment
  /* A credential is born on the voter's device: the secret never leaves it.
   * What the issuer gets — and certifies — is only the public key g^x. */
  function newCredential(files) {
    const trusteesDoc = files && files["trustees.json"] ? JSON.parse(files["trustees.json"]) : null;
    const group = trusteesDoc ? trusteesDoc.group : "rfc3526-modp-2048";
    if (!(group in KNOWN_GROUPS)) throw new Error("unknown ballot group " + group);
    const P = KNOWN_GROUPS[group], Q = (P - B1) / B2;
    const x = randScalar(Q);
    return { nym_secret: hx(x), voter_pub: hx(modpow(B2, x, P)), group };
  }
  function pubOf(secretHex, group) {
    const P = KNOWN_GROUPS[group || "rfc3526-modp-2048"], Q = (P - B1) / B2;
    return hx(modpow(B2, mod(fromHex(secretHex), Q), P));
  }

  return { newCredential, pubOf, prepare, seal, challengeOpen, finalize };
});
