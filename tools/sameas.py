"""One record per body: find register records that are the same body seen by different sources, and combine them.

Strict rules (any one is enough; all are recorded with the reason):
  S1  identical name once case, a leading "The", a legal form (Ltd, Limited, plc), punctuation and a trailing number suffix
      on a register key are ignored. Brackets are NOT dropped: "(NI)" or "(Tax)" usually names a different body.
  S2  one name is the other plus a bracket that only spells out its initials, e.g. "Health Education and Improvement Wales (HEIW)".
  S3  both records carry the same strong identifier: LEI, Companies House number, Wikidata item, ONS GSS code, charity number.
  S4  a person decided they are one body from its own page or founding instrument (sources/evidence/reconciliation-decisions.json).
  S5  a set-aside near-name pair decided 'same' by tools/setaside.py (rule and evidence in data/set-aside.json).
Guard: no group may hold names that state different nations (tools/setaside.py same_as_guard).
Never merged: two records with different values for the same strong identifier; two closed records; a closed with an open record.
The canonical record is the one from the most authoritative family (GOV.UK, council, NHS, then ONS-only, then others).
Writes data/same-as.json. --negative proves the checks fail when they should."""
import collections, copy, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
STRONG = ("lei", "companies_house", "wikidata", "gss", "charity_ew")
RANK = ["government-organisation", "local-authority", "nhs-ods", "wikidata", "ons-name"]


