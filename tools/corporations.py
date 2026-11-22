"""Trading funds and public corporations, each as its own family tree, consolidated and grouped.

Members: every open body that is a trading fund (trading fund orders on legislation.gov.uk and the ONS guide's notes)
or that ONS classifies as a public corporation (non-financial, financial, or the central bank).

Consolidation rule (one place per body):
  family parent = the first body on its accountability chain that is itself a member; failing that, a member that
  owns or controls it by a recorded edge (ONS parent company first, then Companies House, then GLEIF).
  A member with no family parent starts its own tree. Every member therefore appears exactly once.
Each tree also shows, under each member, the other bodies recorded as answering to it (any relation), and above it
the chain up to its accountable owner. Trees are grouped by the level of government that owns them.

Writes data/corporations.json. --negative proves the checks fail when broken."""
import collections, copy, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEPTH = 8  # deeper than any recorded family; reaching it is reported, never silent

SECTOR = [  # ONS sector text -> plain kind
    (re.compile(r"^Central Bank$"), "central-bank"),
    (re.compile(r"^Public Non-Financial", re.I), "non-financial"),
    (re.compile(r"^Public ", re.I), "financial"),
]
KINDS = {
    "trading-fund": ("Trading fund", "A government operation that pays its way from what it charges, under the Government Trading Funds Act 1973. It still answers to a minister."),
    "non-financial": ("Public company or trading body", "Owned or controlled by government and sells goods or services, like a business (ONS: public non-financial corporation)."),
    "financial": ("Public financial body", "Owned or controlled by government and lends, invests, insures or handles money (ONS: public financial corporation)."),
    "central-bank": ("Central bank", "The Bank of England and the bodies ONS counts with it."),
}
LEVELS = {
    "uk": "UK government", "SC": "Scottish Government", "WA": "Welsh Government", "NI": "Northern Ireland Executive",
    "local": "Local government", "other": "Other or not yet established",
}
COUNCIL_T = re.compile(r"council|borough|authority|unitary|district|county|combined", re.I)


def load():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    T = json.loads((ROOT / "data/tree.json").read_text())
    nat = json.loads((ROOT / "data/body-nations.json").read_text())
    cls = json.loads((ROOT / "data/classification.json").read_text())["bodies"]
    return D, T, nat, cls


def kind_of(sector):
    for rx, k in SECTOR:
        if sector and rx.search(sector) and "Pension" not in sector: return k
    return None


ANSWERS = [(re.compile(r"Scottish Parliament"), "SC"), (re.compile(r"Senedd"), "WA"), (re.compile(r"Northern Ireland Assembly"), "NI"),
           (re.compile(r"local government|elected council"), "local"), (re.compile(r"^Parliament"), "uk")]


def level_of(root, R, nat, answerable):
    """Which level of government owns the tree: from the owner's kind, else from what the chain says it answers to."""
    r = R.get(root)
    if r:
        t = r[3] or ""; n = nat.get(root) or []
        if t in ("Ministerial department", "Non-ministerial department"):
            return n[0] if t == "Non-ministerial department" and len(n) == 1 and n[0] in ("SC", "WA", "NI") else "uk"
        if t in ("Devolved government", "Executive office"):
            return n[0] if len(n) == 1 and n[0] in ("SC", "WA", "NI") else "other"
        if COUNCIL_T.search(t) or re.search(r"\bcouncil\b|greater london authority", r[1], re.I): return "local"
    for rx, lv in ANSWERS:
        if answerable and rx.search(answerable): return lv
    return "other"


