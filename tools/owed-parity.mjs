#!/usr/bin/env node
// Owed parity: the two entitlement engines — owed.js (the page's) and
// entitlements/judge.py (the independent judge) — must produce identical
// claim-traces over the persona battery, and every persona's hand-checked
// expectations must hold in BOTH. Also the structural honesty checks the
// plan (docs/wedge-one-v0.md) demands: the corpus embedded in owed.html is
// byte-equivalent to entitlements/uk/*.json (generated, never trusted); no
// network API appears anywhere in the page or its engine (the no-speculative-
// query claim, enforced by construction); and the corpus tax year is loudly
// stale unless explicitly acknowledged.
import { createRequire } from "module";
import { execFileSync } from "child_process";
import { readdirSync, readFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const Owed = require(path.join(ROOT, "owed.js"));

let failures = 0;
const say = (ok, what) => {
  console.log((ok ? "  ok   " : "  FAIL ") + what);
  if (!ok) failures++;
};

// canonical JSON for deep comparison (sorted keys, compact)
function canon(o) {
  if (o === null || typeof o !== "object") return JSON.stringify(o);
  if (Array.isArray(o)) return "[" + o.map(canon).join(",") + "]";
  return "{" + Object.keys(o).sort().map(k => JSON.stringify(k) + ":" + canon(o[k])).join(",") + "}";
}

// --- the corpus, from the files
const UK = path.join(ROOT, "entitlements", "uk");
const spa = JSON.parse(readFileSync(path.join(UK, "spa.json"), "utf8"));
const ents = [];
for (const f of readdirSync(UK).sort()) {
  const doc = JSON.parse(readFileSync(path.join(UK, f), "utf8"));
  if (doc.v === "civic-kernel/entitlement-rules/v0") ents.push(doc);
}
say(ents.length === 6, "corpus loaded: " + ents.length + " entitlements + the pensionable-age table");

// --- no network API anywhere in the page or its engine, by construction
for (const f of ["owed.js", "owed.html"]) {
  const text = readFileSync(path.join(ROOT, f), "utf8");
  const hit = /fetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|EventSource|importScripts/.exec(text);
  say(!hit, f + " contains no network request API at all" + (hit ? " :: found " + hit[0] : ""));
}

// --- staleness is loud: the corpus must name the current tax year or say why not
const now = new Date();
const ty = now.getUTCMonth() + 1 > 4 || (now.getUTCMonth() + 1 === 4 && now.getUTCDate() >= 6)
  ? now.getUTCFullYear() : now.getUTCFullYear() - 1;
const currentTaxYear = ty + "-" + String((ty + 1) % 100).padStart(2, "0");
for (const ent of ents) {
  const eff = ent.effective;
  say(eff.tax_year === currentTaxYear || typeof eff.stale_acknowledged === "string",
    ent.id + ": tax year " + eff.tax_year
    + (eff.tax_year === currentTaxYear ? " is current (" + currentTaxYear + ")"
      : (eff.stale_acknowledged ? " is stale but acknowledged: " + eff.stale_acknowledged
        : " is STALE (current is " + currentTaxYear + ") and unacknowledged — re-check the amounts and re-pin")));
}

// --- the corpus embedded in owed.html equals the files (generated, never trusted)
const page = readFileSync(path.join(ROOT, "owed.html"), "utf8");
const m = /\/\/OWED-CORPUS-START\s*\nconst CORPUS = (.*);\s*\/\/OWED-CORPUS-END/s.exec(page);
say(!!m, "owed.html carries the corpus between its markers");
if (m) {
  let embedded = null;
  try { embedded = JSON.parse(m[1]); } catch (e) { say(false, "embedded corpus parses: " + e.message); }
  if (embedded) {
    say(canon(embedded.spa) === canon(spa), "embedded pensionable-age table equals entitlements/uk/spa.json");
    say(canon(embedded.entitlements) === canon(ents),
      "embedded entitlements equal entitlements/uk/*.json (tools/validate.py regenerates this block)");
  }
}

// --- the circumstances file: what the page saves, the page and the judge reload
// identically — persona-shaped on purpose
const PERSONAS = path.join(ROOT, "entitlements", "personas");
{
  let rt = true, why = "";
  for (const f of readdirSync(PERSONAS).sort()) {
    const p = JSON.parse(readFileSync(path.join(PERSONAS, f), "utf8"));
    const doc = JSON.parse(JSON.stringify(Owed.circumstancesFile(p.answers, p.as_of)));
    if (canon(Owed.circumstancesAnswers(doc)) !== canon(p.answers)) { rt = false; why = f; break; }
    if (doc.v !== "civic-kernel/circumstances/v0" || !/KEEP PRIVATE/.test(doc.note)) { rt = false; why = f + " (envelope)"; break; }
  }
  say(rt, "circumstances files round-trip every persona's answers identically, privacy note included"
    + (why ? " :: " + why : ""));
}

// --- both engines, every persona: expectations hold and the full traces agree
for (const f of readdirSync(PERSONAS).sort()) {
  const persona = JSON.parse(readFileSync(path.join(PERSONAS, f), "utf8"));
  const js = {};
  for (const ent of ents) js[ent.id] = Owed.evaluate(ent, spa, persona.answers, persona.as_of);
  let expectOk = true, detail = "";
  for (const [eid, expect] of Object.entries(persona.expect || {})) {
    for (const [key, want] of Object.entries(expect)) {
      const got = js[eid] ? js[eid][key] : undefined;
      if (canon(got === undefined ? null : got) !== canon(want)) {
        expectOk = false;
        detail = " :: " + eid + "." + key + " = " + JSON.stringify(got) + ", expected " + JSON.stringify(want);
      }
    }
  }
  say(expectOk, persona.name + " — owed.js meets every expectation" + detail);
  let py = null;
  try {
    py = JSON.parse(execFileSync("python3",
      [path.join(ROOT, "entitlements", "judge.py"), UK, "--persona", path.join(PERSONAS, f), "--json"],
      { stdio: "pipe" }).toString());
  } catch (e) {
    say(false, persona.name + " — judge.py ran :: " + (e.stderr || e.message).toString().slice(0, 120));
    continue;
  }
  say(canon(js) === canon(py), persona.name + " — the two engines' full traces are identical");
}

if (failures) {
  console.log(failures + " owed-parity failure(s) — the page and the judge do not agree");
  process.exit(1);
}
console.log("owed parity: two engines, one corpus, identical traces — and no way to phone home");
