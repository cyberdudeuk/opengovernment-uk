"""The UK's relationships: memberships, treaties and agreements, at UK and home-nation level, linked to the UK bodies
that hold them.
  memberships  organisations the UK or a home nation is a member of (Wikidata P463, current and former), merged with
               the officially checked UK leads (data/international.json);
  treaties     every international treaty GOV.UK publishes, with the partner from the title ("UK/Korea: ...") or
               'multilateral', the FCDO Command Paper series printed in the title, and the UK publishing body;
  agreements   memoranda of understanding, concordats, accords, framework and partnership agreements, joint
               declarations and letters of intent that GOV.UK publishes, between the UK and others or between UK bodies.
Domains (defence, trade, justice and so on) are worked out from titles and types, so a few may be wrong.
Writes data/relations.json. --negative proves the checks fail when they should."""
import collections, copy, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]; EV = ROOT / "sources/evidence"
DOMAINS = [("defence", "Defence and security", r"defen[cs]e|military|armed forces|nato|aukus|five eyes|security|classified|intelligence|armament|occar|\barmy\b|\bnavy\b|air force|weapon|missile|nuclear suppliers|wassenaar|australia group|non-proliferation"),
           ("justice", "Justice, policing and borders", r"police|policing|crime|criminal|justice|extradition|legal assistance|interpol|europol|prisoner|\bborder\b|readmission|migration|asylum|immigration|\bvisa\b"),
           ("trade", "Trade, customs and investment", r"trade|customs|tariff|investment|economic partnership|free trade|mutual recognition|conformity|export|import|commerce|cptpp|\bwto\b|world trade"),
           ("finance", "Finance, tax and development", r"tax|double taxation|fiscal|bank|monetary|finance|financial|\bimf\b|development|\bdebt\b|\bloan\b|\baid\b|\bg7\b|\bg20\b|oecd"),
           ("transport", "Transport, aviation and maritime", r"air services|aviation|civil aviation|maritime|shipping|\bship\b|seafarer|\bport\b|\brail\b|\broad\b|transport|eurocontrol|hydrographic|vessel|navigation"),
           ("science", "Science, space and technology", r"science|scientific|research|space|satellite|technology|digital|telecommunication|cyber|\bdata\b|observatory|earth observation|meteorolog|innovation|artificial intelligence"),
           ("energy", "Energy, climate and environment", r"energy|climate|environment|nuclear energy|\batomic\b|\boil\b|\bgas\b|electricity|renewable|carbon|emission|biodiversity|whaling|fisher|ocean|marine|antarctic|arctic"),
           ("health", "Health and social security", r"health|medical|medicine|pandemic|social security|pension|healthcare|who\b|world health"),
           ("culture", "Culture, education and people", r"culture|cultural|education|school|university|youth|\bsport\b|heritage|holocaust|museum|language|scholarship|\bfilm\b|co-production|audiovisual"),
           ("governance", "Diplomacy and governance", r"united nations|council of europe|osce|commonwealth|diplomatic|consular|privileges and immunities|human rights|elections|governance|cooperation")]
SERIES = {"TS": "Treaty Series", "CS": "Country Series", "MS": "Miscellaneous Series", "EU": "European Union Series"}
PERSON = re.compile(r"\b(Rt Hon|Sir |Dame |Baroness |Lord [A-Z][a-z]+|Mr |Mrs |Ms |Dr [A-Z]|(Prime Minister|President|Chancellor|Foreign Secretary|Minister) [A-Z][a-z]+ [A-Z][a-z]+)")
KEEP = {"policy_paper", "corporate_report", "guidance", "notice", "detailed_guide", "document_collection", "transparency", "independent_report", "statutory_guidance", "promotional", "decision"}


def domain(text):
    t = text.lower()
    return next((k for k, _, rx in DOMAINS if re.search(rx, t)), "other")


def norm(s): return re.sub(r"[^a-z0-9]+", " ", re.sub(r"\(.*?\)", "", s.lower())).replace(" the ", " ").strip()


