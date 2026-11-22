"""The UK in international bodies: which UK public body holds each relationship or is its single point of contact.
Reads sources/evidence/international-bodies.json (every row cites an official page), resolves each lead to its open
register record and writes data/international.json for the nations page. Roles only: no personal names.
--negative proves the checks fail when they should."""
import collections, copy, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OFFICIAL = re.compile(r"^https://([a-z0-9-]+\.)*(gov\.uk|parliament\.uk|legislation\.gov\.uk|caa\.co\.uk|metoffice\.gov\.uk|nationalcrimeagency\.gov\.uk|interpol\.int|publishing\.service\.gov\.uk)/")
PERSON = re.compile(r"\b(Rt Hon|MP\b|Sir |Dame |Baroness |Lord [A-Z]|Mr |Mrs |Ms |Dr [A-Z])")


def load():
    E = json.loads((ROOT / "sources/evidence/international-bodies.json").read_text())
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    return E, {r[0]: r for r in D["r"]}


def check(E, R):
    e = []
    for b in E["bodies"]:
        if b["group"] not in E["groups"]: e.append(f"{b['name']}: unknown group")
        if not b.get("evidence") or not all(OFFICIAL.match(x["url"]) for x in b["evidence"]): e.append(f"{b['name']}: evidence missing or not from an official site")
        for i in b["lead"]:
            if i not in R or not R[i][4]: e.append(f"{b['name']}: lead {i} is not an open register record")
        if PERSON.search(json.dumps(b, ensure_ascii=False)): e.append(f"{b['name']}: names a person (roles only)")
    names = [b["name"] for b in E["bodies"]]
    if len(names) != len(set(names)): e.append("a body is listed twice")
    known = {"INTERPOL": "government-organisation:PB558", "NATO": "government-organisation:D17", "International Monetary Fund": "government-organisation:D15", "World Meteorological Organization (WMO)": "government-organisation:EA46"}
    for n, lead in known.items():
        b = next((x for x in E["bodies"] if x["name"] == n), None)
        if not b or lead not in b["lead"]: e.append(f"known answer wrong: {n}")
    return e


def main():
    E, R = load()
    if "--negative" in sys.argv:
        cases = []
        x = copy.deepcopy(E); x["bodies"][0]["evidence"][0]["url"] = "https://example.com/x"; cases.append(x)
        x = copy.deepcopy(E); x["bodies"][0]["role"] += " Rt Hon Somebody MP leads it."; cases.append(x)
        x = copy.deepcopy(E); x["bodies"][0]["lead"] = ["government-organisation:D1382"]; cases.append(x)  # closed department
        x = copy.deepcopy(E); next(b for b in x["bodies"] if b["name"] == "INTERPOL")["lead"] = ["government-organisation:D1315"]; cases.append(x)
        if not all(check(c, R) for c in cases): sys.exit("international negative: a breaker was not caught")
        print(f"international negative: all {len(cases)} breakers caught"); return
    e = check(E, R)
    if e: sys.exit("international: " + "; ".join(e))
    out = {"read": E["read"], "groups": E["groups"], "to_confirm": E["to_confirm"],
           "bodies": [dict(b, lead=[{"id": i, "name": R[i][1]} for i in b["lead"]]) for b in E["bodies"]]}
    (ROOT / "data/international.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    c = collections.Counter(ld["name"] for b in out["bodies"] for ld in b["lead"])
    print("international:", len(out["bodies"]), "bodies;", dict(c.most_common()))


if __name__ == "__main__":
    main()
