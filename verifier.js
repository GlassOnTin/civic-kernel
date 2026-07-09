/* Civic Kernel — the clubvote verifier, in JavaScript.
 *
 * Same checks as proto/verify.py, sharing no code with it or with clubvote.py:
 * it re-implements canonicalization, the Merkle tree, the group arithmetic, all
 * three zero-knowledge proof verifications, a JSON-Schema evaluator for the two
 * waist schemas, and the external-anchor check. Runs in a browser (script tag,
 * used by verifier.html) or in Node >= 20 (used by tools/verify-parity.mjs,
 * which asserts in CI that this file and verify.py reach the same verdicts).
 *
 * The standards are pinned INSIDE the verifier — the ballot group by name and
 * the two schemas by value — because a verifier that takes its standards from
 * outside can be fed different ones. tools/verify-parity.mjs asserts the
 * embedded schemas equal schema/*.schema.json, so they cannot drift.
 *
 * Requires WebCrypto with Ed25519 (Chrome 137+, Firefox 129+, Safari 17+,
 * Node 20+). If Ed25519 is unavailable the verdict is "cannot verify here",
 * never a false VERIFIED.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CivicVerifier = factory();
})(typeof self !== "undefined" ? self : globalThis, function () {
  "use strict";

  // ---------------------------------------------------------------- pinned
  // The verifier's own copy of RFC 3526 group 14 — parameters come from this
  // file, never from the transcript under audit.
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

  // The two waist schemas, embedded verbatim (see header). //SCHEMAS-START
  const SCHEMAS = {"log-entry":{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"https://glassontin.github.io/civic-kernel/schema/log-entry.schema.json","title":"Civic Kernel transparency-log entry","description":"One kernel event, appended to a community's Merkle transparency log (§3.4). The Merkle leaf is SHA-256 over the JCS (RFC 8785) canonical form of this object minus `sig`. Log heads/checkpoints are NOT redefined here: they use the existing signed-note checkpoint format (RFC 9162 / Sigstore witness ecosystem), co-signed by independent witnesses. Payloads must stay kilobyte-scale and self-contained — valid whenever they arrive, over any transport (§4).","type":"object","required":["v","type","community","timestamp","body","sig"],"additionalProperties":false,"properties":{"v":{"const":"civic-kernel/log-entry/v0","description":"Format identifier and version. The waist is versioned like any other artifact (§5)."},"type":{"description":"Kernel event type. Namespaced; the enum below is the set named in the architecture document — extensions use an `x-` prefix rather than diluting the core vocabulary (§6).","anyOf":[{"enum":["decision.opened","decision.closed","decision.tally-proof","credential.authority-key-rotated","credential.revoked","rights.classification","rights.escalation","rules.amendment","manifest.published","anchor.checkpoint","process.denial-trace","process.cost-aggregate","coercive.act"]},{"type":"string","pattern":"^x-[a-z0-9-]+(\\.[a-z0-9-]+)*$"}]},"community":{"type":"string","format":"uri","description":"Identifier (DID or URI) of the community whose log this is. Communities nest fractally (§6); each runs its own log."},"timestamp":{"type":"string","format":"date-time","description":"RFC 3339 UTC time claimed by the ordering authority. Ordering truth is the Merkle tree, not this field."},"body":{"type":"object","description":"Type-specific payload. E.g. decision.opened carries the decision id, question hash, eligibility-rule version and deliberation window; rights.classification carries the tripped invariant articles and reasons (§3.3); process.cost-aggregate carries anonymous aggregate metrics only — measure the process, never the person (§8)."},"sig":{"$ref":"#/$defs/signature"}},"allOf":[{"if":{"properties":{"type":{"const":"coercive.act"}}},"then":{"description":"A coercive.act entry logs an exercise of the state's monopoly on force — an arrest, search, surveillance authorization, sanction, use of force (§ law-and-order). It must cite its authority: an act with no authorizing_rule is a schema violation, not a policy dispute — §8's 'every demanded field cites its authorizing rule' generalised to 'every coercive act cites its warrant'. The kernel does not wield this power; it makes its exercise legible and appealable.","properties":{"body":{"$ref":"#/$defs/coercive_body"}}}}],"$defs":{"coercive_body":{"type":"object","required":["act_class","authorizing_rule"],"additionalProperties":false,"properties":{"act_class":{"enum":["warrant","search","arrest","detention","seizure","surveillance","sanction","use-of-force"],"description":"The kind of coercive act."},"authorizing_rule":{"type":"string","description":"Citation of the rule/warrant/statute that authorizes this act. REQUIRED — an unwarranted coercive act cannot be logged validly, which is the point."},"issuing_authority":{"type":"string","description":"Who authorized the act (court, magistrate, tribunal)."},"subject_ref":{"type":"string","description":"Opaque reference to the subject IN THE ENFORCEMENT IDENTITY DOMAIN. MUST NOT be a civic unlinkable pseudonym — the kernel refuses to bridge civic anonymity to enforcement attribution (T6, T1). Attribution lives in the state's separate legal-identity system, walled off from the civic layer."},"sealed_until":{"type":"string","format":"date-time","description":"Commit-now-reveal-later: the act's existence and timing are logged immediately (tamper-evident), but sealed_body_digest commits to content revealed only after this time or by court order. Honest caveat: the unseal key is a trusted party — the same witness-recursion problem as §6's anchor, not a cryptographic guarantee."},"sealed_body_digest":{"type":"string","description":"Hash commitment to the sealed content, published now so the later reveal cannot be altered."},"rights_guard_ref":{"type":"string","description":"If the act tripped a UDHR invariant (Art. 5, 9, 11, 12…), the rights.classification entry that escalated it (§3.3)."},"appeal_trace":{"type":"string","description":"Pointer to the appealable computation trace — the right to reasons and to challenge, made machine-checkable (§8, §11)."}}},"signature":{"type":"object","required":["key_id","alg","value"],"additionalProperties":false,"properties":{"key_id":{"type":"string","description":"Identifier of the signing key. Key rotations are themselves log entries (credential.authority-key-rotated)."},"alg":{"type":"string","examples":["ed25519"]},"value":{"type":"string","contentEncoding":"base64url","description":"Detached signature over the JCS canonical form of the entry minus `sig`."}}}},"examples":[{"v":"civic-kernel/log-entry/v0","type":"decision.opened","community":"did:web:allotment-society.example","timestamp":"2026-07-07T18:00:00Z","body":{"decision_id":"2026-agm-treasurer","question_hash":"sha256:9f2b7c1a0d4e8f3b6a5c2e1d7f0a9b8c3d6e5f4a1b2c3d4e5f6a7b8c9d0e1f2a","eligibility_rules":"roster/v3","window":{"deliberation_ends":"2026-07-14T18:00:00Z","cast_ends":"2026-07-21T18:00:00Z"}},"sig":{"key_id":"did:web:allotment-society.example#log-1","alg":"ed25519","value":"hbXNaP1yQvR8sT2uW4xZ6aB9cD0eF3gH5iJ7kL9mN1oP3qR5sT7uV9wX1yZ3aB5c"}}]},"manifest":{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"https://glassontin.github.io/civic-kernel/schema/manifest.schema.json","title":"Civic Kernel conformance manifest","description":"A community's signed, machine-readable declaration of exactly which kernel services and which UDHR invariants it upholds (§6). Published as a `manifest.published` entry in the community's own transparency log, so a manifest that lies is a consistency-proof failure, not a marketing dispute. Subtraction must be explicit: all four services are declared true or false — absence of a claim is never silence, it is a schema violation. The citizen's client renders this directly: 'upholds 24 of 30 invariants; absent: Art. 12, 19; ballots verifiable but not receipt-free.'","type":"object","required":["v","community","services","sig"],"additionalProperties":false,"properties":{"v":{"const":"civic-kernel/manifest/v0","description":"Format identifier and version."},"community":{"type":"object","required":["id"],"additionalProperties":false,"properties":{"id":{"type":"string","format":"uri","description":"DID or URI of the community. One person couples into many communities under unlinkable pseudonyms (§6)."},"name":{"type":"string"},"parent":{"type":"string","format":"uri","description":"Enclosing community, if nested — a parish inside a city inside a nation (§6, fractal adoption)."}}},"services":{"type":"object","description":"The lattice position (§6). Every service is declared explicitly; a `true` here requires the matching detail block below.","required":["personhood","decisions","rights_guard","transparency_log"],"additionalProperties":false,"properties":{"personhood":{"type":"boolean"},"decisions":{"type":"boolean"},"rights_guard":{"type":"boolean"},"transparency_log":{"type":"boolean"}}},"personhood":{"type":"object","description":"How 'one human, one voice' is established (§3.1, §10, §13). Issuers are lattice entries, not architectural commitments.","required":["method","unlinkable","sybil_resistance"],"additionalProperties":false,"properties":{"method":{"enum":["ceremony","ceremony-biometric-dedup","document","external-issuer","platform-account"],"description":"ceremony = physical enrolment, the reference profile; ceremony-biometric-dedup adds the secret-shared MPC gallery (§10); platform-account = a chat roster, the legitimate low-lattice onboarding ramp (Form C)."},"issuer":{"type":"string","description":"Who signs eligibility credentials, e.g. 'municipal registrar', 'World ID', 'discord:server-roster'."},"unlinkable":{"type":"boolean","description":"Whether presentations are unlinkable across decisions. An EUDI-wallet deployment today would declare false — the legible degradation §6 exists to express (§13)."},"sybil_resistance":{"enum":["strong","medium","weak"]},"eligibility_rules":{"type":"string","description":"Version reference of the rules-as-code eligibility criteria; amendable only via the constitutional path (§10)."}}},"decisions":{"type":"object","description":"Ballot properties (§3.2). The two non-negotiables of the reference profile are declared, not assumed.","required":["verifiable","receipt_free"],"additionalProperties":false,"properties":{"verifiable":{"type":"boolean","description":"End-to-end verifiable: anyone can check the announced total against the encrypted ballots."},"receipt_free":{"type":"boolean","description":"You can prove your vote was counted, never what it said (T4)."},"cast_or_audit":{"type":"boolean","description":"Benaloh challenge against a compromised device (T5)."},"paper_channel":{"type":"boolean","description":"Paper/kiosk/assisted channels in the same protocol with the same verifiability (T9, §4)."},"coercion_resistance":{"enum":["none","revote-silent","revote-safe-space","fake-credential"],"description":"Defence against a coercer present DURING casting (T4), which receipt-freeness alone cannot touch. A lattice, weakest first: 'none' = receipt-free only, no defence against over-the-shoulder observation; 'revote-silent' = any later ballot silently supersedes (deniability by silence — the coercer cannot detect a re-vote), but requires a later coercer-excluded moment; 'revote-safe-space' = silent re-vote PLUS staffed coercer-excluded cast points (booths, pharmacies, refuges — the domestic-abuse safeguarding estate), so the private moment is guaranteed, not hoped for; 'fake-credential' = indistinguishable fake credentials filtered at tally (JCJ/Civitas), deniability by indistinguishability. Honest caveats a client should surface: no level defeats forced abstention or a coercer who controls the device from enrolment onward; and 'fake-credential' is sound only if universal within the community — a known, opt-in duress mode inverts the burden ('prove you did not fake it') and can escalate harm."},"trustee_quorum":{"type":"string","description":"Threshold-decryption arrangement, e.g. '3-of-5: court, two universities, two opposition parties'."}}},"rights_guard":{"type":"object","description":"Which UDHR articles are encoded as machine-checkable invariants (§3.3). The reference profile is all thirty.","required":["invariants"],"additionalProperties":false,"properties":{"invariants":{"type":"array","uniqueItems":true,"items":{"type":"integer","minimum":1,"maximum":30},"description":"UDHR article numbers upheld. Clients render the complement — what is absent — as prominently as what is present."},"remedy":{"enum":["none","declaration","escalate","strike"],"description":"What the guard can actually DO when a decision trips an invariant — a second axis distinct from coverage, because two systems can uphold the same article with very different force. 'none' = no remedy; 'declaration' = flag only, the decision still stands (e.g. UK: HRA s.4 declaration of incompatibility, Parliament remains sovereign); 'escalate' = re-route to supermajority + adversarial review, the kernel's reference posture (§3.3); 'strike' = a constitutional court can void the decision, and an unamendable core may block even a supermajority (e.g. Germany: Grundgesetz Art 79(3) eternity clause + Bundesverfassungsgericht). Coverage says which rights are named; remedy says what naming them is worth."},"scope":{"enum":["unconditional","conditional"],"description":"Whether the guard applies to EVERY decision in the community's domain, or only to a subset gated by a precondition — a THIRD axis, distinct from coverage (which rights are named) and remedy (what a court can do about them). 'unconditional' = a national constitution binds all of its own community's decisions (the reference case: the German, UK and US instruments apply to any national law in their own courts). 'conditional' = the guard's applicability to a given decision must first be established, e.g. the EU Charter, which Art 51 confines to Member States 'only when they are implementing Union law' — so for a purely national matter its protection must be argued into. The three axes form a CASCADE: an instrument must apply (scope) before its remedy matters, before the breadth of rights it names (coverage) matters. The EU majority-vs-minority run exposed this: coverage and remedy both looked strongest, yet scope gated everything, and remedy alone could not express it."}}},"transparency_log":{"type":"object","required":["log_id"],"additionalProperties":false,"properties":{"log_id":{"type":"string","format":"uri"},"witnesses":{"type":"array","items":{"type":"string"},"description":"Independent institutions co-signing the log head (§3.4)."},"anchors":{"type":"array","items":{"type":"string"},"description":"Permissionless chains receiving periodic log-head/manifest-digest checkpoints — notary of last resort, never database (§6). Reference profile: at least two independent anchors. No token ever enters the citizen's path."}}},"decision_metadata":{"type":"boolean","description":"Whether every ballot carries the decision-metadata standard: plain-language summary, structured arguments for and against, provenance for both (§7)."},"interaction_cost":{"type":"array","description":"Published burden metrics per civic process, in anonymous aggregate — measure the process, never the person (§8). Sludge becomes two comparable numbers on the same dashboard.","items":{"type":"object","required":["process","steps","fields","median_seconds"],"additionalProperties":false,"properties":{"process":{"type":"string"},"steps":{"type":"integer","minimum":0},"fields":{"type":"integer","minimum":0,"description":"Every demanded field must cite its authorizing rule (T12)."},"median_seconds":{"type":"number","minimum":0},"abandonment_rate":{"type":"number","minimum":0,"maximum":1}}}},"sig":{"type":"object","required":["key_id","alg","value"],"additionalProperties":false,"properties":{"key_id":{"type":"string"},"alg":{"type":"string","examples":["ed25519"]},"value":{"type":"string","contentEncoding":"base64url","description":"Detached signature over the JCS (RFC 8785) canonical form of the manifest minus `sig`."}}}},"allOf":[{"if":{"properties":{"services":{"properties":{"personhood":{"const":true}}}}},"then":{"required":["personhood"]}},{"if":{"properties":{"services":{"properties":{"decisions":{"const":true}}}}},"then":{"required":["decisions"]}},{"if":{"properties":{"services":{"properties":{"rights_guard":{"const":true}}}}},"then":{"required":["rights_guard"]}},{"if":{"properties":{"services":{"properties":{"transparency_log":{"const":true}}}}},"then":{"required":["transparency_log"]}}],"examples":[{"v":"civic-kernel/manifest/v0","community":{"id":"did:web:allotment-society.example","name":"Model Allotment Society","parent":"did:web:example-town.example"},"services":{"personhood":true,"decisions":true,"rights_guard":false,"transparency_log":true},"personhood":{"method":"platform-account","issuer":"whatsapp:group-roster","unlinkable":false,"sybil_resistance":"weak","eligibility_rules":"roster/v3"},"decisions":{"verifiable":true,"receipt_free":false,"cast_or_audit":true,"paper_channel":false},"transparency_log":{"log_id":"did:web:allotment-society.example","witnesses":["did:web:example-town.example","did:web:neighbouring-society.example"]},"decision_metadata":true,"sig":{"key_id":"did:web:allotment-society.example#manifest-1","alg":"ed25519","value":"qR5sT7uV9wX1yZ3aB5chbXNaP1yQvR8sT2uW4xZ6aB9cD0eF3gH5iJ7kL9mN1oP3"}}]}}; //SCHEMAS-END

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
  // mod must be prime (P and Q both are: p is a safe prime).
  function modinv(a, mod) {
    a %= mod; if (a < B0) a += mod;
    if (a === B0) throw new Error("no inverse of 0");
    return modpow(a, mod - B2, mod);
  }
  function fromHex(s) {
    if (typeof s !== "string" || !/^[0-9a-fA-F]+$/.test(s)) throw new Error("bad hex: " + String(s).slice(0, 40));
    return BigInt("0x" + s);
  }
  function hx(n) { return n.toString(16); }

  // ---------------------------------------------------------------- bytes
  const te = new TextEncoder();

  function b64d(s) {
    let t = s.replace(/-/g, "+").replace(/_/g, "/");
    while (t.length % 4) t += "=";
    const bin = typeof atob === "function" ? atob(t) : Buffer.from(t, "base64").toString("binary");
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
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
  function concatBytes(...arrs) {
    const n = arrs.reduce((a, b) => a + b.length, 0);
    const out = new Uint8Array(n);
    let o = 0;
    for (const a of arrs) { out.set(a, o); o += a.length; }
    return out;
  }

  // ------------------------------------------------------------ canonical JSON
  // Mirrors Python json.dumps(obj, sort_keys=True, separators=(",",":"),
  // ensure_ascii=False) — exact for this artifact set (strings/ints/bools).
  function canon(obj) {
    return te.encode(canonStr(obj));
  }
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
  async function sha256hex(bytes) {
    return "sha256:" + bytesToHex(await sha256(bytes));
  }

  async function edSupported() {
    if (!subtle) return false;
    try {
      // any 32 bytes import as a raw Ed25519 public key candidate; rejection of
      // the algorithm name (not the key bytes) is what we are detecting
      await subtle.importKey("raw", new Uint8Array(32), { name: "Ed25519" }, false, ["verify"]);
      return true;
    } catch (e) {
      return e && e.name === "DataError"; // algorithm known, key bytes rejected
    }
  }

  async function sigOk(pubB64, sig, objMinusSig) {
    try {
      const key = await subtle.importKey("raw", b64d(pubB64), { name: "Ed25519" }, false, ["verify"]);
      return await subtle.verify("Ed25519", key, b64d(sig.value), canon(objMinusSig));
    } catch (e) {
      return false;
    }
  }

  // ---------------------------------------------------------------- merkle
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

  // ------------------------------------------------- JSON Schema (2020-12 subset)
  // Evaluates exactly the vocabulary the two waist schemas use: type, required,
  // properties, additionalProperties, const, enum, anyOf, allOf, if/then,
  // pattern, $ref (JSON pointer into the same document), items, minimum,
  // maximum, uniqueItems. `format`/`contentEncoding` are annotations in
  // Draft 2020-12 and are not asserted — the same behaviour as verify.py's
  // Draft202012Validator. tools/verify-parity.mjs checks agreement on both
  // valid and deliberately broken documents.
  function deepEq(a, b) {
    return canonStr(a) === canonStr(b);
  }
  function typeOk(t, v) {
    switch (t) {
      case "object": return v !== null && typeof v === "object" && !Array.isArray(v);
      case "array": return Array.isArray(v);
      case "string": return typeof v === "string";
      case "boolean": return typeof v === "boolean";
      case "number": return typeof v === "number";
      case "integer": return typeof v === "number" && Number.isInteger(v);
      case "null": return v === null;
      default: return false;
    }
  }
  function resolveRef(ref, rootSchema) {
    if (!ref.startsWith("#/")) throw new Error("unsupported $ref " + ref);
    let node = rootSchema;
    for (const part of ref.slice(2).split("/")) {
      node = node[part.replace(/~1/g, "/").replace(/~0/g, "~")];
      if (node === undefined) throw new Error("dangling $ref " + ref);
    }
    return node;
  }
  function schemaErrors(schema, value, rootSchema, path) {
    const errs = [];
    if (schema === true || schema === undefined) return errs;
    if (schema === false) { errs.push(path + ": schema forbids this value"); return errs; }
    if (schema.$ref) {
      errs.push(...schemaErrors(resolveRef(schema.$ref, rootSchema), value, rootSchema, path));
    }
    if (schema.type !== undefined) {
      const ts = Array.isArray(schema.type) ? schema.type : [schema.type];
      if (!ts.some(t => typeOk(t, value))) errs.push(path + ": expected " + ts.join("|"));
    }
    if (schema.const !== undefined && !deepEq(value, schema.const)) {
      errs.push(path + ": must equal " + JSON.stringify(schema.const));
    }
    if (schema.enum !== undefined && !schema.enum.some(e => deepEq(e, value))) {
      errs.push(path + ": not one of the allowed values");
    }
    if (schema.pattern !== undefined && typeof value === "string" && !new RegExp(schema.pattern).test(value)) {
      errs.push(path + ": does not match " + schema.pattern);
    }
    if (typeof value === "number") {
      if (schema.minimum !== undefined && value < schema.minimum) errs.push(path + ": below minimum " + schema.minimum);
      if (schema.maximum !== undefined && value > schema.maximum) errs.push(path + ": above maximum " + schema.maximum);
    }
    if (Array.isArray(value)) {
      if (schema.items !== undefined) {
        value.forEach((v, i) => errs.push(...schemaErrors(schema.items, v, rootSchema, path + "[" + i + "]")));
      }
      if (schema.uniqueItems) {
        const seen = new Set();
        for (const v of value) {
          const k = canonStr(v);
          if (seen.has(k)) { errs.push(path + ": items are not unique"); break; }
          seen.add(k);
        }
      }
    }
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      const props = schema.properties || {};
      if (schema.required) {
        for (const k of schema.required) {
          if (!(k in value)) errs.push(path + ": missing required property '" + k + "'");
        }
      }
      for (const [k, sub] of Object.entries(props)) {
        if (k in value) errs.push(...schemaErrors(sub, value[k], rootSchema, path + "." + k));
      }
      if (schema.additionalProperties !== undefined) {
        for (const k of Object.keys(value)) {
          if (!(k in props)) {
            if (schema.additionalProperties === false) errs.push(path + ": unexpected property '" + k + "'");
            else errs.push(...schemaErrors(schema.additionalProperties, value[k], rootSchema, path + "." + k));
          }
        }
      }
    }
    if (schema.anyOf !== undefined) {
      if (!schema.anyOf.some(s => schemaErrors(s, value, rootSchema, path).length === 0)) {
        errs.push(path + ": matches none of the allowed alternatives");
      }
    }
    if (schema.allOf !== undefined) {
      for (const s of schema.allOf) errs.push(...schemaErrors(s, value, rootSchema, path));
    }
    if (schema.if !== undefined) {
      if (schemaErrors(schema.if, value, rootSchema, path).length === 0 && schema.then !== undefined) {
        errs.push(...schemaErrors(schema.then, value, rootSchema, path));
      }
    }
    return errs;
  }

  // ---------------------------------------------------------------- helpers
  function stripKey(obj, key) {
    const out = {};
    for (const [k, v] of Object.entries(obj)) if (k !== key) out[k] = v;
    return out;
  }
  async function fsChallenge(stmt, Q) {
    return bytesToBig(await sha256(canon(stmt))) % Q;
  }

  // ---------------------------------------------------------------- verify
  // files: { "manifest.json": text, ..., "log.jsonl": text, ... }
  // hooks (all optional): onSection(numText, title), onCheck({section, ok, text, plain}),
  //                       onBallot(done, total), onSkip(numText, text)
  // `plain` is the check's meaning in plain speech; `text` stays the exact
  // technical statement (and carries failure detail after "::").
  async function verify(files, hooks = {}) {
    const checks = [];
    const failures = [];
    const t0 = Date.now();
    const onCheck = hooks.onCheck || (() => {});
    const onSection = hooks.onSection || (() => {});
    const onSkip = hooks.onSkip || (() => {});

    function check(section, ok, text, plain) {
      const c = { section, ok, text, plain: plain || text };
      checks.push(c);
      if (!ok) failures.push(text);
      onCheck(c);
    }
    function need(name) {
      if (typeof files[name] !== "string") throw new Error("missing file: " + name);
      return files[name];
    }
    function result(verdict, summary, counts) {
      return { verdict, summary, counts: counts || null, checks, failures, elapsedMs: Date.now() - t0 };
    }
    function finish(counts, rosterDoc, latest) {
      if (failures.length) {
        return result("NOT VERIFIED", failures.length + " failure(s) — the first is: " + failures[0], null);
      }
      let winner = null, best = -1;
      for (const [k, v] of Object.entries(counts)) if (v > best) { winner = k; best = v; }
      const parts = Object.entries(counts).map(([k, v]) => k + " " + v).join("; ");
      return result("VERIFIED",
        rosterDoc.members.length + " enrolled; " + latest.size + " voted; " + parts + ". " +
        winner + " is elected. No ballot was ever opened, no voter was ever named, " +
        "and nobody had to trust the shed.", counts);
    }

    if (!(await edSupported())) {
      return result("CANNOT VERIFY HERE",
        "This browser does not support Ed25519 signature verification (WebCrypto). " +
        "Nothing can be checked without it — try a current Firefox, Chrome, or Safari.", null);
    }

    try {
      // The trust anchors: keys the verifier already trusts, which witnesses it
      // requires on every head, and which external parties must anchor the close.
      const anchors = JSON.parse(need("trust.json"));
      const trust = anchors.keys, requiredWitnesses = anchors.witnesses;
      const manifest = JSON.parse(need("manifest.json"));
      const rosterDoc = JSON.parse(need("roster.json"));
      const boxDoc = JSON.parse(need("ballot-box.json"));
      const trusteesDoc = JSON.parse(need("trustees.json"));
      const entries = need("log.jsonl").split("\n").filter(l => l.trim()).map(l => JSON.parse(l));
      const heads = need("heads.jsonl").split("\n").filter(l => l.trim()).map(l => JSON.parse(l));

      onSection("1", "The paperwork matches the published formats");
      const mErrs = schemaErrors(SCHEMAS["manifest"], manifest, SCHEMAS["manifest"], "manifest");
      check("1", mErrs.length === 0, "manifest validates against manifest.schema.json (" + mErrs.length + " errors)"
        + (mErrs.length ? " :: " + mErrs[0] : ""),
        "The community's declaration of what it upholds is in the promised format.");
      const eErrs = [];
      entries.forEach((en, i) => {
        for (const e of schemaErrors(SCHEMAS["log-entry"], en, SCHEMAS["log-entry"], "entry")) {
          eErrs.push("entry[" + i + "] " + e);
        }
      });
      check("1", eErrs.length === 0, "all " + entries.length + " log entries validate against log-entry.schema.json"
        + (eErrs.length ? " :: " + eErrs[0] : ""),
        "Every event in the record is in the promised format.");

      onSection("2", "Every artifact is signed by a key the trust anchors name");
      const mBody = stripKey(manifest, "sig");
      check("2", await sigOk(trust[manifest.sig.key_id] || "", manifest.sig, mBody), "manifest signature",
        "The declaration really was issued with this community's key.");
      const logKeyId = entries.length ? entries[0].sig.key_id : "?";
      let allSigs = true;
      for (const e of entries) {
        if (!(await sigOk(trust[e.sig.key_id] || "", e.sig, stripKey(e, "sig")))) { allSigs = false; break; }
      }
      check("2", allSigs, "all log-entry signatures verify against " + logKeyId,
        "Every event in the record was really written with the log's key.");
      const ts = entries.map(e => e.timestamp);
      check("2", ts.every((t, i) => i === 0 || ts[i - 1] <= t), "log timestamps are non-decreasing",
        "The record's clock only ever moves forward.");

      onSection("3", "The record is append-only, witnessed, and commits to everything else");
      const leaves = [];
      for (const e of entries) leaves.push(await leafHash(canon(stripKey(e, "sig"))));
      let headsOk = true;
      for (const h of heads) {
        const root = "sha256:" + bytesToHex(await merkleRoot(leaves.slice(0, h.size)));
        if (h.root !== root) { headsOk = false; break; }
      }
      check("3", headsOk, "every published head's root matches a strict prefix of today's log "
        + "(consistency, " + heads.length + " heads)",
        "Every fingerprint ever published matches this record — the past has not been rewritten under it.");
      check("3", heads.length > 0 && heads[heads.length - 1].size === entries.length,
        "the latest head covers the whole log",
        "The newest fingerprint covers the whole record — nothing slipped in after the last witness looked.");
      // Who co-signed matters more than whether signatures verify: an insider can
      // regenerate heads and drop the witnesses they cannot forge. The bar is the
      // verifier's trust anchors plus whatever the manifest declares.
      const declared = (manifest.transparency_log || {}).witnesses || [];
      const expected = new Set([...requiredWitnesses, ...declared]);
      async function headOk(h) {
        const body = stripKey(h, "sigs");
        const covered = new Set();
        for (const s of h.sigs) {
          if (!(await sigOk(trust[s.key_id] || "", s, body))) return false;
          for (const w of expected) if (s.key_id === w || s.key_id.startsWith(w + "#")) covered.add(w);
        }
        for (const w of expected) if (!covered.has(w)) return false;
        return true;
      }
      const missing = [];
      for (const h of heads) if (!(await headOk(h))) missing.push(h.size);
      check("3", requiredWitnesses.length > 0 && missing.length === 0,
        "every head co-signed by the log key and all " + expected.size + " required/declared witnesses"
        + (requiredWitnesses.length ? "" : " :: the trust anchors name no witness, and an unwitnessed "
          + "log cannot defeat a records rewrite")
        + (missing.length ? " :: head(s) at size [" + missing.join(", ") + "] lack a valid co-signature "
          + "from every witness — the log key alone re-signed this history" : ""),
        "Independent witnesses co-signed every fingerprint — the operator alone could not have produced this history.");
      check("3", requiredWitnesses.every(w => declared.includes(w)),
        "the manifest declares every witness the trust anchors require (the manifest is signed "
        + "by the log key, so it cannot be its own standard: a manifest that quietly drops a "
        + "witness is a lying manifest)",
        "The declaration names every witness this page insists on — it cannot quietly lower its own bar.");

      const byType = {};
      for (const e of entries) byType[e.type] = e;
      const pub = (byType["manifest.published"] || {}).body || {};
      check("3", pub.manifest_digest === await sha256hex(canon(mBody)),
        "logged manifest digest matches the published manifest (a manifest that lies is a "
        + "consistency failure)",
        "The declaration on file is the exact one the record committed to.");
      const rost = (byType["x-roster.published"] || {}).body || {};
      check("3", rost.roster_digest === await sha256hex(canon(rosterDoc)),
        "logged roster digest matches the published roster (" + (rost.member_count ?? "?") + " members)",
        "The member list is the exact one the record committed to — nobody edited it after the vote.");
      const trst = (byType["x-trustees.published"] || {}).body || {};
      check("3", trst.trustees_digest === await sha256hex(canon(trusteesDoc)),
        "logged trustee-setup digest matches the published setup",
        "The key-holder setup is the exact one the record committed to.");
      const closed = (byType["decision.closed"] || {}).body || {};
      check("3", closed.ballot_box_digest === await sha256hex(canon(boxDoc)),
        "logged ballot-box digest matches the published box",
        "The ballot box is the exact one the record committed to.");

      onSection("4", "Only enrolled members: the roster ring and the election key check out");
      const issuerKey = rosterDoc.members.length
        ? (trust[rosterDoc.members[0].issuer_sig.key_id] || "") : "";
      let credsOk = true;
      for (const c of rosterDoc.members) {
        if (!(await sigOk(issuerKey, c.issuer_sig, stripKey(c, "issuer_sig")))) { credsOk = false; break; }
      }
      check("4", credsOk, "all " + rosterDoc.members.length + " roster credentials verify against the issuer key",
        "Everyone on the member list was certified by the enrolment authority.");

      check("4", trusteesDoc.group in KNOWN_GROUPS,
        "ballot group '" + trusteesDoc.group + "' is one this verifier pins "
        + "(parameters are the verifier's own, never the transcript's)",
        "The election's arithmetic is one this page brought with it — a transcript never gets to choose its own maths.");
      if (!(trusteesDoc.group in KNOWN_GROUPS)) return finish(null, rosterDoc, null);
      const P = KNOWN_GROUPS[trusteesDoc.group];
      const Q = (P - B1) / B2, G = B2;
      // DKG: the election key and every trustee key derive from the product of
      // the per-trustee Feldman commitments — asserted by nobody.
      const A = [B1, B1];
      for (const tr of trusteesDoc.trustees) {
        A[0] = (A[0] * fromHex(tr.commitments[0])) % P;
        A[1] = (A[1] * fromHex(tr.commitments[1])) % P;
      }
      const h = A[0];

      const inGroup = x => x > B0 && x < P && modpow(x, Q, P) === B1;

      const opened = (byType["decision.opened"] || {}).body || {};
      const decisionId = opened.decision_id;
      const options = opened.options || [];

      async function cdsOk(ct, prf) {
        // disjunctive Chaum-Pedersen: ct encrypts g^0 or g^1 under h
        const c1 = fromHex(ct.c1), c2 = fromHex(ct.c2);
        const stmt = { t: "cds01", ctx: decisionId, h: hx(h), c1: ct.c1, c2: ct.c2,
                       a0: prf.a0, b0: prf.b0, a1: prf.a1, b1: prf.b1 };
        const cc = [fromHex(prf.c0), fromHex(prf.c1)];
        const zz = [fromHex(prf.z0), fromHex(prf.z1)];
        if ((cc[0] + cc[1]) % Q !== await fsChallenge(stmt, Q)) return false;
        for (let i = 0; i <= 1; i++) {
          const a_i = fromHex(prf["a" + i]), b_i = fromHex(prf["b" + i]);
          if (modpow(G, zz[i], P) !== (a_i * modpow(c1, cc[i], P)) % P) return false;
          const u = (c2 * modinv(modpow(G, BigInt(i), P), P)) % P; // c2 / g^i
          if (modpow(h, zz[i], P) !== (b_i * modpow(u, cc[i], P)) % P) return false;
        }
        return true;
      }

      // The anonymity set: the roster's keys in the roster's order, and a
      // per-decision generator — both recomputed from digest-committed artifacts.
      const ring = rosterDoc.members.map(c => fromHex(c.voter_pub));
      const ringDigest = await sha256hex(canon(rosterDoc.members.map(c => c.voter_pub)));

      async function contextGen(ctx) {
        for (let i = 0; i < 64; i++) {
          const c = bytesToBig(await sha256(te.encode("civic-kernel/ctx|" + ctx + "|" + i))) % P;
          if (c > B1 && modpow(c, B2, P) !== B1) return modpow(c, B2, P);
        }
        throw new Error("no context generator");
      }
      const hl = await contextGen(decisionId);

      async function ringChallenge(msg, tag, z1, z2) {
        return bytesToBig(await sha256(canon(
          { t: "lsag", ring: ringDigest, ctx: decisionId, msg, tag: hx(tag), z1: hx(z1), z2: hx(z2) })));
      }
      async function lsagOk(b) {
        // The ring closes only if some ring key signed THIS ballot with THIS tag.
        const sig = b.ring_sig || {};
        const s = (sig.s || []).map(fromHex);
        if (s.length !== ring.length) return false;
        const tag = fromHex(b.nullifier), c0 = fromHex(sig.c0 || "0");
        const msg = await sha256hex(canon(stripKey(b, "ring_sig")));
        let c = c0;
        for (let i = 0; i < ring.length; i++) {
          const z1 = (modpow(G, s[i], P) * modpow(ring[i], c, P)) % P;
          const z2 = (modpow(hl, s[i], P) * modpow(tag, c, P)) % P;
          c = await ringChallenge(msg, tag, z1, z2);
        }
        return c === c0;
      }

      onSection("5", "Device challenges (cast-or-audit) hold up");
      const auditsDoc = JSON.parse(need("audits.json"));
      const audits = auditsDoc.audits;
      check("5", closed.audits_digest === await sha256hex(canon(auditsDoc)),
        "logged audits digest matches the published audit file",
        "The device-challenge evidence is the exact file the record committed to.");
      const reencrypts = a => {
        const m = a.opened_choice === options[0] ? B1 : B0;
        const r = fromHex(a.opened_r);
        return fromHex(a.ciphertext.c1) === modpow(G, r, P)
          && fromHex(a.ciphertext.c2) === (modpow(G, m, P) * modpow(h, r, P)) % P;
      };
      const badAudit = audits.filter(a =>
        !reencrypts(a) || ((a.outcome === "match") !== (a.opened_choice === a.claimed_choice)));
      check("5", badAudit.length === 0, "all " + audits.length + " audit records re-encrypt to their "
        + "opened choice (internally consistent evidence)",
        "Every device challenge adds up: each opened test envelope contained what it claims.");
      const castCts = new Set(boxDoc.ballots.map(b => b.ciphertext.c1 + "|" + b.ciphertext.c2));
      check("5", !audits.some(a => castCts.has(a.ciphertext.c1 + "|" + a.ciphertext.c2)),
        "no challenged (spoiled) ciphertext was ever cast",
        "No ballot opened as a test was ever counted — a test can never become a vote.");
      const auditFails = audits.filter(a => a.outcome === "MISMATCH");
      const afEntries = entries.filter(e => e.type === "x-ballot.audit-failed");
      check("5", afEntries.length === auditFails.length && auditFails.length === (closed.audit_failures ?? -1),
        "every audit failure is a public log entry (" + auditFails.length + " cheating device caught)",
        "Every device caught cheating is on the public record.");

      // Stage gate: verifying a ballot is O(roster); do not spend the ring on a
      // box the log has not earned the right to assert.
      if (failures.length) {
        onSkip("6-7", "not checked: the artifacts that commit to the ballots did not verify (above)");
        return finish(null, rosterDoc, null);
      }

      onSection("6", "Every ballot: anonymous, well-formed, provably from an enrolled member");
      check("6", ring.every(inGroup),
        "all " + ring.length + " roster keys are prime-order subgroup elements (input hygiene on the "
        + "ring: no tamper reaches it, because a rewritten roster fails its logged digest first)",
        "Every enrolment key passes the arithmetic hygiene check.");
      const ballots = [], problems = [];
      const onBallot = hooks.onBallot || (() => {});
      for (let i = 0; i < boxDoc.ballots.length; i++) {
        const b = boxDoc.ballots[i];
        const tag = fromHex(b.nullifier);
        let why = null;
        if (b.decision_id !== decisionId) {
          why = "wrong decision";
        } else if (!(inGroup(tag) && tag !== B1)) {
          why = "nullifier is not in the prime-order subgroup (a negated linking tag votes twice)";
        } else if (!(inGroup(fromHex(b.ciphertext.c1)) && inGroup(fromHex(b.ciphertext.c2)))) {
          why = "ciphertext component not in the prime-order subgroup";
        } else if (!(await lsagOk(b))) {
          why = "ring signature does not verify (no roster member signed this ballot with this nullifier)";
        } else if (!(await cdsOk(b.ciphertext, b.proof))) {
          why = "ballot validity proof does not verify (not a 0-or-1 encryption)";
        }
        if (why) problems.push("ballot[" + i + "] " + why);
        else ballots.push(b);
        onBallot(i + 1, boxDoc.ballots.length);
      }
      check("6", problems.length === 0, "all " + boxDoc.ballots.length + " cast ballots are well-formed "
        + "anonymous votes (subgroup membership, ring-membership proof, 0-or-1 validity proof)"
        + (problems.length ? " :: " + problems[0] : ""),
        "Every ballot is a sealed vote from an enrolled member — nobody outside the list, nobody twice, nothing malformed.");

      if (failures.length) {
        onSkip("7", "not checked: the ballots did not verify, so neither can their tally");
        return finish(null, rosterDoc, null);
      }

      onSection("7", "The count, recomputed from the sealed sum — no ballot is ever opened");
      const tally = (byType["decision.tally-proof"] || {}).body || {};
      const latest = new Map();
      for (const b of [...ballots].sort((a, b2) => a.seq - b2.seq)) latest.set(b.nullifier, b);
      let C1 = B1, C2 = B1;
      for (const b of latest.values()) {
        C1 = (C1 * fromHex(b.ciphertext.c1)) % P;
        C2 = (C2 * fromHex(b.ciphertext.c2)) % P;
      }
      const sumCt = tally.sum_ciphertext || {};
      check("7", sumCt.c1 === hx(C1) && sumCt.c2 === hx(C2) && Object.keys(sumCt).length === 2,
        "the logged sum ciphertext is the homomorphic product of the " + latest.size + " counted ballots",
        "The sealed total really is all the counted ballots added together — this page redid the addition.");

      // Each share proves itself against a trustee key DERIVED from the
      // commitments: h_i = A0 * A1^i.
      const shares = tally.trustee_shares || [];
      const required = trusteesDoc.threshold.required;
      const valid = [];
      for (const s of shares) {
        const idx = s.index, d = fromHex(s.share || "0");
        if (!Number.isInteger(idx) || idx < 1 || idx > trusteesDoc.threshold.of) continue;
        if (valid.some(v => v[0] === idx) || !inGroup(d)) continue;
        const h_i = (A[0] * modpow(A[1], BigInt(idx), P)) % P;
        const prf = s.proof || {};
        const stmt = { t: "cp", ctx: decisionId, index: idx, h_i: hx(h_i),
                       c1: hx(C1), d: s.share, a: prf.a, b: prf.b };
        const c = await fsChallenge(stmt, Q), z = fromHex(prf.z || "0");
        const a_ = fromHex(prf.a || "0"), b_ = fromHex(prf.b || "0");
        if (modpow(G, z, P) === (a_ * modpow(h_i, c, P)) % P
          && modpow(C1, z, P) === (b_ * modpow(d, c, P)) % P) valid.push([idx, d]);
      }
      check("7", valid.length >= required,
        "a " + required + "-of-" + trusteesDoc.threshold.of + " trustee quorum proved the decryption ("
        + valid.length + "/" + required + " required Chaum-Pedersen decryption proofs valid)",
        "Enough independent key-holders proved their part of the unsealing, honestly.");

      let countsDec = null, T = null;
      if (valid.length >= required) {
        let D = B1;
        for (const [idx, d] of valid) {
          let lam = B1;
          for (const [jdx] of valid) {
            if (jdx !== idx) {
              lam = (lam * BigInt(jdx)) % Q;
              lam = (lam * modinv(BigInt(jdx - idx), Q)) % Q;
            }
          }
          D = (D * modpow(d, lam, P)) % P;
        }
        const gT = (C2 * modinv(D, P)) % P;
        let acc = B1;
        for (let t_ = 0; t_ <= latest.size; t_++) {
          if (acc === gT) { T = t_; break; }
          acc = (acc * G) % P;
        }
        check("7", T !== null, "the combined decryption opens as a small exponent (the sum is well-formed)",
        "The unsealed total is a sensible number of votes.");
        if (T !== null) {
          countsDec = {};
          countsDec[options[0]] = T;
          countsDec[options[1]] = latest.size - T;
        }
      }
      const announced = tally.counts || {};
      check("7", countsDec !== null && deepEq(announced, countsDec),
        "announced counts match the threshold decryption: "
        + (countsDec ? Object.entries(countsDec).map(([k, v]) => k + " " + v).join(", ") : "(no decryption)"),
        "The announced result matches what this page just recomputed.");
      check("7", tally.distinct_voters === latest.size
        && tally.superseded === ballots.length - latest.size,
        "recast policy applied: " + ballots.length + " valid ballots, " + latest.size + " distinct linking "
        + "tags counted, " + (ballots.length - latest.size) + " silently superseded (last ballot counts)",
        "Where someone re-voted, only their last ballot counted.");

      // A transcript in which every proof verifies can still be a lie of
      // omission. The last check is against something outside it: the closing
      // head, republished beyond the collusion's reach.
      if (failures.length) {
        onSkip("8", "not checked: the transcript did not verify, so no anchor can vouch for it");
        return finish(null, rosterDoc, null);
      }

      onSection("8", "The closing head matches the copy the world saw (the anchor)");
      const receipts = typeof files["anchor.json"] === "string"
        ? (JSON.parse(files["anchor.json"]).receipts || []) : [];
      const requiredAnchors = anchors.anchors || [];
      const fullRoot = "sha256:" + bytesToHex(await merkleRoot(leaves));
      async function receiptOk(r) {
        const body = stripKey(r, "sig");
        const kid = (r.sig || {}).key_id || "";
        return (await sigOk(trust[kid] || "", r.sig || {}, body))
          && body.log_id === (manifest.community || {}).id
          && body.size === entries.length
          && body.root === fullRoot;
      }
      const unanchored = [];
      for (const a of requiredAnchors) {
        let ok = false;
        for (const r of receipts) {
          const kid = (r.sig || {}).key_id || "";
          if ((kid === a || kid.startsWith(a + "#")) && await receiptOk(r)) { ok = true; break; }
        }
        if (!ok) unanchored.push(a);
      }
      check("8", requiredAnchors.length > 0 && unanchored.length === 0,
        "the closing head is anchored outside the collusion set (" + requiredAnchors.length + " required "
        + "anchor(s) hold a valid receipt for this exact history)"
        + (requiredAnchors.length ? "" : " :: the trust anchors name no external anchor, and an "
          + "unanchored log cannot refute a quietly erased ballot")
        + (unanchored.length ? " :: no valid receipt from [" + unanchored.join(", ") + "] matches this "
          + "log's closing head — the history under audit is not the history the world saw" : ""),
        "The world's copy of the closing fingerprint matches this record — history was not quietly shortened after the close.");

      return finish(countsDec, rosterDoc, latest);
    } catch (e) {
      return result("NOT VERIFIED",
        "the transcript is malformed: " + (e && e.name ? e.name + ": " + e.message : String(e)), null);
    }
  }

  // ------------------------------------------------------- find my ballot
  // The voter-side recorded-as-cast check: from a nym secret, recompute the
  // linking tag for this decision and look it up in the published box. Runs
  // entirely in this page; the secret never leaves it.
  async function findBallot(files, secretHex) {
    const trusteesDoc = JSON.parse(files["trustees.json"]);
    const boxDoc = JSON.parse(files["ballot-box.json"]);
    const rosterDoc = JSON.parse(files["roster.json"]);
    const entries = files["log.jsonl"].split("\n").filter(l => l.trim()).map(l => JSON.parse(l));
    const opened = entries.filter(e => e.type === "decision.opened").pop();
    if (!opened) throw new Error("no decision.opened entry in the log");
    const decisionId = opened.body.decision_id;
    if (!(trusteesDoc.group in KNOWN_GROUPS)) throw new Error("unknown ballot group");
    const P = KNOWN_GROUPS[trusteesDoc.group];
    const x = fromHex(secretHex.trim().replace(/^0x/, ""));
    let hl = null;
    for (let i = 0; i < 64 && hl === null; i++) {
      const c = bytesToBig(await sha256(te.encode("civic-kernel/ctx|" + decisionId + "|" + i))) % P;
      if (c > B1 && modpow(c, B2, P) !== B1) hl = modpow(c, B2, P);
    }
    const tag = hx(modpow(hl, x, P));
    const pub = hx(modpow(B2, x, P));
    const member = rosterDoc.members.find(m => m.voter_pub === pub) || null;
    const mine = boxDoc.ballots.filter(b => b.nullifier === tag).sort((a, b) => a.seq - b.seq);
    const maxSeq = mine.length ? mine[mine.length - 1].seq : null;
    return {
      decisionId, tag,
      enrolled: member !== null,
      memberName: member ? member.member : null,
      ballots: mine.map(b => ({ seq: b.seq, counted: b.seq === maxSeq })),
    };
  }

  return { verify, findBallot, edSupported, _internals: { canonStr, schemaErrors, SCHEMAS } };
});
