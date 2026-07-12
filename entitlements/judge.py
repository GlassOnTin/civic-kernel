#!/usr/bin/env python3
"""The independent entitlement judge.

Second implementation of the entitlements engine: reads the same rules
files as owed.js and shares no code with it — the producer/judge
discipline the election pages use, pointed at welfare arithmetic. Given a
persona (answers + an as-of date + expected outcomes), it evaluates every
entitlement in the corpus and refuses loudly when an expectation does not
hold. tools/owed-parity.mjs runs both engines over the persona battery and
diffs the full traces.

Semantics, shared with owed.js because the corpus defines them: integers
throughout (money is pence, booleans are 0/1), `if` tests non-zero,
and/or short-circuit; ages are attained on the anniversary of birth;
month arithmetic preserves the day of the month, clamped to the month's
length.

Usage:
  judge.py <entitlements-uk-dir> --persona <persona.json> [--json]
    --json prints {entitlement_id: trace} and skips expectation checks

A circumstances file saved by owed.html is persona-shaped and runs here
unchanged — your own file, through the independent judge.
"""
import json
import math
import sys
from datetime import date
from pathlib import Path


def parse_date(s: str) -> date:
    return date.fromisoformat(str(s).strip())


def days_in_month(y: int, m: int) -> int:
    if m == 12:
        return 31
    return (date(y, m + 1, 1) - date(y, m, 1)).days


def add_years_months(d: date, years: int, months: int) -> date:
    y = d.year + years + (d.month + months - 1) // 12
    m = (d.month + months - 1) % 12 + 1
    return date(y, m, min(d.day, days_in_month(y, m)))


def spa_date(dob_str: str, spa: dict) -> date:
    dob = parse_date(dob_str)
    if dob < parse_date(spa["before"]["born"]):
        return add_years_months(dob, spa["before"]["years"], 0)
    for row in spa["table"]:
        if parse_date(row["born_from"]) <= dob <= parse_date(row["born_to"]):
            return add_years_months(dob, row["years"], row["months"])
    if parse_date(spa["after"]["born"]) <= dob <= parse_date(spa["after"]["until"]):
        return add_years_months(dob, spa["after"]["years"], 0)
    sys.exit(f"date of birth beyond the pensionable-age table ({spa['after']['until']})")


class Eval:
    def __init__(self, ent: dict, spa: dict, answers: dict, as_of: str):
        self.spa = spa
        self.answers = answers
        self.as_of = parse_date(as_of)
        self.by_id = {v["id"]: v for v in ent["values"]}
        self.memo: dict = {}

    def answer(self, qid: str):
        if qid not in self.answers:
            sys.exit(f"unanswered question: {qid}")
        return self.answers[qid]

    def date_operand(self, e: dict) -> str:
        if "get" in e:
            return str(self.answer(e["get"]))
        sys.exit("expected a question reference for a date operand")

    def ev(self, e: dict) -> int:
        if "num" in e:
            return e["num"]
        if "get" in e:
            a = self.answer(e["get"])
            if isinstance(a, bool):
                return 1 if a else 0
            if not isinstance(a, int):
                sys.exit(f"answer {e['get']} is not an integer: {a!r}")
            return a
        if "val" in e:
            vid = e["val"]
            if vid not in self.by_id:
                sys.exit(f"unknown value: {vid}")
            if vid not in self.memo:
                self.memo[vid] = self.ev(self.by_id[vid]["expr"])
            return self.memo[vid]
        if "add" in e:
            return sum(self.ev(x) for x in e["add"])
        if "sub" in e:
            return self.ev(e["sub"][0]) - self.ev(e["sub"][1])
        if "mul" in e:
            r = 1
            for x in e["mul"]:
                r *= self.ev(x)
            return r
        if "max" in e:
            return max(self.ev(x) for x in e["max"])
        if "min" in e:
            return min(self.ev(x) for x in e["min"])
        if "ceil_div" in e:
            a, b = self.ev(e["ceil_div"][0]), self.ev(e["ceil_div"][1])
            if b <= 0:
                sys.exit(f"ceil_div by {b}")
            return math.ceil(a / b)
        if "gt" in e:
            return int(self.ev(e["gt"][0]) > self.ev(e["gt"][1]))
        if "gte" in e:
            return int(self.ev(e["gte"][0]) >= self.ev(e["gte"][1]))
        if "lt" in e:
            return int(self.ev(e["lt"][0]) < self.ev(e["lt"][1]))
        if "lte" in e:
            return int(self.ev(e["lte"][0]) <= self.ev(e["lte"][1]))
        if "eq" in e:
            return int(self.ev(e["eq"][0]) == self.ev(e["eq"][1]))
        if "and" in e:
            for x in e["and"]:
                if not self.ev(x):
                    return 0
            return 1
        if "or" in e:
            for x in e["or"]:
                if self.ev(x):
                    return 1
            return 0
        if "not" in e:
            return 0 if self.ev(e["not"]) else 1
        if "if" in e:
            c, t, f = e["if"]
            return self.ev(t) if self.ev(c) else self.ev(f)
        if "age_at_least" in e:
            dob = parse_date(self.date_operand(e["age_at_least"]["dob"]))
            return int(add_years_months(dob, e["age_at_least"]["years"], 0) <= self.as_of)
        if "born_on_or_before" in e:
            dob = parse_date(self.date_operand(e["born_on_or_before"]["dob"]))
            return int(dob <= parse_date(e["born_on_or_before"]["date"]))
        if "spa_reached" in e:
            return int(spa_date(self.date_operand(e["spa_reached"]["dob"]), self.spa) <= self.as_of)
        sys.exit(f"unknown expression: {json.dumps(e)[:60]}")


