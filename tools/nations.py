"""Per-nation registers: every public body associated with each UK nation, broken down by
branch of the state (legislature, executive, judiciary) and tier.
Nation comes from the register's own stated code, else from where the accountability chain ends
(a devolved legislature). Nothing is inferred from names. Writes data/nations.json and docs/nations.html."""
import collections, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
NATIONS = {"EN": "England", "SC": "Scotland", "WA": "Wales", "NI": "Northern Ireland",
           "UK": "UK-wide (stated)", "GB": "UK Government, extent not stated", "OT": "Overseas Territories", "CD": "Crown Dependencies"}
FROM_ROOT = {"the Scottish Parliament": "SC", "the Senedd": "WA", "the Northern Ireland Assembly": "NI"}
# Explicit names only: the bare word "parliamentary" also matches boundary commissions and panels that sit in the executive (D-OG16).
LEGIS_NAME = re.compile(r"^(houses? of parliament|house of commons|house of lords( commission)?|scottish parliament|senedd|welsh parliament|national assembly for wales|northern ireland assembly)\b|scottish parliamentary corporate body|independent parliamentary standards authority|commonwealth parliamentary association|parliamentary and health service ombudsman|^(senedd|assembly) commission|electoral commission|national audit office|audit scotland|audit wales|wales audit office|northern ireland audit office", re.I)
L = "https://www.legislation.gov.uk/"
# Apex of each branch, from the founding legislation (each link checked against the Act's text on legislation.gov.uk, 22 Nov 2026).
# These are stated, not register records: the register does not yet hold the legislatures or Scotland's supreme courts.
UK_APEX = {"legislature": [("UK Parliament: House of Commons and House of Lords", "No founding Act; the Parliament Act 1911 sets relations between the Houses", L + "ukpga/Geo5/1-2/13/section/1")],
           "executive": [("UK Government: the Prime Minister and ministers of the Crown", "No founding Act; ministers act under the Crown and statute", "")],
           "judiciary": [("Supreme Court of the United Kingdom", "Constitutional Reform Act 2005, s.23", L + "ukpga/2005/4/section/23")]}
EW_COURTS = ("Senior Courts of England and Wales: Court of Appeal, High Court and Crown Court", "Senior Courts Act 1981, s.1", L + "ukpga/1981/54/section/1")
APEX = {"EN": {"legislature": [("No devolved legislature: the UK Parliament legislates for England", "", "")], "executive": [("No devolved government: the UK Government governs England", "", "")], "judiciary": [EW_COURTS]},
        "SC": {"legislature": [("Scottish Parliament", "Scotland Act 1998, s.1", L + "ukpga/1998/46/section/1")],
               "executive": [("Scottish Government (the Scottish Administration)", "Scotland Act 1998, s.44", L + "ukpga/1998/46/section/44")],
               "judiciary": [("Court of Session", "Court of Session Act 1988, s.1", L + "ukpga/1988/36/section/1"), ("The Lord President, Head of the Scottish Judiciary", "Judiciary and Courts (Scotland) Act 2008, s.2", L + "asp/2008/6/section/2")]},
        "WA": {"legislature": [("Senedd Cymru (Welsh Parliament)", "Government of Wales Act 2006, s.1; renamed by the Senedd and Elections (Wales) Act 2020, s.2", L + "ukpga/2006/32/section/1")],
               "executive": [("Welsh Government", "Government of Wales Act 2006, s.45", L + "ukpga/2006/32/section/45")],
               "judiciary": [("Shared with England: " + EW_COURTS[0], EW_COURTS[1], EW_COURTS[2])]},
        "NI": {"legislature": [("Northern Ireland Assembly", "Northern Ireland Act 1998, Part IV", L + "ukpga/1998/47/part/IV")],
               "executive": [("Northern Ireland Executive (the Executive Committee)", "Northern Ireland Act 1998, s.20", L + "ukpga/1998/47/section/20")],
               "judiciary": [("Court of Judicature of Northern Ireland: Court of Appeal, High Court and Crown Court", "Judicature (Northern Ireland) Act 1978, s.1", L + "ukpga/1978/23/section/1")]},
        "GB": UK_APEX}
JUDIC_NAME = re.compile(r"\b(court|courts|tribunal|tribunals|judicial|judiciary|judges|sheriff principal|lord chief justice)\b", re.I)
COURT_ADMIN = re.compile(r"courts? (and|&) tribunals? service|courts service|tribunals service|judicial appointments|judicial office|judicial college|judicial conduct", re.I)

