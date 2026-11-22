"""Interactive org charts of every body in its context, four ways round:
  answers   who answers to whom: each open body under its first accountable parent (data/tree.json chains), grouped by
            the elected body it answers to in the end;
  nations   nation or territory, then branch of the state, then the grouping on the nations page, then bodies;
  types     type of body, then purpose, then bodies (classification is modelled);
  world     the UK in the world: domain, then each membership, then the UK body that leads it.
Writes docs/orgchart.html (shared shell) with the data inline. Same-as duplicates are shown once.
--negative proves the checks fail when they should."""
import collections, copy, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import design  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANS = {"Parliament, through the Secretary of State or minister in charge": "UK Parliament", "Parliament, through its sponsoring minister": "UK Parliament",
       "Parliament directly (not a ministerial body)": "UK Parliament", "the Scottish Parliament": "Scottish Parliament", "the Senedd": "Senedd Cymru",
       "the Northern Ireland Assembly": "Northern Ireland Assembly", "local government (a council or group of councils)": "Local government",
       "its elected council": "Local government", "NHS governance in its nation": "The NHS", "not established from the sources": "Not yet established from the sources"}
BRANCH = {"legislature": "Law-makers", "executive": "Government and public bodies", "judiciary": "Courts and tribunals"}


def load():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    T = json.loads((ROOT / "data/tree.json").read_text()); CL = json.loads((ROOT / "data/classification.json").read_text())
    SA = json.loads((ROOT / "data/same-as.json").read_text())["groups"]; N = json.loads((ROOT / "data/nations.json").read_text())
    REL = json.loads((ROOT / "data/relations.json").read_text()); NAT = json.loads((ROOT / "data/body-nations.json").read_text())
    return D, T, CL, SA, N, REL, NAT


class Tree:
    """Flat node list: [label, parent index, body id or '', type key, nations]; index 0 is the root."""
    def __init__(self, root): self.n = [[root, -1, "", "group", ""]]; self.key = {}
    def group(self, path):
        p = 0
        for i, lab in enumerate(path):
            k = tuple(path[:i + 1])
            if k not in self.key: self.key[k] = len(self.n); self.n.append([lab, p, "", "group", ""])
            p = self.key[k]
        return p
    def body(self, parent, bid, name, t, nat): self.n.append([name, parent, bid, t, nat]); return len(self.n) - 1


def build():
    D, T, CL, SA, N, REL, NAT = load()
    folded = {m for g in SA.values() for m in g["members"]}
    R = {r[0]: r for r in D["r"]}; opn = [r[0] for r in D["r"] if r[4] and r[0] not in folded]
    bt = lambda i: CL["bodies"].get(i, {}).get("btype", "central"); nat = lambda i: ",".join(NAT.get(i) or [])
    views = {}
    # 1 accountability
    a = Tree("The UK state: who answers to whom"); idx = {}
    for i in opn:  # place parents before children by walking each chain from the top
        c = T["chains"].get(i) or {}
        top = ANS.get(c.get("answerable", ""), "Not yet established from the sources")
        path = [i] + [s["to"] for s in c.get("path", [])]
        path = [x for x in path if x not in folded]
        g = a.group([top])
        for b in reversed(path):
            if b in idx: g = idx[b]; continue
            if b not in R: break
            idx[b] = a.body(g, b, R[b][1] + ("" if R[b][4] else " (closed)"), bt(b), nat(b)); g = idx[b]
    views["answers"] = a.n
    # 2 nations and branches (includes the territories' own bodies)
    t2 = Tree("The UK state by nation and branch")
    for code, nn in N["nations"].items():
        for br, tiers in nn["branches"].items():
            for tier, items in tiers.items():
                g = t2.group([nn["name"], BRANCH.get(br, br), tier])
                for x in items:
                    if x["id"] in folded: continue
                    t2.body(g, x["id"] if x["id"] in R else "", x["name"], bt(x["id"]) if x["id"] in R else ("territory" if code in ("OT", "CD") else "central"), code)
    views["nations"] = t2.n
    # 3 type and purpose
    t3 = Tree("The UK state by type and purpose"); lab = lambda f, k: next((x["label"] for x in CL["meta"][f] if x["key"] == k), k)
    for i in sorted(opn, key=lambda i: R[i][1].lower()):
        c = CL["bodies"].get(i, {})
        t3.body(t3.group([lab("btypes", c.get("btype", "central")), lab("purposes", c.get("purpose", "unknown"))]), i, R[i][1], bt(i), nat(i))
    views["types"] = t3.n
    # 4 the UK in the world
    t4 = Tree("The UK in the world")
    for m in sorted(REL["memberships"], key=lambda m: (m["domain"], m["name"])):
        g = t4.group([REL["domains"].get(m["domain"], "Other"), ("Former: " if m["status"] == "former" else "") + m["name"] + ("" if m["who"] == "UK" else f" ({m['who']})")])
        for ld in m["lead"]: t4.body(g, ld, R[ld][1] if ld in R else ld, bt(ld), nat(ld))
    views["world"] = t4.n
    return views, R, opn, folded


def check(views, R, opn, folded):
    e = []
    for k, ns in views.items():
        for j, n in enumerate(ns[1:], 1):
            if not 0 <= n[1] < j: e.append(f"{k}: node {j} has a parent after it or none"); break
        if any(n[2] and n[2] not in R for n in ns): e.append(f"{k}: a node points at an unknown body")
    placed = {n[2] for n in views["answers"]}
    miss = [i for i in opn if i not in placed]
    if miss: e.append(f"answers: {len(miss)} open bodies not placed")
    if any(n[2] in folded for v in views.values() for n in v): e.append("a combined duplicate is shown separately")
    byname = {n[0]: (j, n) for j, n in enumerate(views["answers"])}
    hmt = byname.get("HM Treasury"); dmo = byname.get("UK Debt Management Office")
    if not hmt or not dmo or views["answers"][dmo[0]][1] != hmt[0]: e.append("known answer wrong: UK Debt Management Office should sit under HM Treasury")
    return e


PAGE = (ROOT / "tools/orgchart-page.html")


def main():
    views, R, opn, folded = build()
    if "--negative" in sys.argv:
        cases = []
        v = copy.deepcopy(views); v["answers"][5][1] = 999999; cases.append(v)
        v = copy.deepcopy(views); v["answers"] = [n for n in v["answers"] if n[2] != opn[0]] ; cases.append(v)
        v = copy.deepcopy(views); v["types"][3][2] = "government-organisation:NOPE"; cases.append(v)
        if not all(check(c, R, opn, folded) for c in cases): sys.exit("orgchart negative: a breaker was not caught")
        print(f"orgchart negative: all {len(cases)} breakers caught"); return
    e = check(views, R, opn, folded)
    if e: sys.exit("orgchart: " + "; ".join(e))
    data = json.dumps({"views": views}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (ROOT / "docs/orgchart.html").write_text(design.wrap_page(PAGE.read_text(), "orgchart").replace("__DATA__", data))
    print("orgchart:", {k: len(v) for k, v in views.items()}, "nodes;", collections.Counter(n[3] for n in views["answers"]).most_common(4))


if __name__ == "__main__":
    main()
