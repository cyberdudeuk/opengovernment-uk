"""Checks on the trends, the 2020 reconciliation and the 2030 scenarios. --negative proves each check fails on a deliberate break."""
import copy, csv, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scenarios  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]; DATA = ROOT / "data"
PERSON = re.compile(r"^(mr|mrs|ms|miss|dr|sir|dame|professor)\s", re.I)
INSTITUTION = re.compile(r"\b(museum|gallery|trust|commission|society|foundation|college|library|school|hospital|institute|centre|council)\b", re.I)  # D-OG13: "Sir John Soane's Museum" is a body, not a person

def t_units(T):
    """Every edition records its money unit evidence and financial year; the uncertain-year edition stays out of the money series."""
    return [e for e, s in T["editions"].items() if not s.get("unit_evidence") or not re.fullmatch(r"\d{4}-\d{2}", s.get("financial_year", ""))] + ([] if T["editions"]["2015"]["money_series"] is False else ["2015 in money series"])
def t_no_persons(T, R, S):
    """No personal name or personal field anywhere in the outputs (chairs, accounting officers, sponsors are never read)."""
    # D-OG12: body names may contain "Chair" (Law Commission, with the exception of the Chair), so field names are checked, not body names
    keys = set()
    def walk(o):
        if isinstance(o, dict): keys.update(o); [walk(v) for v in o.values()]
        elif isinstance(o, list): [walk(v) for v in o]
    walk(T); walk(S); keys.update(R[0] if R else {})
    return [k for k in keys if re.search(r"chair|accounting|officer|sponsor_name|senior|remunerat|email|phone|address", str(k), re.I)] + [r["name_2020"] for r in R if PERSON.match(r["name_2020"]) and not INSTITUTION.search(r["name_2020"])]
def t_reconciled(R):
    """The 2020 baseline is fully accounted for: 244 rows, every replaced row names a successor, current means open in today's register."""
    bad = [] if len(R) == 244 else [f"rows {len(R)}"]
    bad += [r["name_2020"] for r in R if r["verdict"].startswith("replaced") and not r["verdict"].split(":", 1)[1].strip()]
    bad += [r["name_2020"] for r in R if r["verdict"] == "current" and r["register_status"] != "open"]
    return bad
def t_scenarios(S):
    """Scenarios recompute exactly from their assumptions, entries fall from evolution to revolution, and no lens releases more than the base."""
    fresh = scenarios.run(); L = S["lenses"]
    bad = [] if json.dumps(fresh, sort_keys=True) == json.dumps(S, sort_keys=True) else ["stored scenarios differ from recomputation"]
    if not (L["evolution"]["entries_2030"] > L["reform"]["entries_2030"] > L["revolution"]["entries_2030"]): bad.append("order of lenses")
    bad += [k for k, v in L.items() if v["admin_released_share"] > 1 or v["admin_released_share"] < 0]
    return bad

def load():
    return (json.loads((DATA / "public-bodies-trends.json").read_text()), list(csv.DictReader(open(DATA / "reconciliation-2020.csv"))), json.loads((DATA / "scenarios-2030.json").read_text()))
def run(T, R, S):
    res = {"t_units": t_units(T), "t_no_persons": t_no_persons(T, R, S), "t_reconciled": t_reconciled(R), "t_scenarios": t_scenarios(S)}
    return {k: v for k, v in res.items() if v}

if __name__ == "__main__":
    T, R, S = load()
    if "--negative" not in sys.argv:
        f = run(T, R, S); [print(("FAIL " if k in f else "pass ") + k) for k in ("t_units", "t_no_persons", "t_reconciled", "t_scenarios")]; sys.exit(1 if f else 0)
    breaks = {
        "t_units": lambda T, R, S: T["editions"]["2015"].update(money_series=True),
        "t_no_persons": lambda T, R, S: (R[0].update(name_2020="Dr Example Person"), T["editions"]["2020"].update(chair_remuneration=1)),
        "t_reconciled": lambda T, R, S: R.pop(),
        "t_scenarios": lambda T, R, S: S["lenses"]["reform"].update(entries_2030=999),
    }
    ok = True
    for name, brk in breaks.items():
        t, r, s = copy.deepcopy(T), copy.deepcopy(R), copy.deepcopy(S); brk(t, r, s); caught = name in run(t, r, s); ok &= caught
        print(("caught " if caught else "MISSED ") + name)
    sys.exit(0 if ok else 1)
