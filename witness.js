/* Civic Kernel — the witness, in JavaScript.
 *
 * The neighbouring society's half of witnessing, in the browser: hold one
 * Ed25519 key, remember the last head you co-signed, and sign a new head
 * ONLY if the history you are shown extends the history you remember — so
 * a committee that rewrites the past cannot get its checkpoint witnessed.
 * The log key you check against arrives out of band (the ceremony: two
 * secretaries swapping keys at a federation meeting); it is never taken
 * from the request you are asked to sign.
 *
 * Interchangeable with `clubvote.py witness`: the witness file, the card,
 * and the co-signature are the same formats, and the refusals carry the
 * same reasons. tools/witness-parity.mjs asserts in CI that a committee
 * running clubvote.py accepts this engine's cards and co-signatures at
 * every checkpoint of a real election, that verify.py certifies the
 * result — and that this engine refuses the same rewrite the Python
 * witness refuses, on the same memory.
 *
 * Shares no code with clubvote.py, cast.js or verifier.js — the same
 * discipline as the rest of the family: actors that must agree can only
 * agree because the formats agree.
 *
 * Runs in a browser (script tag, used by witness.html) or in Node >= 20.
 * Requires WebCrypto Ed25519 key generation and signing (Chrome 137+,
 * Firefox 129+, Safari 17+, Node 20+).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CivicWitness = factory();
})(typeof self !== "undefined" ? self : globalThis, function () {
  "use strict";

  const te = new TextEncoder();
  const subtle = (typeof crypto !== "undefined" && crypto.subtle) ? crypto.subtle : null;

  // ------------------------------------------------------------ canonical JSON
  // Mirrors Python json.dumps(obj, sort_keys=True, separators=(",",":"),
  // ensure_ascii=False) — exact for this artifact set (strings/ints/bools).
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
  function canon(obj) { return te.encode(canonStr(obj)); }

  // ---------------------------------------------------------------- bytes
  function b64u(bytes) {
    let bin = "";
    for (const x of bytes) bin += String.fromCharCode(x);
    const b64 = typeof btoa === "function" ? btoa(bin) : Buffer.from(bytes).toString("base64");
    return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function b64d(s) {
    let t = String(s).replace(/-/g, "+").replace(/_/g, "/");
    while (t.length % 4) t += "=";
    const bin = typeof atob === "function" ? atob(t) : Buffer.from(t, "base64").toString("binary");
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function hexToBytes(h) {
    if (typeof h !== "string" || h.length % 2 || !/^[0-9a-fA-F]*$/.test(h)) throw new Error("bad hex");
    const out = new Uint8Array(h.length / 2);
    for (let i = 0; i < out.length; i++) out[i] = parseInt(h.slice(2 * i, 2 * i + 2), 16);
    return out;
  }
  function bytesToHex(b) {
    let s = "";
    for (const x of b) s += x.toString(16).padStart(2, "0");
    return s;
  }
  function concatBytes(...arrs) {
    const n = arrs.reduce((a, b) => a + b.length, 0);
    const out = new Uint8Array(n);
    let o = 0;
    for (const a of arrs) { out.set(a, o); o += a.length; }
    return out;
  }

  // ---------------------------------------------------------------- crypto
  async function sha256(bytes) {
    if (!subtle) throw new Error("WebCrypto unavailable");
    return new Uint8Array(await subtle.digest("SHA-256", bytes));
  }
  // RFC 8410 PKCS#8 wrapping of a raw 32-byte Ed25519 seed: WebCrypto will
  // not import a bare seed, but the PKCS#8 envelope for one is a constant
  // 16-byte prefix. This is how a witness file written by clubvote.py
  // (which stores the raw seed as hex) signs in a browser, and vice versa.
  const PKCS8_PREFIX = hexToBytes("302e020100300506032b657004220420");

  async function privKeyOf(seedHex) {
    const seed = hexToBytes(seedHex);
    if (seed.length !== 32) throw new Error("the witness key is not a raw 32-byte Ed25519 seed");
    return subtle.importKey("pkcs8", concatBytes(PKCS8_PREFIX, seed), { name: "Ed25519" }, false, ["sign"]);
  }
  async function signOver(seedHex, keyId, objMinusSig) {
    const key = await privKeyOf(seedHex);
    const sig = new Uint8Array(await subtle.sign("Ed25519", key, canon(objMinusSig)));
    return { key_id: keyId, alg: "ed25519", value: b64u(sig) };
  }
  async function sigOk(pubB64, sig, objMinusSig) {
    try {
      const key = await subtle.importKey("raw", b64d(pubB64), { name: "Ed25519" }, false, ["verify"]);
      return await subtle.verify("Ed25519", key, b64d(sig.value), canon(objMinusSig));
    } catch (e) {
      return false;
    }
  }
  async function edSupported() {
    if (!subtle) return false;
    try {
      await subtle.importKey("pkcs8", concatBytes(PKCS8_PREFIX, new Uint8Array(32)), { name: "Ed25519" }, false, ["sign"]);
      return true;
    } catch (e) {
      return e && e.name === "DataError";
    }
  }

  // ---------------------------------------------------------------- merkle
  // RFC 6962, same tree the log uses.
  async function leafHash(leafBytes) {
    return sha256(concatBytes(new Uint8Array([0]), leafBytes));
  }
  async function merkleRoot(leaves) {
    if (leaves.length === 0) return sha256(new Uint8Array(0));
    if (leaves.length === 1) return leaves[0];
    let k = 1;
    while (k * 2 < leaves.length) k *= 2;
    const l = await merkleRoot(leaves.slice(0, k));
    const r = await merkleRoot(leaves.slice(k));
    return sha256(concatBytes(new Uint8Array([1]), l, r));
  }

  function stripKey(obj, key) {
    const out = {};
    for (const [k, v] of Object.entries(obj)) if (k !== key) out[k] = v;
    return out;
  }

  // ---------------------------------------------------------------- the witness
  /* Make a new witness: one key, born on this device. Returns the state
   * (the content of witness.json — KEEP PRIVATE: the key and, later, the
   * memory live in it) and the card (hand it to the committee). Formats
   * are clubvote.py's own. */
  async function newWitness(keyId) {
    if (typeof keyId !== "string" || !keyId.includes("#")) {
      throw new Error("the witness key id should carry a key fragment, e.g. did:web:example.org#w1");
    }
    const pair = await subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
    const jwk = await subtle.exportKey("jwk", pair.privateKey);
    if (!jwk.d || !jwk.x) throw new Error("this browser would not export the key it just made");
    return {
      state: { key_id: keyId, priv: bytesToHex(b64d(jwk.d)), watch: null, last: null },
      card: { witness: keyId, pub: jwk.x },
    };
  }

  /* The ceremony: pin whom this witness watches. The community id and the
   * log's public key must arrive OUT OF BAND — never from the request you
   * are asked to sign. */
  function watch(state, community, logPubB64) {
    if (b64d(logPubB64).length !== 32) {
      throw new Error("that does not look like a raw Ed25519 public key (base64url)");
    }
    if (typeof community !== "string" || !community.trim()) {
      throw new Error("the community id is empty");
    }
    return { ...state, watch: { community: community.trim(), log_pub: String(logPubB64).trim() } };
  }

  /* Co-sign a checkpoint — or refuse. The checks, in clubvote.py's order:
   * the head is from the community I watch; it is signed by the log key I
   * was given at the ceremony; it roots the log that came with it; and the
   * history EXTENDS the one I last co-signed. Returns the co-signature
   * (send it back to the committee) and the updated state (the new memory:
   * replace your old witness file with it). Throws with the refusal reason
   * otherwise — the same reasons the Python witness gives. */
  async function sign(state, request) {
    if (!state || typeof state.priv !== "string" || typeof state.key_id !== "string") {
      throw new Error("not a witness file: it should hold key_id and priv");
    }
    if (!state.watch) {
      throw new Error("this witness watches nobody yet — complete the ceremony first");
    }
    let req = request;
    if (typeof req === "string") {
      try { req = JSON.parse(req); } catch (e) { throw new Error("not a witness request: " + e.message); }
    }
    if (!req || typeof req !== "object" || !req.head || !Array.isArray(req.entries)) {
      throw new Error("not a witness request: it should hold a head and the log entries");
    }
    const head = req.head, entries = req.entries;
    const body = stripKey(head, "sigs");
    if (body.log_id !== state.watch.community) {
      throw new Error("this head is from " + JSON.stringify(body.log_id) + ", not the community I watch");
    }
    let signedByLog = false;
    for (const s of head.sigs || []) {
      if (await sigOk(state.watch.log_pub, s, body)) { signedByLog = true; break; }
    }
    if (!signedByLog) {
      throw new Error("the head is not signed by the log key I was given at the ceremony — refusing");
    }
    const leaves = [];
    for (const e of entries) leaves.push(await leafHash(canon(stripKey(e, "sig"))));
    if (body.size !== entries.length
      || body.root !== "sha256:" + bytesToHex(await merkleRoot(leaves))) {
      throw new Error("the head does not root the log that came with it — refusing");
    }
    if (state.last) {
      const prefixRoot = "sha256:" + bytesToHex(await merkleRoot(leaves.slice(0, state.last.size)));
      if (body.size < state.last.size || prefixRoot !== state.last.root) {
        throw new Error("REFUSED: this history is not an extension of the history I co-signed "
          + "at size " + state.last.size + ". Append-only is violated — someone is "
          + "asking me to witness a rewrite, and my memory is the defence.");
      }
    }
    const cosig = { head: body, sig: await signOver(state.priv, state.key_id, body) };
    return { cosig, state: { ...state, last: { size: body.size, root: body.root } } };
  }

  return { newWitness, watch, sign, edSupported };
});
