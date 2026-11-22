"""Known-answer questions for the agent instructions (agent/SKILL.md), answered from the published files only (docs/)

Each eval names a recipe; the recipe follows the "Where each answer is" table in agent/SKILL.md, reading only what the
site publishes, so an outside agent could do the same. Fails if any answer differs from agent/evals.json. This checks
that the files can answer the questions; it does not run a language model.

  python tools/agent_evals.py             run the evals
  python tools/agent_evals.py --negative  prove a wrong expected answer is caught
"""
import csv, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
_cache = {}


def j(p):
    if p not in _cache: _cache[p] = json.loads((DOCS / p).read_text())
    return _cache[p]


def bods():
    b = j("bods-0.4.json")
    return b, {s["recordId"]: s["recordDetails"] for s in b if s["recordType"] == "entity"}


def accountable_owner(name):
    with open(DOCS / "accountable-owner.csv", newline="") as f:
        return next((r["accountable_owner"] for r in csv.DictReader(f) if r["name"] == name), None)


def controller(subject):
    b, ent = bods()
    for s in b:
        if s["recordType"] == "relationship" and ent.get(s["recordDetails"]["subject"], {}).get("name") == subject:
            return f"{ent[s['recordDetails']['interestedParty']]['name']} by {s['recordDetails']['interests'][0]['type']}"


def uk_votes(institution):
    b, ent = bods()
    for s in b:
        d = s.get("recordDetails", {})
        if s.get("publicAccountability", {}).get("relation") == "member-shareholder" and ent[d["subject"]]["name"] == institution:
            return str(next(i["share"]["exact"] for i in d["interests"] if i["type"] == "votingRights"))


def lei(name):
    _, ent = bods()
    for e in ent.values():
        if e["name"] == name:
            return next((i["id"] for i in e.get("identifiers", []) if i.get("scheme") == "XI-LEI"), None)


def country_node(name):
    return next((i for i in j("data/international.jsonld")["@graph"] if i.get("@type") == "schema:Country" and i.get("schema:name") == name), {})


def trade(country):
    t = country_node(country).get("og:tradeAgreementInEffect") or []
    return t[0]["schema:name"] if t else None


def commonwealth_count():
    return str(sum(1 for i in j("data/international.jsonld")["@graph"] if i.get("@type") == "schema:Country" and i.get("og:commonwealthMember")))


def not_read(source):
    return "not read" if any(g["source"] == source for g in j("data/source-status.json")["not_read"]) else "read"


RECIPES = {f.__name__: f for f in (accountable_owner, controller, uk_votes, lei, trade, commonwealth_count, not_read)}


def run(evals):
    return [f"{e['id']}: got {got!r}, expected {e['expected']!r}" for e in evals if (got := RECIPES[e["recipe"]](**e["args"])) != e["expected"]]


def main():
    ev = json.loads((ROOT / "agent/evals.json").read_text())["evals"]
    if "--negative" in sys.argv:
        bad = [dict(e, expected="Department for Transport") if e["id"] == "met-office-owner" else e for e in ev]
        if not run(bad): sys.exit("agent evals negative: a wrong answer was not caught")
        print("agent evals negative: a wrong expected answer is caught"); return
    bad = run(ev)
    if bad: sys.exit("agent evals: " + "; ".join(bad))
    print(f"agent evals: {len(ev)} of {len(ev)} answered from the published files")


if __name__ == "__main__":
    main()
