"""Which nation(s) each open body belongs to, from trusted sources only, every piece of evidence kept.

Ranked sources (lower rank wins; disagreements are recorded as conflicts, never overwritten).
Governance relationships and the body's own present-tense statement outrank a register's location code, which can be
stale or inferred (OG-D25: Velindre NHS Trust stated as England; Planning Inspectorate stated as Wales).
 1 chain       - the accountability chain ends at a devolved legislature
 2 ons-sponsor - ONS Public Sector Classification Guide sponsoring entity (SG/WG/NIA/NIE/NIO, or a council with a GSS code)
 3 own-site    - the body's own GOV.UK page says where it works ("in England and Wales", "across the UK")
 4 register    - the nation code the owning register states
 5 ons-gss     - the body is a council whose name matches an ONS local authority; nation from the GSS code prefix
 6 statute     - the territorial extent of its founding Act (Wikidata link, extent read from legislation.gov.uk); an upper
                 bound, so never applied to councils, whose general Acts cover Great Britain (OG-D26)
 7 wikidata    - Wikidata "applies to jurisdiction" (P1001), country level only
 8 pb-2020     - the 2020 public bodies compilation (built on the 2019 edition; dated evidence; not redistributed)
 9 companies   - registered in Scotland or Northern Ireland (Companies House number prefix)
Nothing is inferred from a body's name alone. Writes data/nation-evidence.json."""
import collections, csv, html, json, pathlib, re, sys
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[1]; SRC = ROOT / "sources"; EV = SRC / "evidence"
ALL4 = ["EN", "SC", "WA", "NI"]
LABEL = {"United Kingdom": ["UK"], "England": ["EN"], "Wales": ["WA"], "Scotland": ["SC"], "Northern Ireland": ["NI"], "England and Wales": ["EN", "WA"], "Great Britain": ["EN", "WA", "SC"]}
EXTENT = {"E+W+S+N.I.": ["UK"], "E+W+S": ["EN", "WA", "SC"], "E+W": ["EN", "WA"], "E+W+N.I.": ["EN", "WA", "NI"], "E": ["EN"], "W": ["WA"], "S": ["SC"], "N.I.": ["NI"], "E+N.I.": ["EN", "NI"]}
GSS = {"E": "EN", "W": "WA", "S": "SC", "N": "NI"}
LOCAL = {"Local Government", "Non-metropolitan district", "Unitary authority", "Metropolitan district", "London borough", "County council", "Combined authority"}

