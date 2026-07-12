/* Civic Kernel — the entitlement engine, in JavaScript.
 *
 * Runs an entitlements/*.json rules file against one household's answers,
 * entirely on the device: evaluates the little expression language the
 * corpus is written in (integer pence throughout; booleans are 0/1), fires
 * the gates in order, computes every named value as a trace step, and
 * returns a claim-trace — verdict, weekly amount, which rules fired, what
 * was demanded and under what authority, and what was deliberately not
 * asked.
 *
 * The corpus is the whole logic: this file knows no benefit rules, no
 * amounts, no thresholds. Change the law, change the JSON — this file does
 * not change. entitlements/judge.py is the independent second engine,
 * sharing these rules files and nothing else; tools/owed-parity.mjs holds
 * the two to identical outputs over the persona battery in CI.
 *
 * No network anywhere in this file, by construction — the parity test
 * greps for the absence of every request API. Dates: ages are attained on
 * the anniversary of birth; month arithmetic preserves the day, clamped to
 * the month's length (a one-day generosity for 29 February births, noted
 * rather than hidden).
 *
 * Runs in a browser (script tag, used by owed.html) or in Node >= 20.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CivicOwed = factory();
})(typeof self !== "undefined" ? self : globalThis, function () {
  "use strict";

  // ---------------------------------------------------------------- dates
  function parseDate(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s).trim());
    if (!m) throw new Error("not a date (YYYY-MM-DD): " + s);
    return { y: +m[1], m: +m[2], d: +m[3] };
  }
  function daysInMonth(y, m) {
    return [31, (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0 ? 29 : 28,
      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1];
  }
  function addYearsMonths(date, years, months) {
    let y = date.y + years, m = date.m + months;
    y += Math.floor((m - 1) / 12);
    m = ((m - 1) % 12) + 1;
    return { y, m, d: Math.min(date.d, daysInMonth(y, m)) };
  }
  function cmpDate(a, b) {
    return a.y - b.y || a.m - b.m || a.d - b.d;
  }
  function spaDate(dobStr, spa) {
    const dob = parseDate(dobStr);
    if (cmpDate(dob, parseDate(spa.before.born)) < 0) {
      return addYearsMonths(dob, spa.before.years, 0);
    }
    for (const row of spa.table) {
      if (cmpDate(dob, parseDate(row.born_from)) >= 0 && cmpDate(dob, parseDate(row.born_to)) <= 0) {
        return addYearsMonths(dob, row.years, row.months);
      }
    }
    if (cmpDate(dob, parseDate(spa.after.born)) >= 0 && cmpDate(dob, parseDate(spa.after.until)) <= 0) {
      return addYearsMonths(dob, spa.after.years, 0);
    }
    throw new Error("date of birth is beyond this corpus's pensionable-age table (" + spa.after.until + ")");
  }

  // ------------------------------------------------------------ expressions
  // Everything is an integer: money is pence, booleans are 0/1, `if` tests
  // non-zero, and/or short-circuit.
  function makeEval(ent, spa, answers, asOfStr) {
    const asOf = parseDate(asOfStr);
    const byId = {};
    for (const v of ent.values) byId[v.id] = v;
    const memo = {};
    function answer(id) {
      if (!(id in answers)) throw new Error("unanswered question: " + id);
      return answers[id];
    }
    function num(x, what) {
      if (typeof x !== "number" || !Number.isFinite(x) || Math.floor(x) !== x) {
        throw new Error(what + " is not an integer: " + x);
      }
      return x;
    }
    function ev(e) {
      if ("num" in e) return e.num;
      if ("get" in e) {
        const a = answer(e.get);
        if (typeof a === "boolean") return a ? 1 : 0;
        return num(a, "answer " + e.get);
      }
      if ("val" in e) {
        if (!(e.val in byId)) throw new Error("unknown value: " + e.val);
        if (!(e.val in memo)) memo[e.val] = ev(byId[e.val].expr);
        return memo[e.val];
      }
      if ("add" in e) return e.add.reduce((a, x) => a + ev(x), 0);
      if ("sub" in e) return ev(e.sub[0]) - ev(e.sub[1]);
      if ("mul" in e) return e.mul.reduce((a, x) => a * ev(x), 1);
      if ("max" in e) return Math.max(...e.max.map(ev));
      if ("min" in e) return Math.min(...e.min.map(ev));
      if ("ceil_div" in e) {
        const a = ev(e.ceil_div[0]), b = ev(e.ceil_div[1]);
        if (b <= 0) throw new Error("ceil_div by " + b);
        return Math.ceil(a / b);
      }
      if ("gt" in e) return ev(e.gt[0]) > ev(e.gt[1]) ? 1 : 0;
      if ("gte" in e) return ev(e.gte[0]) >= ev(e.gte[1]) ? 1 : 0;
      if ("lt" in e) return ev(e.lt[0]) < ev(e.lt[1]) ? 1 : 0;
      if ("lte" in e) return ev(e.lte[0]) <= ev(e.lte[1]) ? 1 : 0;
      if ("eq" in e) return ev(e.eq[0]) === ev(e.eq[1]) ? 1 : 0;
      if ("and" in e) { for (const x of e.and) if (!ev(x)) return 0; return 1; }
      if ("or" in e) { for (const x of e.or) if (ev(x)) return 1; return 0; }
      if ("not" in e) return ev(e.not) ? 0 : 1;
      if ("if" in e) return ev(e.if[0]) ? ev(e.if[1]) : ev(e.if[2]);
      if ("age_at_least" in e) {
        const dob = parseDate(answerString(e.age_at_least.dob));
        return cmpDate(addYearsMonths(dob, e.age_at_least.years, 0), asOf) <= 0 ? 1 : 0;
      }
      if ("born_on_or_before" in e) {
        const dob = parseDate(answerString(e.born_on_or_before.dob));
        return cmpDate(dob, parseDate(e.born_on_or_before.date)) <= 0 ? 1 : 0;
      }
      if ("spa_reached" in e) {
        return cmpDate(spaDate(answerString(e.spa_reached.dob), spa), asOf) <= 0 ? 1 : 0;
      }
      throw new Error("unknown expression: " + JSON.stringify(e).slice(0, 60));
    }
    function answerString(e) {
      // date-typed operands: a `get` of a date answer
      if ("get" in e) return String(answer(e.get));
      throw new Error("expected a question reference for a date operand");
    }
    return { ev, memo };
  }

  /* Which questions apply to this household (their `when` holds)? The form
   * and the trace's `demanded` both come from here — a question the rules
   * did not demand is never asked and never listed. */
  function demanded(ent, spa, answers, asOf) {
    const { ev } = makeEval(ent, spa, answers, asOf);
    const out = [];
    for (const q of ent.questions) {
      if (q.when === undefined || ev(q.when)) {
        out.push({ id: q.id, label: q.label, rule: q.rule, uri: q.uri });
      }
    }
    return out;
  }

  /* Evaluate one entitlement for one household. Returns the claim-trace. */
  function evaluate(ent, spa, answers, asOf) {
    const trace = {
      v: "civic-kernel/claim-trace/v0",
      entitlement: ent.id,
      kind: ent.kind,
      tax_year: ent.effective.tax_year,
      as_of: asOf,
      verdict: null, weekly: null, because: null, rule: null, uri: null,
      demanded: demanded(ent, spa, answers, asOf),
      steps: [],
      not_asked: ent.not_asked,
    };
    if (ent.kind === "local") {
      const v = ent.verdicts[0];
      trace.verdict = v.verdict; trace.because = v.because; trace.rule = v.rule; trace.uri = v.uri;
      return trace;
    }
    const { ev, memo } = makeEval(ent, spa, answers, asOf);
    for (const g of ent.gates) {
      if (ev(g.when)) {
        trace.verdict = g.verdict; trace.because = g.because; trace.rule = g.rule; trace.uri = g.uri;
        return trace;
      }
    }
    for (const v of ent.values) {
      if (!(v.id in memo)) memo[v.id] = ev(v.expr);
      trace.steps.push({ id: v.id, plainly: v.plainly, rule: v.rule, uri: v.uri, result: memo[v.id] });
    }
    for (const v of ent.verdicts) {
      if (ev(v.when)) {
        trace.verdict = v.verdict; trace.because = v.because; trace.rule = v.rule; trace.uri = v.uri;
        if (v.weekly !== undefined) trace.weekly = ev(v.weekly);
        return trace;
      }
    }
    throw new Error(ent.id + ": no verdict matched — the corpus must end with a catch-all");
  }

  function poundsFromPence(p) {
    return "£" + (p / 100).toFixed(2);
  }

  return { evaluate, demanded, spaDate, poundsFromPence, _internals: { makeEval, addYearsMonths, parseDate } };
});