def court_administration_branch(name: str) -> tuple[str, str]:
    """Contested case: bodies that run or appoint to the courts but do not judge (HM Courts & Tribunals Service,
    Scottish Courts and Tribunals Service, Judicial Appointments Commission ...). Constitutionally they sit in the
    executive or are independent statutory bodies; functionally they serve the judiciary.
    Default chosen: count them under the judiciary, tier 'court administration and appointments', so a reader
    looking at a nation's justice system sees them; the tier label keeps them distinct from courts themselves."""
    return "judiciary", "Court administration and appointments"

def tier_of(t: str, fam: str, answerable: str) -> str:
    if fam == "Local authority" or t in {"Local Government", "Non-metropolitan district", "Unitary authority", "Metropolitan district", "London borough", "County council", "Combined authority"}:
        return "Local government"
    if fam == "NHS body" or "NHS" in answerable or t in {"NHS trust", "Integrated care board", "Health board", "Local health board", "Special health authority", "Health and social care trust", "Care trust", "Commissioning support unit", "NHS England region"}:
        return "Health service"
    if t in {"Ministerial department", "Non-ministerial department", "Devolved government", "UK nation"}:
        return "Government departments"
    if t in {"Public Non-Financial Corporations", "Public corporation"} or t.startswith("Public Other financial") or t in {"Public Financial Auxiliaries", "Public Pension Funds"}:
        return "Public corporations and financial bodies"
    return "Arm's-length bodies and other central bodies"

def branch_of(name: str, t: str, fam: str, answerable: str) -> tuple[str, str]:
    if COURT_ADMIN.search(name): return court_administration_branch(name)
    if t in {"Court", "Tribunal"} or JUDIC_NAME.search(name): return "judiciary", "Courts and tribunals"
    if LEGIS_NAME.search(name) or answerable == "Parliament directly (not a ministerial body)": return "legislature", "Legislatures and their bodies"
    return "executive", tier_of(t, fam, answerable)

def nations_of(code: str, answerable: str) -> tuple[list[str], str]:
    if code:
        found = [c for c in ("EN", "SC", "WA", "NI", "OT", "CD", "UK") if c in code]
        if found: return found, "stated by the register"
    if answerable in FROM_ROOT: return [FROM_ROOT[answerable]], "answers to that nation's legislature"
    if answerable.startswith("Parliament"): return ["GB"], "answers to the UK Parliament; extent not stated"
    return [], ""

def load():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    chains = json.loads((ROOT / "data/tree.json").read_text())["chains"]
    return D, chains

def build(D, chains):
    out = {k: {"name": v, "branches": {"legislature": collections.defaultdict(list), "executive": collections.defaultdict(list), "judiciary": collections.defaultdict(list)}} for k, v in NATIONS.items()}
    unplaced = 0
    for r in D["r"]:
        if not r[4]: continue  # open bodies only: closed ones belong to history, not the current register
        ans = (chains.get(r[0]) or {}).get("answerable", "")
        codes, basis = nations_of(r[5], ans)
        if not codes: unplaced += 1; continue
        br, tier = branch_of(r[1], r[3], D["fam"][r[2]], ans)
        for c in codes: out[c]["branches"][br][tier].append({"id": r[0], "name": r[1], "type": r[3], "basis": basis, "answers_to": ans})
    for c, n in out.items():
        n["apex"] = {br: [{"name": a, "basis": b, "url": u} for a, b, u in v] for br, v in APEX.get(c, {}).items()}
        n["uk_apex"] = {br: [{"name": a, "basis": b, "url": u} for a, b, u in v] for br, v in UK_APEX.items()} if c in ("EN", "SC", "WA", "NI") else {}
        for br in n["branches"]:
            n["branches"][br] = {k: sorted(v, key=lambda x: x["name"]) for k, v in sorted(n["branches"][br].items())}
        n["counts"] = {br: sum(len(v) for v in n["branches"][br].values()) for br in n["branches"]}
    return out, unplaced

