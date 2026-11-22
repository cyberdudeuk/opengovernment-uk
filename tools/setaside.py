"""Decide the near-name pairs that reconciliation set aside -> data/set-aside.json

Each pair is a register record and an ONS name that look alike. The rules, in order (the first that applies decides):
  R1  both names state a nation (England, Scotland or Scottish, Wales or Welsh, Northern Ireland or (NI), Irish)
      and the nations differ: two different records.
  R2  one name states a nation, and the other record's own nation, from an explicit source (its register, its own
      site, a statute, Wikidata, an ONS code, the 2020 public bodies list), does not include it: two different records.
  R2b the names are identical once the nation qualifier is removed, and the stated nation is the record's own nation:
      one body (the earlier cleaning rule, now allowed because the nations agree).
  R3  each name resolves to exactly one Wikidata item (label or alias, read 22 November 2026): the same item means
      one body, two items mean two records. A name that matches several items gives no verdict.
  R5  the names are identical once spaces and punctuation are removed ("One North East", "One NorthEast"): one body.
  M   decided from an official page, with a quote that --verify checks is still there
      (sources/evidence/set-aside-decisions.json).
Anything else stays on the list for a person. Decided pairs leave the list; 'same' pairs with an ONS record of their
own are joined by tools/sameas.py (rule S5).

  python tools/setaside.py             decide, check, write
  python tools/setaside.py --verify    also fetch every quoted page and check the quote is on it
  python tools/setaside.py --negative  prove the checks fail when they should
"""
import collections, html, json, pathlib, re, subprocess, sys, unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
EV = ROOT / "sources/evidence"
NAT = [(r"\bnorthern ireland\b|\(ni\)|\birish\b", "NI"), (r"\bscotland\b|\bscottish\b", "SC"), (r"\bwales\b|\bwelsh\b", "WA"), (r"\bengland\b|\benglish\b", "EN")]
EXP = {"GB": {"EN", "SC", "WA"}, "UK": {"EN", "SC", "WA", "NI"}}
EXPLICIT = {"register", "own-site", "statute", "wikidata", "ons-gss", "pb-2020"}  # not 'chain' or 'ons-sponsor', which are inferred


def stated(name):
    low = name.lower()
    return {c for p, c in NAT if re.search(p, low)}


def expand(ns):
    return set().union(*[EXP.get(n, {n}) for n in ns]) if ns else set()


def fold(n):
    return unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower().replace("&", " and ")


def core(n):
    n = re.sub(r"\((northern ireland|ni|england and wales|wales|scotland|england)\)|\bfor (northern ireland|england|wales|scotland)\b|^the |^northern ireland |^scottish |^welsh ", "", fold(n))
    return re.sub(r"[^a-z0-9]+", " ", n).strip()


def letters(n):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"^the ", "", fold(n)))


def load():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    ev = json.loads((ROOT / "data/nation-evidence.json").read_text())["bodies"]
    bn = json.loads((ROOT / "data/body-nations.json").read_text())
    Q = collections.defaultdict(set)
    for x in json.loads((EV / "wikidata-set-aside.json").read_text())["rows"]: Q[x["n"]].add(x["item"].rsplit("/", 1)[1])
    man = {(m["id"], m["ons"]): m for m in json.loads((EV / "set-aside-decisions.json").read_text())["manual"]}
    return D, ev, bn, Q, man


