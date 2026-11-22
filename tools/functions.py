"""Flag bodies that run government's own central and back-office functions, in two distinct classes:

  A  back-office body       exists to run a function for government itself (Government Property Agency, UK Shared Business Services)
  B  back-office line       a public-facing body that also runs a cross-government back-office service as one line of business

The function list is the Government Functional Standards collection on GOV.UK, read 22 November 2026
(https://www.gov.uk/government/collections/functional-standards): GovS 001 defines the functions; there is no GovS 012.
Legal, Policy and Science and engineering are recognised cross-government functions without a standard.
Evidence: the body's own GOV.UK name, type and description (GOV.UK content API). Every flag records its basis; a body that
no rule decides is left unflagged, never guessed. Advisory bodies advise government; they are not back office and are excluded."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FUNCTIONS = {
    "GovS 002": ("Project delivery", r"project delivery|major projects|infrastructure and projects|service transformation authority|programme delivery"),
    "GovS 003": ("People", r"\bpeople (function|group)\b|human resources|\bhr\b|recruitment|civil service (learning|careers|hr)|leadership college|payroll"),
    "GovS 004": ("Property", r"\bproperty\b|\bestates?\b(?! agents)|workplace"),
    "GovS 005": ("Digital", r"\bdigital\b|technology|\bit (services|business)\b|\bdata (quality|standards)\b"),
    "GovS 006": ("Finance", r"\bfinance (function|profession)|corporate finance|financial management|accounting|actuar"),
    "GovS 007": ("Security", r"\bsecurity (group|function|profession|vetting)|vetting|counter[- ]eavesdropping|technical security"),
    "GovS 008": ("Commercial", r"commercial|procure"),
    "GovS 009": ("Internal audit", r"internal audit"),
    "GovS 010": ("Analysis", r"analysis|statistic|geograph|economic service|operational research|social research|data quality hub"),
    "GovS 011": ("Communication", r"communication service|communications? (function|profession)"),
    "GovS 013": ("Counter fraud", r"fraud"),
    "GovS 014": ("Debt", r"\bdebt\b"),
    "GovS 015": ("Grants", r"\bgrants? (management|function|centre)"),
    "Legal": ("Legal", r"\blegal (department|profession|services)|government lawyers"),
    "Policy": ("Policy", r"policy profession"),
    "Science and engineering": ("Science and engineering", r"science and engineering profession"),
}
INTERNAL_NAME = re.compile(r"^(government|crown commercial|civil service|uk shared business services|central digital|public sector fraud|national security and intelligence|uk national authority for counter|leadership college|defence business services)|\bprofession$", re.I)
FOR_GOVERNMENT = re.compile(r"(for|to|across|on behalf of|serving) (the )?(central )?(government|other government departments|government departments|departments|the civil service|the public sector|public sector (bodies|organisations))\b|shared services|cross-government|in-house", re.I)
ADVISORY = re.compile(r"advisory", re.I)
ADVICE = re.compile(r"\badvi[cs]e|recommendations?\b|independent (scientific )?committee", re.I)
BO_MAP = [(r"payroll|pensions? administration|human resources|\bhr\b", "GovS 003"), (r"payments?|finance|accounting", "GovS 006"), (r"procure", "GovS 008"),
          (r"it services|technology", "GovS 005"), (r"debt", "GovS 014"), (r"fraud", "GovS 013"), (r"estates? management", "GovS 004"), (r"legal services", "Legal")]
# B needs the body's own words to say it PROVIDES back-office services to government or the public sector
SERVICE = re.compile(r"shared service|provid\w*[^.]{0,80}(services?|support)[^.]{0,60}\b(to|for|across)\b[^.]{0,20}(government|departments|public sector|nhs|civil service|public bodies|public authorities)|central services", re.I)
BACK_OFFICE_WORDS = re.compile(r"payroll|pensions? administration|payments?|procure|hr\b|human resources|finance|it services|business services|central services|debt|fraud|estates? management|legal services", re.I)

def classify_function(body: dict) -> tuple[str | None, str | None, str]:
    """Return (class, function code, basis). class is "A", "B" or None.
    body: name, kind (GOV.UK format), description (GOV.UK), open (bool)."""
    name, kind, desc = body.get("name", ""), body.get("kind", ""), body.get("description", "") or ""
    if ADVISORY.search(kind) or not body.get("open", True): return None, None, "advisory or closed: not back office"
    text = f"{name}. {desc}"
    hits = [(code, label) for code, (label, pat) in FUNCTIONS.items() if re.search(pat, text, re.I)]
    if not hits and SERVICE.search(desc) and not ADVICE.search(desc):  # service words map to their functional standard
        for pat, code in BO_MAP:
            if re.search(pat, desc, re.I): hits = [(code, FUNCTIONS[code][0])]; break
        if not hits and BACK_OFFICE_WORDS.search(desc):
            return "B", "Not stated", "public-facing body whose own GOV.UK description says it provides central services to government or the public sector, without naming the function"
    if not hits: return None, None, "no government function named in its GOV.UK name or description"
    code, label = hits[0]
    if INTERNAL_NAME.search(name):
        return "A", code, f"name is government-internal and names the {label} function"
    if SERVICE.search(desc) and BACK_OFFICE_WORDS.search(desc) and not ADVICE.search(desc):
        return "B", code, f"public-facing body whose own GOV.UK description says it provides {label.lower()} services to government or the public sector"
    return None, code, f"names the {label} function but not as a back-office service to government"

if __name__ == "__main__":
    desc = json.loads(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "sources" / "govuk-descriptions.json").read_text())
    orgs = {o["details"]["slug"]: o for o in json.loads((ROOT / "sources" / "govuk-organisations.json").read_text())}
    base = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources" / "opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    slug2id = {r[10].get("govuk_slug"): r[0] for r in base["r"] if r[10].get("govuk_slug")}
    out = []
    for slug, d in desc.items():
        o = orgs[slug]; cls, code, basis = classify_function({"name": o["title"], "kind": o["format"], "description": d, "open": o["details"].get("govuk_status") != "closed"})
        if cls: out.append({"id": slug2id.get(slug, ""), "slug": slug, "name": o["title"], "govuk_type": o["format"], "class": cls, "function": code, "function_name": FUNCTIONS.get(code, ("not stated",))[0], "basis": basis, "description": d})
    out.sort(key=lambda x: (x["class"], x["function"], x["name"]))
    (ROOT / "data" / "back-office.json").write_text(json.dumps({"source": "GOV.UK organisations and their content descriptions", "functions": {k: v[0] for k, v in FUNCTIONS.items()}, "bodies": out}, indent=1, ensure_ascii=False))
    for x in out: print(x["class"], f'{x["function"]:24}', x["name"][:50], "|", x["govuk_type"])
    print("A", sum(x["class"] == "A" for x in out), "B", sum(x["class"] == "B" for x in out))