def check(out, unplaced, D):
    """Known answers, no double-counting within a nation, every open body placed or counted as unplaced."""
    p = []
    def where(name):
        return {(c, br) for c, n in out.items() for br, tiers in n["branches"].items() for v in tiers.values() for x in v if x["name"] == name}
    # Known answers must be FOUND: a known answer that silently matches nothing proves nothing (D-OG17).
    for name, want in [("The Scottish Government", ("SC", "executive")), ("Scottish Parliamentary Corporate Body", ("SC", "legislature")),
                       ("Northern Ireland Assembly Commission", ("NI", "legislature")), ("Welsh Government", ("WA", "executive")),
                       ("Scottish Courts and Tribunals Service", ("SC", "judiciary")), ("Supreme Court of the United Kingdom", ("GB", "judiciary")),
                       ("Houses of Parliament", ("GB", "legislature")), ("Parliamentary Boundary Commission for England", ("EN", "executive"))]:
        if want not in where(name): p.append(f"{name}: expected {want}, got {sorted(where(name))}")
    for c in ("EN", "SC", "WA", "NI", "GB"):
        for br in ("legislature", "executive", "judiciary"):
            if not out[c]["apex"].get(br): p.append(f"{c}: no apex for {br}")
            for a in out[c]["apex"].get(br, []):
                if a["url"] and not a["url"].startswith("https://www.legislation.gov.uk/"): p.append(f"{c}: apex link not to legislation.gov.uk")
    for c, n in out.items():
        ids = [x["id"] for tiers in n["branches"].values() for v in tiers.values() for x in v]
        if len(ids) != len(set(ids)): p.append(f"{c}: a body appears twice")
    placed = {x["id"] for n in out.values() for tiers in n["branches"].values() for v in tiers.values() for x in v}
    if len(placed) + unplaced != sum(1 for r in D["r"] if r[4]): p.append("open bodies not all accounted for")
    return p

PAGE = """<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OpenGovernment UK: the state, nation by nation</title>
<style>:root{--bg:#f6f2ea;--paper:#fffdf8;--ink:#1c1a17;--muted:#5a544b;--line:#ddd3c3;--hi:#b6391f;--leg:#2f5d8a;--exe:#2e6b4f;--jud:#7a4b8c;--focus:#1c5bd6}@media(prefers-color-scheme:dark){:root{--bg:#14120f;--paper:#1c1915;--ink:#efe9de;--muted:#b4aa9a;--line:#3a342b;--hi:#ff8a6e;--leg:#8cb8e6;--exe:#86c9a6;--jud:#c9a3dc;--focus:#8ab4ff}}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 Inter,"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink)}header,footer{padding:18px 24px;background:var(--paper);border-bottom:1px solid var(--line)}footer{border-top:1px solid var(--line);border-bottom:0;color:var(--muted);font-size:.85rem}
h1{font:700 1.5rem Georgia,serif;margin:0 0 4px}h2{font:700 1.2rem Georgia,serif;margin:0 0 8px}p{margin:0;color:var(--muted)}main{padding:16px 24px;max-width:1200px}
[role=tablist]{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px}[role=tab]{font:inherit;padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:var(--paper);color:var(--ink);cursor:pointer}[role=tab][aria-selected=true]{background:var(--ink);color:var(--paper)}
button:focus-visible,summary:focus-visible,input:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:10px 0 16px}@media(max-width:640px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}.kpi{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:10px 12px}.kpi b{display:block;font-size:1.5rem}
.bar{display:flex;height:14px;border-radius:7px;overflow:hidden;gap:2px;margin:6px 0 14px}.bar span{display:block}
.branch{border-left:5px solid var(--c);background:var(--paper);border-radius:10px;padding:10px 14px;margin:0 0 12px}.branch h3{margin:0 0 6px;font-size:1rem}
details{border-top:1px solid var(--line);padding:6px 0}summary{cursor:pointer}ul{margin:6px 0 4px;padding-left:20px;columns:2;column-gap:28px}@media(max-width:700px){ul{columns:1}}li{break-inside:avoid;font-size:.9rem}li small{color:var(--muted)}
label{display:block;margin:0 0 10px}input{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;width:100%;max-width:420px;background:var(--paper);color:var(--ink)}.note{font-size:.85rem;margin:8px 0}.apex{color:var(--ink);margin:0 0 6px;font-size:.92rem}.apex small{color:var(--muted)}a{color:var(--hi)}</style></head><body>
<header><h1>The state, nation by nation</h1><p>Every open public body associated with each nation, split into the three branches of the state. A nation is shown only where a register states it, or where the body answers to that nation's legislature.</p></header>
<main><div role="tablist" id="tabs" aria-label="Nations"></div><section id="panel" role="tabpanel" aria-live="polite"></section>
<p class="note">Bodies answering to the UK Parliament that state no territorial extent are shown under “UK Government, extent not stated”, rather than guessed as England-only. The top of each branch is stated from its founding legislation, linked; the legislatures themselves are not yet register records. Court administration and judicial appointments bodies are counted with the judiciary, in their own tier, although they do not judge cases. __UNPLACED__ open bodies have no nation in any source and are not shown.</p></main>
<footer>OpenGovernment UK, an open-source public good. <a href="./">Back to the register</a> · <a href="./navigator.html">Documentation and traceability</a> · Data: <a href="https://github.com/cyberdudeuk/opengovernment-uk/blob/main/data/nations.json">nations.json</a></footer>
<script id="nd" type="application/json">__DATA__</script>
<script>"use strict";
const N=JSON.parse(document.getElementById("nd").textContent),esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const B=[["legislature","Legislature","--leg"],["executive","Executive","--exe"],["judiciary","Judiciary","--jud"]],order=["EN","SC","WA","NI","UK","GB","OT","CD"];
const tabs=document.getElementById("tabs");tabs.innerHTML=order.map((k,i)=>`<button role="tab" id="t-${k}" aria-selected="${i===0}" aria-controls="panel" tabindex="${i===0?0:-1}" data-k="${k}">${esc(N[k].name)}</button>`).join("");
const apex=(xs,label)=>xs&&xs.length?`<p class="apex"><b>${label}:</b> ${xs.map(a=>`${esc(a.name)}${a.basis?` <small>(${a.url?`<a href="${esc(a.url)}">${esc(a.basis)}</a>`:esc(a.basis)})</small>`:""}`).join("; ")}</p>`:"";
let q="";function show(k){const n=N[k],tot=B.reduce((s,b)=>s+n.counts[b[0]],0);
document.querySelectorAll("[role=tab]").forEach(t=>{const on=t.dataset.k===k;t.setAttribute("aria-selected",on);t.tabIndex=on?0:-1});
const f=x=>!q||x.name.toLowerCase().includes(q);
document.getElementById("panel").innerHTML=`<h2>${esc(n.name)}</h2><div class="kpis"><div class="kpi"><b>${tot}</b>open bodies</div>${B.map(b=>`<div class="kpi"><b>${n.counts[b[0]]}</b>${b[1].toLowerCase()}</div>`).join("")}</div>
<div class="bar" role="img" aria-label="${B.map(b=>b[1]+" "+n.counts[b[0]]).join(", ")}">${B.map(b=>`<span style="flex:${n.counts[b[0]]};background:var(${b[2]})"></span>`).join("")}</div>
<label>Filter this nation by name <input id="q" type="search" value="${esc(q)}" autocomplete="off"></label>
${B.map(b=>`<section class="branch" style="--c:var(${b[2]})"><h3>${b[1]} · ${n.counts[b[0]]} bodies in the register</h3>${apex(n.apex[b[0]],"At the top")}${apex(n.uk_apex[b[0]],"For reserved matters, the UK level")}${Object.entries(n.branches[b[0]]).map(([tier,xs])=>{const v=xs.filter(f);return v.length?`<details${q?" open":""}><summary>${esc(tier)} (${v.length})</summary><ul>${v.map(x=>`<li>${esc(x.name)} <small>${esc(x.type)} · ${esc(x.basis)}</small></li>`).join("")}</ul></details>`:""}).join("")||"<p>None in the sources.</p>"}</section>`).join("")}`;
const i=document.getElementById("q");i.addEventListener("input",()=>{q=i.value.trim().toLowerCase();const p=i.selectionStart;show(k);const j=document.getElementById("q");j.focus();j.setSelectionRange(p,p)})}
tabs.addEventListener("click",e=>{const t=e.target.closest("[role=tab]");if(t)show(t.dataset.k)});
tabs.addEventListener("keydown",e=>{if(!["ArrowRight","ArrowLeft"].includes(e.key))return;const ts=[...tabs.children],i=ts.indexOf(document.activeElement),n=ts[(i+(e.key==="ArrowRight"?1:ts.length-1))%ts.length];n.focus();show(n.dataset.k)});
show(order[0]);
</script></body></html>"""