def clean(s):
    s = html.unescape(str(s or "")).lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s); s = re.sub(r"\b(the|ltd|limited|plc)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# Legal-name forms of councils, matched exactly against ONS local authority names (OG-D28 covered the missing forms).
COUNCIL = re.compile(r"^(london borough of|royal borough of|borough of|city of|county of|city and county of)\s+|\s+(metropolitan district|metropolitan borough|county borough|borough|district|city|county|islands)?\s*council$")
PREFIXES = ("london borough of", "royal borough of", "borough of", "city and county of")
def council_key(name):
    s = clean(name)
    if not s.endswith(" council") and not s.startswith(PREFIXES): return None
    return COUNCIL.sub("", COUNCIL.sub("", s)).strip()

def load():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (SRC / "opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    chains = json.loads((ROOT / "data/tree.json").read_text())["chains"]
    return D, chains

def ons_sponsors(lad):
    ws = openpyxl.load_workbook(SRC / "pscgnov2026.xlsx", read_only=True)["Organisation|Institutional Unit"]
    rows = list(ws.iter_rows(values_only=True)); hi = next(i for i, r in enumerate(rows) if r and r[0] == "Name"); h = rows[hi]
    out = {}
    for r in rows[hi + 1:]:
        if not r or not r[0]: continue
        s = str(r[h.index("Sponsoring Entity")] or "").strip()
        n = None
        if re.match(r"^(SG\b|Scottish Government)", s): n = ["SC"], f"sponsored by the Scottish Government ({s[:40]})"
        elif re.match(r"^(WG\b|Welsh Government|Welsh Local Government Association)", s): n = ["WA"], f"sponsored by {s[:40]}"
        elif re.match(r"^(NIA\b|NIE\b|Northern Ireland Assembly|NIO\b|Northern Ireland Office)", s): n = ["NI"], f"sponsored in Northern Ireland ({s[:40]})"
        elif re.match(r"^(Greater London Authority|Transport for London|TfL|Transport Trading Limited)", s): n = ["EN"], f"sponsored by {s[:40]}, a London body"
        else:
            k = council_key(s) or clean(s)
            if k in lad: n = [lad[k][0]], f"sponsored by {s[:40]} (ONS code {lad[k][1]})"
        if n: out[clean(r[0])] = n
    return out

def lad_index():
    d = json.loads((EV / "ons-lad-dec-2024-uk.json").read_text())
    idx = {}
    for f in d["features"]:
        a = f["attributes"]; k = clean(a["LAD24NM"])
        idx[k] = (GSS[a["LAD24CD"][0]], a["LAD24CD"], a.get("LAD24NMW"))
    idx["na h eileanan siar"] = idx.get("na h eileanan siar") or idx.get(clean("Na h-Eileanan Siar"))
    idx["comhairle nan eilean siar"] = idx["na h eileanan siar"]
    return idx

NAT = r"(?:England|Wales|Scotland|Northern Ireland|Great Britain|United Kingdom|the UK|UK)"
# A list after the preposition is read whole ("in England, Scotland and Wales"): reading only its first item was OG-D27.
SITE = re.compile(r"\b(?:in|for|across|throughout|covering|within)\s+(?:the\s+)?(" + NAT + r"(?:(?:\s*,\s*|\s+and\s+|\s+or\s+)" + NAT + r")*)\b(?!\s*(?:government|Government|'s|’s))")
UKWIDE = re.compile(r"\bUK-wide\b|\bUnited Kingdom-wide\b")
ONE = {"England": ["EN"], "Wales": ["WA"], "Scotland": ["SC"], "Northern Ireland": ["NI"], "Great Britain": ["EN", "WA", "SC"], "United Kingdom": ["UK"], "the UK": ["UK"], "UK": ["UK"]}
def own_site(text):
    found, nat = [], set()
    for m in SITE.finditer(text or ""):
        found.append(m.group(1))
        for part in re.split(r"\s*,\s*|\s+and\s+|\s+or\s+", m.group(1)):
            nat |= set(ONE.get(part.strip(), []))
    if UKWIDE.search(text or ""): found.append("UK-wide"); nat.add("UK")
    if not nat: return None
    if "UK" in nat and len(nat) > 1: return "ambiguous", found
    return sorted(nat), found

def pb2020():
    p = SRC / "evidence" / "pb-nov2020-nonpersonal.tsv"
    if not p.exists(): return {}
    out = {}
    rows = list(csv.reader(p.open(encoding="utf-8"), delimiter="\t"))[1:]
    for r in rows:
        name, cls, dept = r[0], html.unescape(r[2]).strip(), html.unescape(r[6]).strip()
        n = None
        for pat, nn in ((r"Scotland|Scottish", ["SC"]), (r"Wales|Welsh", ["WA"]), (r"Northern Ireland|\bNI\b|Northern Irish", ["NI"]), (r"Local Government - England", ["EN"])):
            if re.search(pat, cls) or re.search(pat, dept):
                if pat.startswith("Local") and not cls.startswith("Local Government - England"): continue
                n = nn; break
        if re.search(r"England and Wales", dept): n = ["EN", "WA"]
        if n: out[clean(name)] = (n, f"{cls or '-'} / {dept or '-'}")
    return out

def resolve():
    D, chains = load(); lad = lad_index(); sp = ons_sponsors(lad); pb = pb2020()
    desc = json.loads((SRC / "govuk-descriptions.json").read_text())
    wd = json.loads((EV / "wikidata-jurisdiction-founding.json").read_text()); ext = json.loads((EV / "legislation-extent.json").read_text())
    wd_j = collections.defaultdict(set)
    for q, _, lbl in wd["jurisdiction"]:
        if lbl in LABEL: wd_j[q].add(lbl)
    wd_f = collections.defaultdict(list)
    for q, _, title, leg, _p in wd["founding"]:
        e = ext.get(leg, {}).get("extent")
        if e in EXTENT: wd_f[q].append((EXTENT[e], f"{ext[leg].get('title') or title} extends to {e}", "https://www.legislation.gov.uk/" + leg))
    out, conflicts = {}, []
    for r in D["r"]:
        if not r[4]: continue
        ids, ans = r[10], (chains.get(r[0]) or {}).get("answerable", "")
        ev = []
        found = [c for c in ("EN", "SC", "WA", "NI", "OT", "CD", "UK") if c in (r[5] or "")]
        if found: ev.append((4, "register", found, f"the register states {r[5]}", ""))
        dev = {"the Scottish Parliament": "SC", "the Senedd": "WA", "the Northern Ireland Assembly": "NI"}.get(ans)
        if dev: ev.append((1, "chain", [dev], f"answers to {ans}", ""))
        q = ids.get("wikidata")
        if r[3] not in LOCAL:
            for nn, why, url in wd_f.get(q, []): ev.append((6, "statute", nn, why, url))
        k = clean(ids.get("ons_name") or r[1])
        if k in sp: ev.append((2, "ons-sponsor", sp[k][0], sp[k][1], ""))
        ck = council_key(r[1])
        if ck and ck in lad: ev.append((5, "ons-gss", [lad[ck][0]], f"council matches ONS local authority {lad[ck][1]}", ""))
        if q in wd_j:
            nn = sorted({n for lbl in wd_j[q] for n in LABEL[lbl]}); ev.append((7, "wikidata", nn, "Wikidata applies to jurisdiction: " + ", ".join(sorted(wd_j[q])), f"https://www.wikidata.org/wiki/{q}"))
        os_ = own_site(desc.get(ids.get("govuk_slug", ""), "")) if ids.get("govuk_slug") else None
        if os_ and os_[0] != "ambiguous": ev.append((3, "own-site", os_[0], "its GOV.UK page says it works " + "; ".join(os_[1]), f"https://www.gov.uk/government/organisations/{ids['govuk_slug']}"))
        if k in pb: ev.append((8, "pb-2020", pb[k][0], f"2020 compilation: {pb[k][1]}", ""))
        ch = ids.get("companies_house"); ch = ch[0] if isinstance(ch, list) and ch else ch
        if isinstance(ch, str) and re.match(r"^(SC|SO|SL|SZ|SA|SF)\d", ch): ev.append((9, "companies", ["SC"], f"registered in Scotland ({ch})", f"https://find-and-update.company-information.service.gov.uk/company/{ch}"))
        if isinstance(ch, str) and re.match(r"^(NI|NC|NF|R0)\d", ch): ev.append((9, "companies", ["NI"], f"registered in Northern Ireland ({ch})", f"https://find-and-update.company-information.service.gov.uk/company/{ch}"))
        if not ev:
            out[r[0]] = {"nations": [], "basis": None, "evidence": []}; continue
        ev.sort(key=lambda e: e[0]); best = ev[0]
        disagree = [e for e in ev[1:] if set(e[2]) != set(best[2]) and not (set(e[2]) <= set(best[2]) or "UK" in best[2])]
        if disagree: conflicts.append({"id": r[0], "name": r[1], "chosen": [best[1], best[2]], "against": [[e[1], e[2]] for e in disagree]})
        out[r[0]] = {"nations": best[2], "basis": best[1], "why": best[3], "url": best[4],
                     "evidence": [{"rank": e[0], "source": e[1], "nations": e[2], "why": e[3], "url": e[4]} for e in ev]}
    return D, out, conflicts, lad

def check(D, out):
    """Known answers from the governance instruments themselves; each must be FOUND (D-OG17)."""
    p = []; by = {r[1]: r[0] for r in D["r"] if r[4]}
    for name, want in [("Aberdeen City Council", ["SC"]), ("Belfast Harbour Commissioners", ["NI"]), ("Estyn", None),
                       ("Law Commission", ["UK"]), ("Planning Inspectorate", ["EN"]), ("Three Rivers District Council", ["EN"]),
                       ("Central Arbitration Committee", ["EN", "SC", "WA"]), ("Bradford Metropolitan District Council", ["EN"]), ("City and County of Swansea", ["WA"]), ("Civil Nuclear Constabulary", ["EN", "SC"]), ("HM Land Registry", ["EN", "WA"])]:
        rid = by.get(name)
        if rid is None: p.append(f"{name}: not an open record"); continue
        got = out.get(rid, {}).get("nations")
        if want is not None and got != want: p.append(f"{name}: expected {want}, got {got}")
    # the resolver never invents: a body with no evidence has no nation
    if any(v["nations"] and not v["evidence"] for v in out.values()): p.append("nation without evidence")
    return p

if __name__ == "__main__":
    D, out, conflicts, lad = resolve()
    if "--negative" in sys.argv:
        out2 = json.loads(json.dumps(out)); rid = next(r[0] for r in D["r"] if r[1] == "Aberdeen City Council"); out2[rid]["nations"] = ["EN"]
        ok = bool(check(D, out2)); print("caught wrong nation" if ok else "MISSED wrong nation"); sys.exit(0 if ok else 1)
    probs = check(D, out)
    welsh = {v[1]: v[2] for v in lad.values() if v[2]}
    (ROOT / "data/nation-evidence.json").write_text(json.dumps({"bodies": out, "conflicts": conflicts, "welsh_names_ons": welsh}, indent=1))
    c = collections.Counter(v["basis"] for v in out.values())
    print("placed", sum(1 for v in out.values() if v["nations"]), "of", len(out), dict(c), "conflicts", len(conflicts), "problems", probs)
    sys.exit(1 if probs else 0)
