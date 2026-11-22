"""Plain-English classification of every open body, for readers with no prior knowledge.

For each body:
  purpose  - what it does, in ten plain-English groups based on the UN Classification of the Functions of Government
             (COFOG). MODELLED: worked out from its kind, name and its own GOV.UK description by stated keyword rules.
  reach    - where it works: a local area, one nation, several nations, the whole UK, or not stated (from data/body-nations.json).
  formed   - how the people in charge get there (elected, appointed, part of a department...), how often, and by what
             process. The rule is typical for that kind of body, with the law or guidance it comes from.
Writes data/classification.json. Election facts verified 22 November 2026 against the Acts on legislation.gov.uk."""
import collections, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]; SRC = ROOT / "sources"
L = "https://www.legislation.gov.uk/"
PURPOSES = [  # (key, plain label, plain explanation, COFOG division)
    ("govt", "Running the country", "Making laws, collecting taxes, keeping records, statistics and elections, and links with other countries.", "01"),
    ("defence", "Defence", "The armed forces and keeping the country safe from attack.", "02"),
    ("safety", "Police, courts and safety", "Police, fire and rescue, courts, prisons and the justice system.", "03"),
    ("economy", "Money, business and transport", "Jobs, business, trade, farming, energy, roads, railways, ports and airports.", "04"),
    ("environment", "Nature and the environment", "Protecting nature, cleaning up pollution and looking after the countryside and sea.", "05"),
    ("housing", "Homes and local places", "Housing, planning new buildings, water supply and improving towns and cities.", "06"),
    ("health", "Health", "Hospitals, doctors, medicines and keeping people healthy.", "07"),
    ("culture", "Culture, sport and heritage", "Museums, libraries, the arts, sport, broadcasting, languages and historic places.", "08"),
    ("education", "Education and research", "Schools, colleges, universities, exams, skills and research.", "09"),
    ("support", "Benefits, pensions and care", "Pensions, benefits, social care and support for children, families and disabled people.", "10"),
    ("local", "Many local services", "Councils run many local services at once: bins, roads, schools, care, libraries and planning.", "06"),
    ("unknown", "Not yet worked out", "The sources don't say enough yet. You can help by sending a correction.", ""),
]
KW = [  # checked in order; the first rule that matches wins (tax first: HMRC's description also mentions benefits)
    ("govt", r"\b(tax|taxes|revenue|customs|treasury)\b"),
    ("defence", r"\b(defen[cs]e|military|armed forces|army|navy|naval|royal air force|raf|veterans?|soldiers?|atomic weapons|nuclear deterrent|dstl)\b"),
    ("safety", r"\b(police|policing|constabulary|court|courts|tribunals?|justice|prison|probation|fire and rescue|fire service|crime|criminal|prosecut\w*|judicial|judges|legal aid|coroner|border force|sentencing|parole|youth justice|ombudsman)\b"),
    ("health", r"\b(health|nhs|hospital|medical|medicines?|clinical|ambulance|dental|nursing|nurses|midwi\w+|care quality|public health|blood|organ|genomic|pharma\w*|surgeon|gp|perinatal|prescribing|disease|caldicott|covid\w*|patients?)\b"),
    ("economy", r"\b(financial|finance|energy|electricity|banking|audience research)\b"),  # before education: "research" and "reporting" misled (NESO, FRC, RAJAR)
    ("education", r"\b(education|schools?|universit\w+|colleges?|student|skills|qualifications?|exam\w*|ofsted|ofqual|estyn|learning|apprenticeship\w*|research|science|scientific|innovation|academ\w+)\b"),
    ("support", r"\b(pensions?|benefits?|social security|child support|social care|disabilit\w+|welfare|children'?s commissioner|older people|carers?|care inspectorate|social work|fuel poverty|poverty)\b"),
    ("culture", r"\b(museums?|galler\w+|library|libraries|arts?|cultur\w+|heritage|historic|sport\w*|theatres?|broadcast\w*|bbc|s4c|channel 4|archives?|lottery|gaelic|g[aà]idhlig|welsh language|cymraeg|zoo|botanic\w*|royal parks|film|cycling|championships|games)\b"),
    ("environment", r"\b(environment\w*|natur\w+|wildlife|waste|pollution|climate|conservation|national park|marine|countryside|forest\w*|woodland|rivers?|canals?|flood\w*|nuclear decommissioning|radioactive)\b"),
    ("housing", r"\b(housing|homes?|planning|regeneration|development corporation|water|sewerage|land registry|valuation|building safety|new towns?|leasehold|communities)\b"),
    ("economy", r"\b(business|trade|enterprise|transport|rail\w*|roads?|highways|airports?|aviation|ports?|harbou?r|shipping|maritime|energy|electricity|gas|industr\w+|investment|bank\w*|financ\w+|competition|markets?|agricultur\w+|farm\w*|fisher\w+|food|tourism|employment|jobs|work|communications|ofcom|post office|royal mint|insolvency|companies|patent|intellectual property|consumer|economic|economy|growth|export|shipbuilding|infrastructure|cattle|livestock|animal|ventures|plant)\b"),
    ("govt", r"\b(tax|revenue|customs|treasury|cabinet|statistics|audit\w*|civil service|government|parliament\w*|assembly|senedd|elections?|electoral|boundary|foreign|international|commonwealth|debt|procurement|commercial|digital|data|records|privy council|prime minister|office|cabinet office|treasury solicitor|legal|law commission|standards in public life|appointments|charit\w+|policy|ict|programme)\b"),
]
TYPE_PURPOSE = {"Court": "safety", "Tribunal": "safety", "NHS trust": "health", "Integrated care board": "health", "Health board": "health", "Local health board": "health",
                "Special health authority": "health", "Health and social care trust": "health", "Care trust": "health", "Commissioning support unit": "health", "NHS England region": "health",
                "Local Government": "local", "Non-metropolitan district": "local", "Unitary authority": "local", "Metropolitan district": "local", "London borough": "local", "County council": "local", "Combined authority": "local"}