def build():
    D, T, nat, cls = load()
    R = {r[0]: r for r in D["r"]}
    CH = T["chains"]
    tf = {i for i in T["stats"]["trading_funds"] if i in R and R[i][4]}
    pcs = {k: kind_of(v["ons"]["sector"].replace("\n", " ")) for k, v in CH.items() if v.get("ons") and kind_of(v["ons"]["sector"].replace("\n", " ")) and k in R and R[k][4]}
    M = tf | set(pcs)
    kids = collections.defaultdict(set)
    owners = collections.defaultdict(list)
    ORDER = {("owns", "ons"): 0, ("owns", "ch"): 1, ("owns", "gleif"): 2, ("controls", "ons"): 3}
    for e in T["edges"]:
        if e["p"] and e["c"] != e["p"] and e["c"] in R and R[e["c"]][4]:
            kids[e["p"]].add(e["c"])
            if e["c"] in M and e["p"] in M and (e["rel"], e["src"]) in ORDER: owners[e["c"]].append((ORDER[(e["rel"], e["src"])], e["p"]))
    fam = {}
    for m in sorted(M):
        hop = next((s["to"] for s in (CH.get(m) or {}).get("path", []) if s["to"] in M and s["to"] != m), None)
        if not hop and owners[m]: hop = min(owners[m])[1]
        if hop: fam[m] = hop
    # break any cycle deterministically: the member with the smallest id in a loop becomes a tree top
    for m in sorted(fam):
        seen, cur = [], m
        while cur in fam and cur not in seen: seen.append(cur); cur = fam[cur]
        if cur in seen: fam.pop(min(seen[seen.index(cur):]), None)
    famkids = collections.defaultdict(list)
    for c, p in fam.items(): famkids[p].append(c)

    def label(i): return R[i][1] if i in R else i

    truncated = []

    def node(i, depth, path):
        ks = "trading-fund" if i in tf else pcs.get(i)
        n = {"id": i, "name": label(i), "member": i in M}
        if ks: n["kind"] = ks
        if i in tf and pcs.get(i): n["also"] = pcs[i]
        if i in tf: n["tf"] = True
        c = cls.get(i) or {}
        if c.get("purpose"): n["purpose"] = c["purpose"]
        if nat.get(i): n["nat"] = nat[i]
        if depth >= DEPTH: truncated.append(i); return n
        sub = sorted(famkids.get(i, []), key=label)
        others = sorted((k for k in kids.get(i, ()) if k not in M and k not in path), key=label)
        ch = [node(k, depth + 1, path | {k}) for k in sub] + [node(k, depth + 1, path | {k}) for k in others]
        if ch: n["children"] = ch
        return n

    trees = []
    for m in sorted((m for m in M if m not in fam), key=label):
        c = CH.get(m) or {}
        up = [s["to"] for s in c.get("path", [])]
        root = c.get("root") or (up[-1] if up else None)
        t = node(m, 0, {m})
        t["owner"] = root if root and root != m else None
        t["owner_name"] = label(root) if root and root != m else None
        t["owner_open"] = bool(R[root][4]) if root in R else None
        t["owner_successor"] = [label(s) for s in (R[root][16] or [])] if root in R and not R[root][4] and R[root][16] else []
        t["up"] = [u for u in up if u != m]
        t["answerable"] = c.get("answerable")
        t["level"] = level_of(root if root != m else None, R, nat, c.get("answerable"))
        trees.append(t)

    def count(n): return (1 if n["member"] else 0) + sum(count(k) for k in n.get("children", []))

    def size(n): return 1 + sum(size(k) for k in n.get("children", []))
    for t in trees: t["members"] = count(t); t["size"] = size(t)
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, t in enumerate(trees): groups[t["level"]][t["owner_name"] or ("Owner not named in the sources" if t["level"] != "other" else "Owner not yet established")].append(i)
    out = {
        "meta": {"built": T["built"], "rule": __doc__.split("\n\n")[1].strip(), "kinds": KINDS, "levels": LEVELS,
                 "counts": {"members": len(M), "trading_funds": len(tf), "public_corporations": len(pcs), "both": len(tf & set(pcs)),
                            "trees": len(trees), "consolidated": len(fam), "truncated": len(truncated)},
                 "sources": ["data/tree.json (trading fund orders on legislation.gov.uk; ONS public sector classification guide)", "data/classification.json (purpose: MODELLED)", "data/body-nations.json"]},
        "trees": trees,
        "groups": {lv: dict(sorted(g.items(), key=lambda kv: (-sum(trees[i]["members"] for i in kv[1]), kv[0]))) for lv, g in groups.items()},
    }
    return out, M