if __name__ == "__main__":
    D, chains = load(); out, unplaced = build(D, chains)
    _orig = branch_of
    if "--negative" in sys.argv:  # break the judiciary rule: the known answers must catch it
        globals()["branch_of"] = lambda n, t, f, a: ("executive", "x")
        bad, _ = build(D, chains); ok = bool(check(bad, _, D)); print("caught branch break" if ok else "MISSED branch break")
        globals()["branch_of"] = _orig; out2, u2 = build(D, chains); out2["SC"]["apex"]["judiciary"] = []
        ok2 = bool(check(out2, u2, D)); print("caught missing apex" if ok2 else "MISSED missing apex"); sys.exit(0 if ok and ok2 else 1)
    probs = check(out, unplaced, D)
    for f in ("data/nations.json", "docs/nations.json"): (ROOT / f).write_text(json.dumps({"nations": out, "unplaced_open_bodies": unplaced}, indent=1))
    (ROOT / "docs/nations.html").write_text(PAGE.replace("__DATA__", json.dumps(out).replace("</", "<\\/")).replace("__UNPLACED__", str(unplaced)))
    for k, n in out.items(): print(f"{k:3} {n['name']:36} {n['counts']}")
    print("unplaced", unplaced, "problems", probs); sys.exit(1 if probs else 0)