LOCAL_TYPES = {"Local Government", "Non-metropolitan district", "Unitary authority", "Metropolitan district", "London borough", "County council", "Combined authority",
               "NHS trust", "Health board", "Local health board", "Health and social care trust", "Care trust", "Integrated care board"}
COUNCIL = re.compile(r"\b(council|borough of|city and county of|comhairle)\b", re.I)

# How the people in charge get there. "src" links are the law or guidance the rule rests on (verified).
PA = ("https://www.gov.uk/government/publications/governance-code-for-public-appointments", "Governance Code for Public Appointments")
VOTE = ("https://www.gov.uk/elections-in-the-uk/local-government", "GOV.UK: voting systems in local elections")
FORM = {
    "council-EN": ("Elected by local voters", "Every 4 years. Some councils elect all councillors at once; others elect a third or half at a time, so there is a vote in most years.", "Voters choose councillors for their area. The candidate with the most votes wins (first past the post).", [VOTE, (L + "ukpga/2000/22/part/IV", "Local Government Act 2000, Part 4")]),
    "council-WA": ("Elected by local voters", "Every 5 years.", "Voters choose councillors for their area. Most councils use first past the post; the law lets a council choose ranked voting instead.", [VOTE, (L + "asc/2021/1/part/1", "Local Government and Elections (Wales) Act 2021, sections 14 to 16")]),
    "council-SC": ("Elected by local voters", "Every 5 years.", "Voters rank candidates in order of preference (single transferable vote), and several councillors are chosen for each area.", [VOTE, (L + "asp/2020/12/section/2", "Scottish Elections (Reform) Act 2020, section 2")]),
    "council-NI": ("Elected by local voters", "Every 4 years.", "Voters rank candidates in order of preference (single transferable vote), and several councillors are chosen for each area.", [VOTE]),
    "dept-UK": ("Led by elected politicians", "Changes after a general election (at least every 5 years) or when ministers are moved.", "Ministers are chosen by the Prime Minister from the elected House of Commons or the appointed House of Lords. Civil servants, who are not elected, do the day-to-day work.", [(L + "ukpga/2022/11/section/4", "Dissolution and Calling of Parliament Act 2022, section 4")]),
    "dept-SC": ("Led by elected politicians", "Changes after a Scottish Parliament election (every 5 years) or when ministers are moved.", "The First Minister is chosen by the elected Scottish Parliament and picks the other ministers.", [(L + "ukpga/1998/46/section/44", "Scotland Act 1998, section 44"), (L + "asp/2020/12/section/1", "Scottish Elections (Reform) Act 2020, section 1")]),
    "dept-WA": ("Led by elected politicians", "Changes after a Senedd election (every 4 years from 2026) or when ministers are moved.", "The First Minister is chosen by the elected Senedd and picks the other ministers.", [(L + "ukpga/2006/32/section/45", "Government of Wales Act 2006, section 45"), (L + "asc/2024/4", "Senedd Cymru (Members and Elections) Act 2024")]),
    "dept-NI": ("Led by elected politicians", "Changes after a Northern Ireland Assembly election (every 5 years).", "Ministers come from the elected Assembly. Parties share the posts by their number of seats, and the First Minister and deputy First Minister share power.", [(L + "ukpga/1998/47/section/20", "Northern Ireland Act 1998, section 20"), (L + "ukpga/2014/13", "Northern Ireland (Miscellaneous Provisions) Act 2014")]),
    "nmd": ("Led by officials, not ministers", "Leaders are appointed for a fixed term.", "Its head or board is appointed, often after an open competition, so it can work independently of politicians. It answers to Parliament.", [PA]),
    "agency": ("Part of a government department", "Its chief executive is appointed when the post falls vacant.", "It is run by civil servants inside a department, which sets its goals and budget. A minister answers for it.", []),
    "appointed": ("Board appointed by ministers", "Members are appointed for fixed terms, usually a few years at a time.", "Ministers appoint the chair and board, normally after an open competition that follows the public appointments rules.", [PA]),
    "company": ("Company owned by government", "Directors are appointed by the owner when terms end.", "It is set up like a company. The government (or a public body) owns it and appoints the board.", []),
    "nhs": ("Board appointed, not elected", "Board members are appointed for fixed terms.", "The chair and board are appointed through the NHS appointments process in its nation. Local people are not asked to vote.", []),
    "judicial": ("Judges chosen by an independent commission", "Judges are usually appointed until they retire.", "An independent commission picks candidates on merit (in England and Wales, the Judicial Appointments Commission). Judges are not elected, so they can be fair to everyone.", [(L + "ukpga/2005/4", "Constitutional Reform Act 2005")]),
    "parliament-body": ("Answers to a parliament", "Its leaders are appointed by or with the agreement of the parliament.", "It works for a parliament (for example, checking how public money is spent) rather than for ministers, so it can be independent of the government.", []),
    "combined": ("Led by an elected mayor and local council leaders", "The mayor is elected every 4 years.", "Voters elect the mayor (first past the post). The leaders of the councils in the area sit on its board.", [(L + "ukpga/2022/37", "Elections Act 2022")]),
    "charity": ("Run by a board of trustees", "Trustees serve terms set in its own rules.", "It is a charity or non-profit body with its own trustees, which government partly funds or controls.", []),
    "local-body": ("Set up or owned by a local council", "Its managers or board are appointed by the council when posts fall vacant.", "ONS counts it as local government because one or more councils control it. The council, whose councillors are elected, appoints who runs it.", [("https://www.ons.gov.uk/economy/nationalaccounts/uksectoraccounts/datasets/publicsectorclassificationguide", "ONS Public Sector Classification Guide")]),
    "central-body": ("Controlled by government", "Its leaders are appointed by the government that controls it.", "ONS counts it as central government because a government department or devolved government controls it. The sources don't say exactly how its leaders are chosen.", [("https://www.ons.gov.uk/economy/nationalaccounts/uksectoraccounts/datasets/publicsectorclassificationguide", "ONS Public Sector Classification Guide")]),
    "pension": ("Pension scheme for public workers", "Its managers or trustees are appointed under the scheme's rules.", "It pays pensions to people who worked in public services. Its rules say who runs it.", []),
    "territory": ("Has its own government", "Elections are held under its own laws.", "It runs most of its own affairs with its own elected law-makers. The UK is responsible for its defence and relations with other countries.", []),
    "gla": ("Elected mayor and assembly", "Every 4 years.", "Londoners elect the Mayor of London (first past the post) and the London Assembly, which checks the Mayor's work.", [(L + "ukpga/2022/37", "Elections Act 2022")]),
    "unknown": ("Not stated in the sources", "", "The sources don't say how this body is led. You can help by sending a correction.", []),
}