def norm(s):
    s = s.lower().replace("&", " and ")
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"\b(ltd|limited|plc|llp)\b\.?", " ", s)
    s = re.sub(r"[^a-z0-9()]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def initials(s):
    return "".join(w[0] for w in re.findall(r"[a-z0-9]+", s) if w not in ("and", "of", "the", "for", "in"))


def acronym_strip(n):
    """S2/S4: drop a trailing bracket that is only a short form of the name: its initials, or a few of its own words."""
    m = re.fullmatch(r"(.+?) \(([a-z0-9 ]+)\)", n)
    if not m: return None
    outer, short = m.group(1), m.group(2)
    if short.replace(" ", "") == initials(outer): return outer
    words = set(re.findall(r"[a-z0-9]+", outer))
    sw = re.findall(r"[a-z0-9]+", short)
    if len(sw) >= 2 and all(w in words for w in sw) and not ({"england", "wales", "scotland", "northern", "ireland", "ni", "gb", "uk"} & set(sw)): return outer
    return None


def build():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    R = {r[0]: r for r in D["r"] if r[4]}
    parent = {k: k for k in R}

    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    why = collections.defaultdict(set)

    def conflict(a, b):
        ia, ib = R[a][10], R[b][10]
        return any(ia.get(k) and ib.get(k) and str(ia[k]) != str(ib[k]) for k in STRONG)

    def join(a, b, rule):
        if a == b or conflict(a, b): return
        why[tuple(sorted((a, b)))].add(rule)
        parent[find(a)] = find(b)
    byname = collections.defaultdict(list)
    for k, r in R.items():
        n = norm(r[1]); byname[n].append(k)
        s = acronym_strip(n)
        if s: byname[s].append(k)
    for n, ks in byname.items():
        for a in ks[1:]:
            rule = "S1 same name" if all(norm(R[x][1]) == n for x in (ks[0], a)) else "S2 name plus a short form in brackets"
            join(ks[0], a, rule)
    for key in STRONG:
        by = collections.defaultdict(list)
        for k, r in R.items():
            v = r[10].get(key)
            if v: by[str(v)].append(k)
        for ks in by.values():
            for a in ks[1:]: join(ks[0], a, f"S3 same {key}")
    for d in json.loads((ROOT / "sources/evidence/reconciliation-decisions.json").read_text())["names"]:
        if d["decision"] == "same" and d.get("match") in R and d["id"] in R: join(d["id"], d["match"], "S4 decided from evidence")
    sa = ROOT / "data/set-aside.json"
    for p in (json.loads(sa.read_text())["pairs"] if sa.exists() else []):
        if p["decision"] == "same" and p.get("ons_id") in R and p["id"] in R: join(p["id"], p["ons_id"], f"S5 set-aside pair decided same ({p['rule']})")
    groups = collections.defaultdict(list)
    for k in R: groups[find(k)].append(k)
    out = {}
    for ks in groups.values():
        if len(ks) < 2: continue
        ks.sort(key=lambda k: (RANK.index(k.split(":")[0]) if k.split(":")[0] in RANK else 9, k))
        canon = ks[0]
        out[canon] = {"members": ks[1:], "names": {k: R[k][1] for k in ks},
                      "rules": sorted({r for a in ks for b in ks if a < b for r in why.get((a, b), ())})}
    return out, R


def check(out, R):
    e = []
    seen = collections.Counter(k for c, g in out.items() for k in [c, *g["members"]])
    if any(v > 1 for v in seen.values()): e.append("a record is in more than one group")
    for c, g in out.items():
        for m in g["members"]:
            for k in STRONG:
                a, b = R[c][10].get(k), R[m][10].get(k)
                if a and b and str(a) != str(b): e.append(f"merged despite different {k}: {c} {m}")
    name = {r[1]: k for k, r in R.items()}
    def same(a, b):
        ia, ib = name.get(a), name.get(b)
        return ia and ib and any(ia in [c, *g["members"]] and ib in [c, *g["members"]] for c, g in out.items())
    must = [("Health Education and Improvement Wales (Heiw)", "Health Education and Improvement Wales"),
            ("Community Health Partnerships Ltd", "Community Health Partnerships Limited"),
            ("NHS Confederation", "The NHS Confederation"),
            ("Sentencing Council for England and Wales", "The Sentencing Council for England and Wales (Sentencing Council)"),
            ("Labour Relations Agency (Northern Ireland)", "Labour Relations Agency")]  # OG-D55: both are the Northern Ireland agency (GOV.UK; ONS sponsor)
    never = [("Construction Industry Training Board", "Construction Industry Training Board (NI)"),
             ("First-tier Tribunal (Tax)", "First-tier Tribunal (Property Chamber)"),
             ("Health and Safety Executive", "Health and Safety Executive for Northern Ireland"),
             ("The Charity Commission", "Charity Commission of Northern Ireland")]
    for a, b in must:
        if not same(a, b): e.append(f"known merge missing: {a} = {b}")
    for a, b in never:
        if same(a, b): e.append(f"wrong merge: {a} = {b}")
    sys.path.insert(0, str(ROOT / "tools")); from setaside import same_as_guard  # noqa: E402
    e += [f"group joins names that state different nations: {b}" for b in same_as_guard(out)]
    vel = [k for k, r in R.items() if r[1] == "Velindre NHS Trust"]
    if len(vel) == 2 and not any(set(vel) <= {c, *g["members"]} for c, g in out.items()): e.append("known merge missing: Velindre NHS Trust (NHS and ONS records)")
    return e


def main():
    out, R = build()
    if "--negative" in sys.argv:
        caught = []
        o = copy.deepcopy(out); c = next(iter(o)); o[c]["members"].append(next(k for k in R if k not in o and all(k not in g["members"] for g in o.values()))); o[next(k for k in o if k != c)]["members"].append(o[c]["members"][-1]); caught.append(bool(check(o, R)))
        o = copy.deepcopy(out); cit = next(k for k, r in R.items() if r[1] == "Construction Industry Training Board"); ni = next(k for k, r in R.items() if r[1] == "Construction Industry Training Board (NI)"); o[cit] = {"members": [ni], "names": {}, "rules": []}; caught.append(bool(check(o, R)))
        o = copy.deepcopy(out); h = next(c for c, g in o.items() if any("Heiw" in n or "HEIW" in n for n in g["names"].values())); del o[h]; caught.append(bool(check(o, R)))
        o = copy.deepcopy(out); ps = next(k for k, r in R.items() if r[1] == "Police Service of Northern Ireland"); sc = next(k for k, r in R.items() if r[1] == "Police Service of Scotland"); o[ps] = {"members": [sc], "names": {}, "rules": []}; caught.append(bool(check(o, R)))  # nation guard
        if not all(caught): sys.exit(f"same-as negative: {caught.count(False)} not caught")
        print(f"same-as negative: all {len(caught)} breakers caught"); return
    e = check(out, R)
    if e: sys.exit("same-as: " + "; ".join(e))
    extra = sum(len(g["members"]) for g in out.values())
    payload = {"meta": {"rule": __doc__.split("\n\n")[1].strip(), "groups": len(out), "records_folded": extra, "open_records": len(R), "bodies": len(R) - extra,
                        "by_rule": dict(collections.Counter(r.split(" ")[0] for g in out.values() for r in g["rules"]))}, "groups": out}
    (ROOT / "data/same-as.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    print("same-as:", payload["meta"]["groups"], "groups;", extra, "records folded;", payload["meta"]["bodies"], "bodies from", len(R), "open records;", payload["meta"]["by_rule"])


if __name__ == "__main__":
    main()
