"""Checks for the accountability tree. Each check names the defect or risk it guards against.
Run: python3 tools/check.py          -> checks the built data
     python3 tools/check.py --negative -> proves each check fails on a deliberate break"""
import copy, hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / "sources"
BASE = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (S / "opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
REG = {r[0]: r for r in BASE["r"]}
NAME = {k: r[1] for k, r in REG.items()}
PERSON = re.compile(r"^(?:mr|mrs|ms|miss|dr|sir|dame|lady|professor|prof)\b|^lord\s+(?!chancellor|advocate|president|privy|high|lieutenant|chief)", re.I)  # D-OG4: offices such as "Lord Chancellor" are not persons
CORP = re.compile(r"\b(limited|limted|ltd|plc|llp|lp|group|holdings|ventures|enterprises|capital|partners|fund|investments|infrastructure|company|co|museum|gallery|trust|commission|society|foundation|college|library|school|hospital|institute|centre|council)\b", re.I)  # D-OG13: institutions named after people
def is_person(n): return bool(PERSON.match(n or "")) and not CORP.search(n or "")  # D-OG5: companies named after people stay visible; bare names are withheld
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
FILES = {"eao": "eao2026.xml", "wgao": "wga-order-2026.xml", "ons": "pscgnov2026.xlsx", "pbd": "pbd2324.xlsx", "govuk": "govuk-organisations.json",
         "gleif": "gleif-level2.json", "ch": "companies-house-psc.json", "eao-ni": "ni-eao-2026.xml", "pfi": "pfi-2025.ods", "tf": "tf-feed.xml"}

def c_provenance(T):
    """R-1: every edge names a known source and the row or part it came from (lineage to the authoritative record)."""
    return [e for e in T["edges"] if e["src"] not in T["sources"] or not e.get("ref") or not e.get("how")]
def c_ends(T):
    """R-2: both ends of every edge are register records; nothing invented."""
    return [e for e in T["edges"] if e["c"] not in REG or (e["p"] and e["p"] not in REG)]
def c_no_persons(T):
    """R-3 / standing rule: no personal names. Natural persons with significant control are counted, never named."""
    blob = json.dumps({k: T[k] for k in ("edges", "unresolved", "ppp")}, ensure_ascii=False)
    hits = [e["pt"] for e in T["edges"] if is_person(e.get("pt"))] + [u["text"] for u in T["unresolved"] if is_person(u["text"])]
    for p in T["ppp"]:
        hits += [h for h, _ in p["equity"] if is_person(h)]
    hits += re.findall(r"overall_(?:chair|accounting_officer|senior_sponsor)\w*", blob)
    return hits
def c_no_email(T):
    """Standing rule: contact by form only; no email address in any published file."""
    return EMAIL.findall(json.dumps(T, ensure_ascii=False))
def c_chain_shape(T):
    """R-4: chains are acyclic, each step follows an edge that exists, and each ends at its stated root."""
    keys = {(e["c"], e["p"], e["rel"], e["src"]) for e in T["edges"]}; bad = []
    for k, c in T["chains"].items():
        seen, cur = {k}, k
        for s in c["path"]:
            if s["from"] != cur or s["to"] in seen or (s["from"], s["to"], s["rel"], s["src"]) not in keys: bad.append(k); break
            seen.add(s["to"]); cur = s["to"]
        else:
            if cur != c["root"]: bad.append(k)
    return bad
def c_coverage(T):
    """R-5: every open register record has a chain, so a body with no evidence shows as a gap, never as missing."""
    return [k for k, r in REG.items() if r[4] and k not in T["chains"]]
def c_hashes(T):
    """R-6: the source fingerprints in the tree match the files on disk (audit trail cannot drift from the evidence)."""
    # D-OG10: files the repository doesn't redistribute (they name people) are checked whenever present; absent, they must be declared
    NR = {"pbd", "pfi", "ch", "eao-ni"}  # D-OG11: see fetch.py
    return [k for k, f in FILES.items() if ((S / f).exists() and T["sources"].get(k, {}).get("sha256") != hashlib.sha256((S / f).read_bytes()).hexdigest()) or (not (S / f).exists() and k not in NR)]
def c_known_answers(T):
    """R-7: chains I can verify independently against the Estimates and Accounts Order and the Public Bodies Directory."""
    want = {"environment-agency": "department-for-environment-food-rural-affairs", "driver-and-vehicle-licensing-agency": "department-for-transport",
            "met-office": "department-for-science-innovation-and-technology", "nhs-england": "department-of-health-and-social-care"}
    slug = {r[10].get("govuk_slug"): k for k, r in REG.items()}
    return [s for s, root in want.items() if T["chains"].get(slug[s], {}).get("root") != slug[root]]
def c_nmd_terminal(T):
    """D-OG3: a non-ministerial department answers to Parliament itself; its chain must not climb into a ministry."""
    return [k for k, c in T["chains"].items() if REG[k][3] == "Non-ministerial department" and c["path"]]
def c_unresolved_reason(T):
    """R-8: nothing unmatched is dropped silently; every queue entry says why and where it came from."""
    return [u for u in T["unresolved"] if not (u.get("why") and u.get("ref") and u.get("src"))]
def c_wording(T):
    """Standing rule: the former office name never appears; it is the Government Data Directorate."""
    return re.findall(r"Office of the Chief Data Officer", json.dumps(T))
def c_digest(T):
    """R-9: the published digest matches the content, so a consumer can prove the file is unaltered."""
    d = hashlib.sha256(json.dumps({k: T[k] for k in ("edges", "chains", "conflicts", "unresolved", "ppp")}, sort_keys=True).encode()).hexdigest()
    return [] if d == T["digest"] else ["digest mismatch"]
def c_person_rule_offices(T):
    """D-OG4: the person filter must not treat offices of state (Lord Chancellor, Lord Advocate) as people, and must still catch people."""
    offices = ["Lord Chancellor's Department", "Lord Advocate", "Lord President of the Council"]; people = ["Mr A Example", "Lord Example", "Dame B Example", "Sir C Example"]; firms = ["Sir Robert McAlpine Enterprises Limited", "Sir John Soane's Museum"]
    return [o for o in offices + firms if is_person(o)] + [p for p in people if not is_person(p)]
CHECKS = [c_person_rule_offices, c_provenance, c_ends, c_no_persons, c_no_email, c_chain_shape, c_coverage, c_hashes, c_known_answers, c_nmd_terminal, c_unresolved_reason, c_wording, c_digest]

PREC = {"eao": 0, "eao-ni": 0, "pbd": 1, "ons": 2, "govuk": 3, "ch": 4, "gleif": 4}
DECIDED = {d["id"] for d in json.loads((ROOT / "sources/evidence/reconciliation-decisions.json").read_text())["chains"]}
def c_conflicts_triangulated(T):
    """OG-D33: every disagreement is either contested or resolved for a stated reason that re-checks independently."""
    bad = []; up = lambda x: {st["to"] for st in T["chains"].get(x, {}).get("path", [])}
    for c in T["conflicts"]:
        st, why, ch = c.get("status"), c.get("reason", ""), c.get("chosen")
        if st not in ("resolved", "contested") or not why: bad.append(c["id"]); continue
        if st != "resolved": continue
        cv = next((v for v in c["views"] if v["parent"] == ch), None); alts = [v for v in c["views"] if v is not cv]
        if why.startswith("rule:"):
            ok = cv and min(PREC[x] for x in cv["sources"]) < min(PREC[x] for v in alts for x in v["sources"]) and len(cv["sources"]) >= max(len(v["sources"]) for v in alts)
        elif why.startswith(("nested", "joint")):
            ok = cv and all(v["parent"] in up(ch) or ch in up(v["parent"]) or set(v["sources"]) & set(cv["sources"]) for v in alts)
        elif why.startswith("decided from evidence:"):  # decided by a person: must cite evidence and keep to a parent a source gave, or none
            ok = bool(c.get("decided")) and (ch is None or ch in {v["parent"] for v in c["views"]}) and c["id"] in DECIDED
        elif why.startswith("rule D-OG3"):
            ok = REG[c["id"]][3] == "Non-ministerial department" or not T["chains"].get(c["id"], {}).get("path")
        else: ok = False
        if not ok: bad.append(c["id"])
    return bad
CHECKS.append(c_conflicts_triangulated)

ONSCODE = re.compile(r"^[A-Z][A-Z0-9:&]{0,7}$")
def c_ons_codes(T):
    """OG-D37: an ONS sponsor written as a code resolves only through the guide's abbreviation list (SE had matched Sport England)"""
    bad = [e["c"] for e in T["edges"] if e["src"] == "ons" and e["rel"] == "sponsors" and ONSCODE.match(e["pt"].strip()) and not e["how"].split("sponsor: ")[-1].startswith("ONS abbreviation")]
    sw = next(k for k, r in REG.items() if r[1] == "Scottish Water")
    if NAME.get(T["chains"][sw]["root"]) != "The Scottish Government": bad.append(sw)
    return bad
CHECKS.append(c_ons_codes)

def breakers(T):
    """One deliberate break per check. Each must make exactly its check fail."""
    k0 = next(iter(T["chains"])); e0 = T["edges"][0]
    nmd = next(k for k in T["chains"] if REG[k][3] == "Non-ministerial department")
    def b(f):
        t = copy.deepcopy(T); f(t); return t
    return {
        "c_person_rule_offices": None,
        "c_provenance": b(lambda t: t["edges"][0].update(ref="")),
        "c_ends": b(lambda t: t["edges"][0].update(p="invented:1")),
        "c_no_persons": b(lambda t: t["edges"][0].update(pt="Mr Example Person")),
        "c_no_email": b(lambda t: t["unresolved"][0].update(text="someone@example.org")),
        "c_chain_shape": b(lambda t: t["chains"][next(k for k, c in t["chains"].items() if c["path"])]["path"][0].update(rel="invented")),
        "c_coverage": b(lambda t: t["chains"].pop(k0)),
        "c_hashes": b(lambda t: t["sources"]["eao"].update(sha256="0" * 64)),
        "c_known_answers": b(lambda t: t["chains"][next(k for k, r in REG.items() if r[10].get("govuk_slug") == "met-office")].update(root=e0["c"])),
        "c_nmd_terminal": b(lambda t: t["chains"][nmd]["path"].append({"from": nmd, "to": e0["p"], "rel": "parent", "src": "govuk", "ref": "x"})),
        "c_unresolved_reason": b(lambda t: t["unresolved"][0].update(why="")),
        "c_wording": b(lambda t: t["edges"][0].update(how="Office of the Chief Data Officer")),
        "c_digest": b(lambda t: t["conflicts"].append({"id": k0, "views": []})),
        "c_ons_codes": b(lambda t: next(e for e in t["edges"] if e["pt"] == "SE").update(how="body: name, cleaned; sponsor: name, cleaned")),
        "c_conflicts_triangulated": b(lambda t: next(c for c in t["conflicts"] if c["status"] == "contested" or c.get("decided")).update(status="resolved", reason="decided from evidence: none", decided=[])),
    }

def run(T, quiet=False):
    fails = {}
    for c in CHECKS:
        r = c(T)
        if r: fails[c.__name__] = r
        if not quiet: print(("FAIL " if r else "pass ") + c.__name__ + " — " + c.__doc__.split(":")[0] + (f"  ({len(r)}: {str(r[:3])[:160]})" if r else ""))
    return fails

if __name__ == "__main__":
    T = json.loads((ROOT / "data" / "tree.json").read_text())
    if "--negative" in sys.argv:
        ok = True
        for name, broken in breakers(T).items():
            if broken is None:  # a rule self-test: break the rule itself and confirm the test notices
                keep = PERSON; PERSON = re.compile(r"^(mr|lord)\b", re.I); caught = bool(c_person_rule_offices(T)); PERSON = keep
                ok &= caught; print(("caught " if caught else "MISSED ") + name); continue
            f = run(broken, quiet=True)
            caught = name in f
            ok &= caught
            print(("caught " if caught else "MISSED ") + name + ("" if caught else "  <- check does not fail when it should"))
        sys.exit(0 if ok else 1)
    sys.exit(1 if run(T) else 0)