def purpose(name, kind, desc):
    if kind in TYPE_PURPOSE and (TYPE_PURPOSE[kind] != "local" or COUNCIL.search(name) or kind == "Combined authority"): return TYPE_PURPOSE[kind], "its kind"
    if re.search(r"\b(greater london authority|city of london corporation|combined (county )?authority|city region)\b", name, re.I): return "local", "its kind"
    text = f"{name} {desc}".lower()
    for key, rx in KW:
        if re.search(rx, text): return key, "its name and description"
    if kind in TYPE_PURPOSE: return TYPE_PURPOSE[kind], "its kind"  # a local-government body with no clearer clue
    return "unknown", ""

def formed(name, kind, fam, nations, answers_to, branch):
    home = [n for n in nations if n in ("EN", "SC", "WA", "NI")]
    if kind in ("Court", "Tribunal") or branch == "judiciary": return "judicial"
    if kind == "Combined authority": return "combined"
    if (fam == "Local authority" or kind in LOCAL_TYPES - {"NHS trust", "Health board", "Local health board", "Health and social care trust", "Care trust", "Integrated care board"}) and COUNCIL.search(name):
        return f"council-{home[0]}" if len(home) == 1 else "unknown"
    if fam == "NHS body" or kind in ("NHS trust", "Health board", "Local health board", "Health and social care trust", "Care trust", "Integrated care board", "Special health authority", "Commissioning support unit"): return "nhs"
    if kind in ("Ministerial department",): return "dept-UK"
    if kind in ("Devolved government", "UK nation"): return f"dept-{home[0]}" if len(home) == 1 and home[0] != "EN" else "dept-UK"
    if kind == "Strategic regional authority" or name == "Greater London Authority": return "gla"
    if kind in ("Overseas Territory", "Crown Dependency"): return "territory"
    if kind == "Non-ministerial department": return "nmd"
    if kind in ("Executive agency", "Sub organisation"): return "agency"
    if branch == "legislature": return "parliament-body"
    if kind in ("Executive non-departmental public body", "Advisory non-departmental public body", "Tribunal non-departmental public body", "Other statutory authority", "Independent monitoring body", "Ad-hoc advisory group", "Public corporation") and not re.search(r"\b(ltd|limited|plc)\b", name, re.I):
        return "appointed"
    if re.search(r"\b(ltd|limited|plc|llp)\b", name, re.I) or kind.startswith(("Public Non-Financial", "Public Other financial", "Public Financial", "Foreign controlled")): return "company"
    if kind == "Non-profit institutions serving households": return "charity"
    if kind == "Public Pension Funds": return "pension"
    if kind == "Local Government": return "local-body"
    if kind in ("Central Government", "Central Bank"): return "central-body"
    if kind == "Central Government" and answers_to.startswith(("the Scottish", "the Senedd", "the Northern Ireland")): return "appointed"
    return "unknown"