def build():
    G = json.loads((EV / "govuk-agreements.json").read_text()); W = json.loads((EV / "wikidata-memberships.json").read_text())
    I = json.loads((ROOT / "data/international.json").read_text())  # noqa: E741
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    slug = {r[10]["govuk_slug"]: r[0] for r in D["r"] if r[10].get("govuk_slug")}
    names = [r[1] for r in D["r"] if PERSON.search(r[1])]  # bodies named after people, e.g. Sir John Soane's Museum
    named = lambda t: bool(PERSON.search(t)) and not any(n in t for n in names)  # roles only: drop titles naming a person
    lead = {norm(b["name"]): b for b in I["bodies"]}
    mem = []
    for m in W["memberships"]:
        b = lead.get(norm(m["name"]))  # exact name only: a partial match could pin a whole body on one track's lead
        mem.append({"who": m["who"], "name": m["name"], "status": m["status"], "start": m["start"], "end": m["end"] or m["dissolved"], "site": m["site"], "qid": m["qid"],
                    "domain": domain(m["name"] + " " + " ".join(m["types"])), "types": m["types"], "lead": [x["id"] for x in b["lead"]] if b else []})
    seen = {norm(m["name"]) for m in mem}
    for b in I["bodies"]:  # officially checked bodies Wikidata does not record as a membership
        if norm(b["name"]) not in seen:
            mem.append({"who": "UK", "name": b["name"], "status": "current", "start": "", "end": "", "site": "", "qid": "", "domain": domain(b["name"] + " " + b["role"]), "types": [I["groups"][b["group"]]], "lead": [x["id"] for x in b["lead"]], "official": b["evidence"][0]["url"]})
    tre = []
    for t in G["treaties"]:
        if named(t["title"]): continue
        m = re.match(r"^(UK|United Kingdom)\s*/\s*([^:]+):|^([^:/]+)\s*/\s*(UK|United Kingdom):", t["title"])
        partner = (m.group(2) or m.group(3)).strip() if m else ""
        s = re.search(r"\[(TS|CS|MS|EU)\b[^\]]*\]", t["title"])
        tre.append({"title": t["title"], "url": t["url"], "date": t["date"], "partner": partner, "kind": "bilateral" if partner else "multilateral or other",
                    "series": SERIES.get(s.group(1), "") if s else "", "domain": domain(t["title"]), "uk": [slug[o] for o in t["orgs"] if o in slug]})
    turls = {t["url"] for t in tre}; partners = {p.lower() for p in (t["partner"] for t in tre) if p}
    agr = []
    for a in G["agreements"]:
        if a["type"] not in KEEP or a["url"] in turls or named(a["title"]): continue
        tl = a["title"].lower(); intl = bool(a["places"]) or any(re.search(r"\b" + re.escape(p) + r"\b", tl) for p in partners if len(p) > 3)
        agr.append({"title": a["title"], "url": a["url"], "date": a["date"], "form": a["matched"], "level": "international" if intl else "within the UK (as titled)",
                    "domain": domain(a["title"] + " " + a["desc"]), "uk": [slug[o] for o in a["orgs"] if o in slug]})
    return {"read": G["read"], "person_names": names, "domains": {k: v for k, v, _ in DOMAINS} | {"other": "Other"}, "series": SERIES, "memberships": mem, "treaties": tre, "agreements": agr}, D


def check(o, D):
    e = []; R = {r[0] for r in D["r"]}
    for x in o["treaties"] + o["agreements"]:
        if not x["url"].startswith("https://www.gov.uk/"): e.append(f"not a GOV.UK link: {x['title'][:40]}")
        if any(u not in R for u in x["uk"]): e.append(f"unknown UK body on {x['title'][:40]}")
    for x in o["treaties"] + o["agreements"]:
        if PERSON.search(x["title"]) and not any(n in x["title"] for n in o["person_names"]): e.append(f"names a person: {x['title'][:40]}")
    names = {m["name"]: m for m in o["memberships"] if m["who"] == "UK"}
    for n, st in [("NATO", "current"), ("European Union", "former"), ("G7", "current")]:
        if names.get(n, {}).get("status") != st: e.append(f"known answer wrong: {n} should be {st}")
    if not any(t["partner"] == "Korea" for t in o["treaties"]): e.append("known answer wrong: no UK/Korea treaty parsed")
    if any(m["status"] == "current" and m["end"] for m in o["memberships"]): e.append("a membership with an end date is shown as current")
    return e


def main():
    o, D = build()
    if "--negative" in sys.argv:
        cases = []
        x = copy.deepcopy(o); next(m for m in x["memberships"] if m["name"] == "European Union")["status"] = "current"; cases.append(x)
        x = copy.deepcopy(o); x["treaties"][0]["url"] = "https://example.com/t"; cases.append(x)
        x = copy.deepcopy(o); x["agreements"][0]["uk"] = ["government-organisation:NOPE"]; cases.append(x)
        x = copy.deepcopy(o); x["agreements"][0]["title"] = "Prime Minister Jane Example's visit: joint statement"; cases.append(x)
        if not all(check(c, D) for c in cases): sys.exit("relations negative: a breaker was not caught")
        print(f"relations negative: all {len(cases)} breakers caught"); return
    e = check(o, D)
    if e: sys.exit("relations: " + "; ".join(e[:6]))
    (ROOT / "data/relations.json").write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")))
    C = collections.Counter
    print("relations:", len(o["memberships"]), "memberships", dict(C((m["who"], m["status"]) for m in o["memberships"])), "|", len(o["treaties"]), "treaties", dict(C(t["kind"] for t in o["treaties"])),
          "|", len(o["agreements"]), "agreements", dict(C(a["level"] for a in o["agreements"])))


if __name__ == "__main__":
    main()