def demanded(ent: dict, spa: dict, answers: dict, as_of: str) -> list:
    ev = Eval(ent, spa, answers, as_of)
    out = []
    for q in ent["questions"]:
        if "when" not in q or ev.ev(q["when"]):
            out.append({"id": q["id"], "label": q["label"], "rule": q["rule"], "uri": q["uri"]})
    return out


def evaluate(ent: dict, spa: dict, answers: dict, as_of: str) -> dict:
    trace = {
        "v": "civic-kernel/claim-trace/v0",
        "entitlement": ent["id"],
        "kind": ent["kind"],
        "tax_year": ent["effective"]["tax_year"],
        "as_of": as_of,
        "verdict": None, "weekly": None, "because": None, "rule": None, "uri": None,
        "demanded": demanded(ent, spa, answers, as_of),
        "steps": [],
        "not_asked": ent["not_asked"],
    }
    if ent["kind"] == "local":
        v = ent["verdicts"][0]
        trace.update(verdict=v["verdict"], because=v["because"], rule=v["rule"], uri=v["uri"])
        return trace
    ev = Eval(ent, spa, answers, as_of)
    for g in ent["gates"]:
        if ev.ev(g["when"]):
            trace.update(verdict=g["verdict"], because=g["because"], rule=g["rule"], uri=g["uri"])
            return trace
    for v in ent["values"]:
        if v["id"] not in ev.memo:
            ev.memo[v["id"]] = ev.ev(v["expr"])
        trace["steps"].append({"id": v["id"], "plainly": v["plainly"], "rule": v["rule"],
                               "uri": v["uri"], "result": ev.memo[v["id"]]})
    for v in ent["verdicts"]:
        if ev.ev(v["when"]):
            trace.update(verdict=v["verdict"], because=v["because"], rule=v["rule"], uri=v["uri"])
            if "weekly" in v:
                trace["weekly"] = ev.ev(v["weekly"])
            return trace
    sys.exit(f"{ent['id']}: no verdict matched — the corpus must end with a catch-all")


def main() -> int:
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    if len(args) != 3 or args[1] != "--persona":
        print(__doc__, file=sys.stderr)
        return 2
    corpus_dir, persona_path = Path(args[0]), Path(args[2])
    spa = json.loads((corpus_dir / "spa.json").read_text())
    ents = {}
    for p in sorted(corpus_dir.glob("*.json")):
        doc = json.loads(p.read_text())
        if doc.get("v") == "civic-kernel/entitlement-rules/v0":
            ents[doc["id"]] = doc
    persona = json.loads(persona_path.read_text())
    results = {eid: evaluate(ent, spa, persona["answers"], persona["as_of"])
               for eid, ent in ents.items()}
    if as_json:
        print(json.dumps(results, indent=1, ensure_ascii=False))
        return 0
    failures = 0
    for eid, expect in persona.get("expect", {}).items():
        if eid not in results:
            print(f"  FAIL {persona['name']}: expects unknown entitlement {eid}")
            failures += 1
            continue
        got = results[eid]
        for key, want in expect.items():
            if got.get(key) != want:
                print(f"  FAIL {persona['name']} / {eid}: {key} = {got.get(key)!r}, expected {want!r}")
                failures += 1
    if failures:
        return 1
    summary = ", ".join(k + "=" + str(v.get("verdict")) for k, v in results.items())
    print(f"  ok   {persona['name']}: every expectation holds ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
