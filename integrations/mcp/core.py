"""OpenGovernment UK: the answers behind the MCP connector, with no dependencies beyond Python's standard library.

Reads only the files the portal publishes, either from the website (default) or from a local copy of docs/
(set OGUK_DATA to a folder or another https base address). Read-only: nothing is written, nothing is executed.
Every answer carries the file it came from and the licence, so whoever uses it can cite it.
"""
import csv, io, json, os, pathlib, re, urllib.request

SITE = "https://cyberdudeuk.github.io/opengovernment-uk/"
LICENCE = "Contains public sector information licensed under the Open Government Licence v3.0, via OpenGovernment UK"
_cache = {}


def _base():
    b = os.environ.get("OGUK_DATA", SITE)
    if not (b.startswith("https://") or pathlib.Path(b).is_dir()): raise ValueError("OGUK_DATA must be an https address or a folder")
    return b


def _read(rel):
    """One published file, by its path under the site (an allowlist: no other paths are read)."""
    if not re.fullmatch(r"(data/)?[a-z0-9.-]+\.(json|jsonld|csv)", rel): raise ValueError(f"not a published file: {rel}")
    if rel in _cache: return _cache[rel]
    b = _base()
    if b.startswith("https://"):
        req = urllib.request.Request(b.rstrip("/") + "/" + rel, headers={"User-Agent": "opengovernment-uk-mcp/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r: text = r.read().decode("utf-8")  # noqa: S310  https only, fixed base
    else:
        root = pathlib.Path(b).resolve(); p = (root / rel).resolve()
        if root not in p.parents: raise ValueError("path outside the data folder")
        text = p.read_text(encoding="utf-8")
    _cache[rel] = text
    return text


def _json(rel): return json.loads(_read(rel))
def _csv(rel): return list(csv.DictReader(io.StringIO(_read(rel))))
def _cite(rel): return {"file": SITE + rel, "licence": LICENCE}
def _clean(q, n=200): return str(q or "").strip()[:n]


def search_bodies(query, limit=10):
    """Find public bodies by name or register key. Returns key, name, family and whether it is open."""
    q = _clean(query).lower()
    if not q: return {"results": [], **_cite("data/search-index.json")}
    rows = _json("data/search-index.json")
    hits = sorted((r for r in rows if q in r[1].lower() or q in r[0].lower()), key=lambda r: (not r[1].lower().startswith(q), not r[3], r[1]))[:max(1, min(int(limit), 50))]
    return {"results": [{"key": r[0], "name": r[1], "family": r[2], "open": bool(r[3]), "page": SITE + "index.html#org-" + re.sub(r"[^A-Za-z0-9-]", "", r[0].replace(":", "--"))} for r in hits], **_cite("data/search-index.json")}


def _find(key_or_name):
    k = _clean(key_or_name)
    rows = _csv("data/register.csv")
    return next((r for r in rows if r["id"] == k), None) or next((r for r in rows if r["name"].lower() == k.lower()), None)


def get_body(key_or_name):
    """One body's record: kind, status, nations, parents, dates, website, worked-out purpose and activity, identifiers."""
    r = _find(key_or_name)
    if not r: return {"error": "No body with that key or exact name. Use search_bodies first."}
    return {"body": r, "note": "purpose, activity and reach are worked out from the body's kind, name and description, so a few may be wrong", **_cite("data/register.csv")}


def who_answers(key_or_name):
    """Who a body answers to in the end, and the chain of links, each with its relation and source."""
    k = _clean(key_or_name)
    rows = _csv("accountable-owner.csv")
    r = next((x for x in rows if x["id"] == k), None) or next((x for x in rows if x["name"].lower() == k.lower()), None)
    if not r: return {"error": "No accountability chain for that key or exact name. Use search_bodies first."}
    return {"body": r["name"], "accountable_owner": r["accountable_owner"], "answers_to": r["answerable_to"], "chain": r["chain"], "sources_agreeing": r["sources_agreeing"], **_cite("accountable-owner.csv")}


def uk_and_country(country):
    """The UK's trade agreement in effect, tax treaty, Commonwealth membership and treaty count with one country."""
    c = _clean(country, 80).lower()
    for n in _json("data/international.jsonld")["@graph"]:
        if n.get("@type") == "schema:Country" and n.get("schema:name", "").lower() == c:
            return {"country": n["schema:name"], "commonwealth_member": n.get("og:commonwealthMember"), "treaties": n.get("og:treatyCount"),
                    "trade_agreements_in_effect": [t["schema:name"] for t in n.get("og:tradeAgreementInEffect", [])], "tax_treaties": [t["@id"] for t in n.get("og:taxTreaty", [])], **_cite("data/international.jsonld")}
    return {"error": "No country by that name in the register's international data."}


def source_status():
    """When each source was read, whether it is current, and what could not be read and why."""
    s = _json("data/source-status.json")
    return {"as_of": s["as_of"], "sources": [{k: x[k] for k in ("name", "read", "status", "official")} for x in s["sources"]], "not_read": s["not_read"], **_cite("data/source-status.json")}


def crosswalk(concept=""):
    """How a register field maps to BODS, FollowTheMoney, ORG and schema.org, Wikidata, org-id and OpenCorporates."""
    d = _json("data/crosswalks.json"); c = _clean(concept, 80).lower()
    rows = [r for r in d["rows"] if not c or c in r["concept"].lower()]
    return {"columns": d["columns"], "rows": rows, **_cite("data/crosswalks.json")}


def list_datasets():
    """Every published file with its title, format and licence, from the DCAT catalogue."""
    g = _json("data/catalogue.jsonld")
    ds = next(x for x in g["@graph"] if "dcat:dataset" in x)["dcat:dataset"] if "@graph" in g else g.get("dcat:dataset", [])
    out = []
    for d in ds:
        for dist in d.get("dcat:distribution", []) if isinstance(d.get("dcat:distribution"), list) else [d.get("dcat:distribution", {})]:
            out.append({"title": d.get("dct:title"), "file": (dist.get("dcat:downloadURL") or {}).get("@id"), "format": dist.get("dcat:mediaType")})
    return {"datasets": out, **_cite("data/catalogue.jsonld")}


TOOLS = [search_bodies, get_body, who_answers, uk_and_country, source_status, crosswalk, list_datasets]