def members_once(out):
    seen = collections.Counter()

    def walk(n):
        if n["member"]: seen[n["id"]] += 1
        for k in n.get("children", []): walk(k)
    for t in out["trees"]: walk(t)
    return seen


def check(out, M):
    errs = []
    seen = members_once(out)
    dup = [k for k, v in seen.items() if v > 1]; miss = sorted(M - set(seen))
    if dup: errs.append(f"members in more than one place: {dup[:5]}")
    if miss: errs.append(f"members missing from every tree: {miss[:5]}")
    if out["meta"]["counts"]["truncated"]: errs.append("a tree reached the depth limit")
    ids = [i for g in out["groups"].values() for v in g.values() for i in v]
    if sorted(ids) != list(range(len(out["trees"]))): errs.append("groups do not hold every tree exactly once")
    by = {t["name"]: t for t in out["trees"]}

    def find(name):
        stack = list(out["trees"])
        while stack:
            n = stack.pop()
            if n["name"] == name: return n
            stack += n.get("children", [])
        return None
    known = [  # (body, test, why)
        ("Manchester Airport Holdings Limited", lambda n: n and n.get("members", 0) >= 20, "its airport companies consolidate under it"),
        ("Ordnance Survey", lambda n: n and n.get("tf") and n.get("also") == "non-financial", "both a trading fund and a public corporation, shown once"),
        ("Royal Mint", lambda n: n and n.get("tf"), "a trading fund"),
        ("Met Office", lambda n: n and n.get("tf") and len(n.get("children", [])) >= 1, "a trading fund with bodies under it"),
        ("Scottish Water", lambda n: n and by.get("Scottish Water", {}).get("level") == "SC", "owned by the Scottish Government"),
        ("Forestry England", lambda n: n and by.get("Forestry England", {}).get("level") == "uk", "under the Forestry Commission, a UK non-ministerial department"),
    ]
    tfl = [t for t in out["trees"] if t["owner_name"] == "Transport for London"]
    if not tfl or any(t["level"] != "local" for t in tfl): errs.append("known answer wrong: trees owned by Transport for London are local government")
    for name, ok, why in known:
        n = find(name)
        if n is None: errs.append(f"known answer not found: {name}")
        elif not ok(n): errs.append(f"known answer wrong: {name} ({why})")
    return errs


def main():
    out, M = build()
    errs = check(out, M)
    if "--negative" in sys.argv:
        caught = []
        o = copy.deepcopy(out); o["trees"].append(copy.deepcopy(o["trees"][0])); caught.append(bool(check(o, M)))  # duplicate a tree
        o = copy.deepcopy(out); o["trees"] = o["trees"][1:]; caught.append(bool(check(o, M)))  # drop a tree
        o = copy.deepcopy(out); t = next(t for t in o["trees"] if t["name"] == "Scottish Water"); t["level"] = "uk"; caught.append(bool(check(o, M)))  # wrong owner level
        o = copy.deepcopy(out); o["meta"]["counts"]["truncated"] = 1; caught.append(bool(check(o, M)))  # depth limit hit
        if not all(caught): sys.exit(f"corporations negative: {caught.count(False)} breaker(s) not caught")
        print(f"corporations negative: all {len(caught)} breakers caught"); return
    if errs: sys.exit("corporations: " + "; ".join(errs))
    (ROOT / "data/corporations.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    c = out["meta"]["counts"]
    print(f"corporations: {c['members']} members ({c['trading_funds']} trading funds, {c['public_corporations']} public corporations, {c['both']} both) "
          f"in {c['trees']} trees; {c['consolidated']} consolidated under a parent")
    print({lv: len(g) for lv, g in out["groups"].items()})


if __name__ == "__main__":
    main()