def reach(nations, kind, fam, name):
    if (kind in LOCAL_TYPES or fam == "Local authority") and len([n for n in nations if n in ("EN", "SC", "WA", "NI")]) <= 1: return "local", "A local area"
    if "UK" in nations: return "uk", "The whole UK"
    home = [n for n in nations if n in ("EN", "SC", "WA", "NI")]
    if len(home) > 1: return "several", "Several nations"
    if len(home) == 1: return "one", "One nation"
    if nations in (["OT"], ["CD"]): return "outside", "Outside the UK (a territory or dependency)"
    return "unstated", "Not stated"

def build():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (SRC / "opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    chains = json.loads((ROOT / "data/tree.json").read_text())["chains"]
    nat = json.loads((ROOT / "data/body-nations.json").read_text())
    desc = json.loads((SRC / "govuk-descriptions.json").read_text())
    sys.path.insert(0, str(ROOT / "tools")); from nations import branch_of  # one definition of the three branches
    out = {}
    for r in D["r"]:
        if not r[4]: continue
        ns = nat.get(r[0], []); ans = (chains.get(r[0]) or {}).get("answerable", ""); fam = D["fam"][r[2]]
        br, _ = branch_of(r[1], r[3], fam, ans)
        pk, pbasis = purpose(r[1], r[3], desc.get(r[10].get("govuk_slug", ""), ""))
        rk, rl = reach(ns, r[3], fam, r[1]); fk = formed(r[1], r[3], fam, ns, ans, br)
        out[r[0]] = {"purpose": pk, "purpose_basis": pbasis, "reach": rk, "reach_label": rl, "formed": fk}
    return D, out

def check(D, out):
    """Known answers, each must be FOUND; every body has all three fields."""
    p = []; by = {r[1]: r[0] for r in D["r"] if r[4]}
    for name, want in [("Ministry of Defence", ("defence", None)), ("NHS England", ("health", "appointed")), ("Aberdeen City Council", ("local", "council-SC")),
                       ("Cardiff Council", ("local", "council-WA")), ("Crown Prosecution Service", ("safety", "nmd")), ("Natural England", ("environment", "appointed")),
                       ("HM Revenue & Customs", ("govt", "nmd")), ("Ofqual", ("education", "nmd")), ("National Energy System Operator", ("economy", None)), ("Financial Reporting Council", ("economy", None)), ("The Scottish Government", (None, "dept-SC"))]:
        i = by.get(name)
        if not i: p.append(f"{name}: not found"); continue
        got = out[i]
        if want[0] and got["purpose"] != want[0]: p.append(f"{name}: purpose {got['purpose']}")
        if want[1] and got["formed"] != want[1]: p.append(f"{name}: formed {got['formed']}")
    if any(not (v["purpose"] and v["reach"] and v["formed"]) for v in out.values()): p.append("missing field")
    return p

if __name__ == "__main__":
    D, out = build()
    if "--negative" in sys.argv:
        o2 = json.loads(json.dumps(out)); o2[next(r[0] for r in D["r"] if r[1] == "Cardiff Council")]["formed"] = "council-EN"
        ok = bool(check(D, o2)); print("caught wrong formation" if ok else "MISSED wrong formation"); sys.exit(0 if ok else 1)
    probs = check(D, out)
    meta = {"purposes": [{"key": k, "label": a, "explain": b, "cofog": c} for k, a, b, c in PURPOSES],
            "formed": {k: {"label": a, "how_often": b, "process": c, "sources": [{"url": u, "title": t} for u, t in s]} for k, (a, b, c, s) in FORM.items()},
            "notes": "Purpose is worked out from each body's kind, name and description (modelled). How a body is formed is the rule for its kind, with the law or guidance it comes from. Election facts checked against the Acts on 22 November 2026."}
    (ROOT / "data/classification.json").write_text(json.dumps({"meta": meta, "bodies": out}, indent=1, ensure_ascii=False))
    print("purpose", dict(collections.Counter(v["purpose"] for v in out.values()).most_common()))
    print("formed", dict(collections.Counter(v["formed"] for v in out.values()).most_common()))
    print("reach", dict(collections.Counter(v["reach"] for v in out.values()).most_common()), "problems", probs)
    sys.exit(1 if probs else 0)