def decide(x, D, ev, bn, Q, man, byname):
    a, b = stated(x["name"]), stated(x["ons"])
    rec = ev.get(x["id"], {}); rn = expand(bn.get(x["id"]) or []); basis = rec.get("basis")
    ons = [i for i in byname.get(x["ons"], []) if i.startswith("ons-name:")]
    on = expand(bn.get(ons[0]) or []) if ons else set()
    out = {"id": x["id"], "name": x["name"], "ons": x["ons"], "ons_id": ons[0] if len(ons) == 1 else "", "set_aside_because": x["reason"]}
    if a and b and a != b:
        return {**out, "decision": "different", "rule": "R1", "why": f"both names state a nation, and they differ ({', '.join(sorted(a))} against {', '.join(sorted(b))})"}
    if b and not a and basis in EXPLICIT and rn and not (b & rn):
        return {**out, "decision": "different", "rule": "R2", "why": f"the ONS name states {', '.join(sorted(b))}; the register record's own nation ({', '.join(sorted(rn))}, from {basis}) does not include it"}
    if a and not b and on and ons and json.loads((ROOT / "data/nation-evidence.json").read_text())["bodies"].get(ons[0], {}).get("basis") in EXPLICIT and not (a & on):
        return {**out, "decision": "different", "rule": "R2", "why": f"the register name states {', '.join(sorted(a))}; the ONS record's own nation does not include it"}
    s = a or b
    if core(x["name"]) == core(x["ons"]) and s and s == (rn or on):
        return {**out, "decision": "same", "rule": "R2b", "why": f"the names are identical once the nation qualifier is removed, and both are {', '.join(sorted(s))}"}
    qa, qb = Q.get(x["name"], set()), Q.get(x["ons"], set())
    if len(qa) == 1 and len(qb) == 1:
        return {**out, "decision": "same" if qa == qb else "different", "rule": "R3", "why": f"Wikidata: {next(iter(qa))} and {next(iter(qb))}", "evidence": [{"title": "Wikidata " + q, "url": "https://www.wikidata.org/wiki/" + q} for q in sorted(qa | qb)]}
    if letters(x["name"]) == letters(x["ons"]):
        return {**out, "decision": "same", "rule": "R5", "why": "the names are identical once spaces and punctuation are removed"}
    m = man.get((x["id"], x["ons"]))
    if m: return {**out, "decision": m["decision"], "rule": "M", "why": m["why"], "evidence": m["evidence"]}
    return {**out, "decision": "", "rule": "", "why": "no rule applies and no official source decides it; left for a person"}


def build():
    D, ev, bn, Q, man = load()
    byname = collections.defaultdict(list)
    for r in D["r"]: byname[r[1]].append(r[0])
    pairs = [decide(x, D, ev, bn, Q, man, byname) for x in D["a"]]
    return {"read": "2026-11-22", "pairs": pairs, "unused_manual": sorted(f"{i} | {o}" for (i, o) in man if not any(p["id"] == i and p["ons"] == o for p in pairs))}


def check(out):
    e = []
    P = {(p["name"], p["ons"]): p for p in out["pairs"]}
    known = {("Police Service of Northern Ireland", "Police Service of Scotland"): ("different", "R1"),
             ("Labour Relations Agency (Northern Ireland)", "Labour Relations Agency"): ("same", "R2b"),
             ("The Charity Commission", "Charity Commission of Northern Ireland"): ("different", "R2"),
             ("One North East", "One NorthEast"): ("same", "R5"),
             ("Health and Safety Executive", "Health and Safety Executive for Northern Ireland"): ("different", "M"),
             ("Information Commission", "Information Commissioner"): ("different", "M")}
    for k, (d, r) in known.items():
        p = P.get(k)
        if not p or (p["decision"], p["rule"]) != (d, r): e.append(f"known answer: {k} should be {d} by {r}, got {p and (p['decision'], p['rule'])}")
    for p in out["pairs"]:
        a, b = stated(p["name"]), stated(p["ons"])
        if p["decision"] == "same" and a and b and a != b: e.append(f"joined across stated nations: {p['name']} = {p['ons']}")  # the user's rule, as a guard
        if p["rule"] == "M" and not all(x.get("quote") and x.get("url", "").startswith("https://www.") for x in p.get("evidence", [])): e.append(f"decision without a quoted official source: {p['name']} | {p['ons']}")
        if p["decision"] and not p["why"]: e.append(f"decision without a reason: {p['name']}")
    if out["unused_manual"]: e.append(f"manual decisions that match no set-aside pair: {out['unused_manual']}")
    return e


def same_as_guard(sa=None):
    """Widened check: across the whole register, no same-as group may hold two names that state different nations."""
    sa = sa if sa is not None else json.loads((ROOT / "data/same-as.json").read_text())["groups"]
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    nm = {r[0]: r[1] for r in D["r"]}
    bad = []
    for c, g in sa.items():
        ns = {frozenset(stated(nm.get(m, ""))) for m in [c, *g["members"]]} - {frozenset()}
        if len(ns) > 1 and not any(set(x) >= set().union(*ns) for x in ns): bad.append(f"{nm.get(c, c)}: {[nm.get(m, m) for m in g['members']]}")
    return bad


def text(url):
    if url.startswith("https://www.gov.uk/"):
        r = subprocess.run(["curl", "-s", "-m", "40", url.replace("https://www.gov.uk/", "https://www.gov.uk/api/content/")], capture_output=True, text=True).stdout  # noqa: S603,S607 fixed program, URL from our own evidence file
        try: j = json.loads(r)
        except ValueError: return ""
        linked = [x.get("title") or "" for k in ("ordered_successor_organisations", "ordered_parent_organisations") for x in (j.get("links") or {}).get(k) or []]
        return html.unescape(re.sub(r"\s+", " ", " ".join([j.get("title") or "", j.get("description") or "", re.sub(r"<[^>]+>", " ", str((j.get("details") or {}).get("body") or "")), *linked])))
    r = subprocess.run(["curl", "-s", "-L", "-m", "40", "-A", "OpenGovernmentUK/0.4", url], capture_output=True, text=True).stdout  # noqa: S603,S607
    r = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", r, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r)))


def verify(out):
    e = []
    for p in out["pairs"]:
        for x in p.get("evidence", []):
            if x.get("quote") and x["quote"] not in text(x["url"]): e.append(f"quote not found: {x['quote']!r} on {x['url']}")
    return e


def main():
    out = build()
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(out)); bad["pairs"][0]["decision"] = "same"; bad["pairs"][0]["ons"] = "Police Service of Scotland"; bad["pairs"][0]["name"] = "Police Service of Northern Ireland"
        nq = json.loads(json.dumps(out)); [x.pop("quote", None) for p in nq["pairs"] if p["rule"] == "M" for x in p["evidence"]]
        ka = json.loads(json.dumps(out)); ka["pairs"] = [p for p in ka["pairs"] if p["ons"] != "Police Service of Scotland"]
        caught = [bool(check(bad)), bool(check(nq)), bool(check(ka)),
                  bool(same_as_guard({"government-organisation:OT657": {"members": ["ons-name:police-service-of-scotland"]}}))]
        if "--verify" in sys.argv:  # needs the network, so only with --verify
            caught.append(bool(verify({"pairs": [{"evidence": [{"url": "https://www.legislation.gov.uk/ukpga/2025/18/section/118", "quote": "the office of Information Commissioner is retained"}]}]})))
        if not all(caught): sys.exit(f"setaside negative: {caught.count(False)} of {len(caught)} not caught")
        print(f"setaside negative: all {len(caught)} breakers caught"); return
    e = check(out)
    if (ROOT / "data/same-as.json").exists(): e += [f"same-as group joins records whose names state different nations: {b}" for b in same_as_guard()]
    if "--verify" in sys.argv: e += verify(out)
    if e: sys.exit("setaside: " + "; ".join(e))
    (ROOT / "data/set-aside.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
    c = collections.Counter((p["decision"] or "left for a person", p["rule"]) for p in out["pairs"])
    print("setaside:", len(out["pairs"]), "pairs;", dict(sorted(c.items(), key=str)), "; verified quotes" if "--verify" in sys.argv else "")


if __name__ == "__main__":
    main()
