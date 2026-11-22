"""Developer hub -> docs/developers.html, docs/openapi.json, docs/data/crosswalks.json and docs/data/crosswalks.csv

One place for anyone who wants to use the data: what to do first, how to connect (the published files are the API: no
keys, open to any website, cacheable), how to harvest, field-by-field crosswalks, the MCP connector and agent
instructions, plugins and add-ons, test cases and validators, licensing, and how to contribute. Every file links back
to the repository.

Checked on every build:
  - every crosswalk cell against the real thing: register columns against the published CSVs; BODS paths and identifier
    schemes against docs/bods-0.4.json; FollowTheMoney properties against its compiled model and register.ftm.json;
    ORG and schema.org terms against register.jsonld; Wikidata properties against labels read from Wikidata;
    OpenCorporates fields against the converter that reads them;
  - every OpenAPI path is a published file; every local link on the page exists; the MCP tools listed are the ones
    integrations/mcp/core.py provides.

  python tools/devhub.py             build and check
  python tools/devhub.py --negative  prove the checks fail when they should
"""
import csv, html, io, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "integrations/mcp"))
import design  # noqa: E402
import core  # noqa: E402  the MCP connector's own functions, so the page lists exactly what it offers

SITE = "https://cyberdudeuk.github.io/opengovernment-uk/"
REPO = "https://github.com/cyberdudeuk/opengovernment-uk"
BLOB = REPO + "/blob/main/"
TREE = REPO + "/tree/main/"
E = html.escape


# ---------- crosswalks ----------
def crosswalk_problems(cw):
    e = []
    heads = {f: next(csv.reader(open(DOCS / p, newline=""))) for f, p in (("register.csv", "data/register.csv"), ("concordance.csv", "concordance.csv"))}
    bods = json.loads((DOCS / "bods-0.4.json").read_text())
    ent = [s["recordDetails"] for s in bods if s["recordType"] == "entity"]; rel = [s for s in bods if s["recordType"] == "relationship"]
    schemes = {i.get("scheme") for x in ent for i in x.get("identifiers", [])} | {i.get("schemeName") for x in ent for i in x.get("identifiers", [])}
    model = json.loads((ROOT / "vendor/followthemoney/defaultModel.json").read_text())["schemata"]
    ftm_used = {}
    for ln in (DOCS / "data/register.ftm.json").read_text().splitlines():
        if ln.strip():
            x = json.loads(ln)
            for k in x["properties"]: ftm_used.setdefault(x["schema"], set()).add(k)
    terms = {k for x in json.loads((DOCS / "data/register.jsonld").read_text())["@graph"] for k in x}
    wd = json.loads((ROOT / "sources/evidence/wikidata-properties.json").read_text())["labels"]
    ocf = set(cw["evidence"]["opencorporates_fields"]["names"])
    for r in cw["rows"]:
        c = r["concept"]
        if r["register"]:
            f, _, col = r["register"].partition(":")
            if col not in heads.get(f, []): e.append(f"{c}: register column {r['register']} not published")
        b = r["bods"]
        if b:
            m = re.fullmatch(r"recordDetails\.identifiers\[(scheme|schemeName)=(.+)\]", b)
            if m: ok = m.group(2) in schemes
            elif b.startswith("relationship: "):
                path = re.sub(r"\[\]", "", b[len("relationship: "):]).split(".")
                def has(o, ks):
                    if not ks: return True
                    if isinstance(o, list): return any(has(i, ks) for i in o)
                    return isinstance(o, dict) and ks[0] in o and has(o[ks[0]], ks[1:])
                ok = any(has(s["recordDetails"], path) for s in rel)
            elif b == "source": ok = all("source" in s for s in bods)
            else: ok = any(b.split(".")[-1] in x for x in ent) if b.startswith("recordDetails.") else False
            if not ok: e.append(f"{c}: BODS {b} not found in the published file")
        if r["ftm"]:
            sc, _, pr = r["ftm"].partition(".")
            props = {}
            for anc in model.get(sc, {}).get("schemata", []): props.update(model[anc].get("properties", {}))
            if pr not in props: e.append(f"{c}: FollowTheMoney {r['ftm']} is not in its model")
            elif pr not in ftm_used.get(sc, set()): e.append(f"{c}: FollowTheMoney {r['ftm']} is in the model but not in register.ftm.json")
        if r["jsonld"] and r["jsonld"] not in terms: e.append(f"{c}: {r['jsonld']} is not used in register.jsonld")
        if r["wikidata"] and r["wikidata"] not in wd: e.append(f"{c}: Wikidata {r['wikidata']} has no label read back")
        if r["orgid"] and r["orgid"] not in schemes: e.append(f"{c}: org-id scheme {r['orgid']} not in the BODS file")
        if r["opencorporates"] and not set(r["opencorporates"].split("/")) <= ocf: e.append(f"{c}: OpenCorporates field {r['opencorporates']} not seen in the converter")
    return e


def publish_crosswalks(cw):
    (DOCS / "data/crosswalks.json").write_text(json.dumps(cw, indent=1, ensure_ascii=False) + "\n")
    buf = io.StringIO(); w = csv.writer(buf, lineterminator="\n")
    w.writerow(["concept"] + [k for k, _ in cw["columns"]] + ["note"])
    for r in cw["rows"]: w.writerow([r["concept"]] + [r[k] for k, _ in cw["columns"]] + [r["note"]])
    (DOCS / "data/crosswalks.csv").write_text(buf.getvalue())


# ---------- the published files as an API (OpenAPI 3.1) ----------
ENDPOINTS = [  # path, format, what it holds
    ("data/catalogue.jsonld", "application/ld+json", "DCAT catalogue of every dataset and download: start here"),
    ("data/register.csv", "text/csv", "The register: one row per body, with every register code"),
    ("data/register.jsonld", "application/ld+json", "The register as linked data (W3C ORG and schema.org)"),
    ("data/register.ftm.json", "application/json", "The register in FollowTheMoney, one entity per line"),
    ("bods-0.4.json", "application/json", "Ownership and control as BODS 0.4 statements"),
    ("accountable-owner.csv", "text/csv", "Who each body answers to in the end, with the chain"),
    ("edges.csv", "text/csv", "Every accountability link with its source"),
    ("concordance.csv", "text/csv", "Each body's codes in other registers"),
    ("data/international.jsonld", "application/ld+json", "International bodies, memberships, treaties, agreements, countries"),
    ("data/taxonomies.skos.jsonld", "application/ld+json", "The classifications as SKOS concept schemes"),
    ("data/crosswalks.json", "application/json", "Field-by-field crosswalks to other standards"),
    ("data/source-status.json", "application/json", "How each source stands: read, current, not read and why"),
    ("data/alerts.json", "application/json", "Notifications and latest changes"),
    ("data/search-index.json", "application/json", "Every body's key, name, family and status, for search"),
    ("data/provenance.jsonld", "application/ld+json", "Where each build's data came from, with fingerprints"),
    ("datapackage.json", "application/json", "Frictionless data package describing the CSV files"),
    ("opengovernment-uk.db", "application/vnd.sqlite3", "Every table in one SQLite file"),
]


def openapi():
    paths = {}
    for p, mt, what in ENDPOINTS:
        op = re.sub(r"[^a-zA-Z0-9]+", "_", p).strip("_")
        paths["/" + p] = {"get": {"operationId": f"get_{op}", "summary": what, "tags": ["open data"],
                                  "responses": {"200": {"description": what, "headers": {"ETag": {"schema": {"type": "string"}}, "Last-Modified": {"schema": {"type": "string"}}},
                                                        "content": {mt: {"schema": {"type": "string", "format": "binary"} if "sqlite" in mt else ({"type": "string"} if mt == "text/csv" else {"type": "object"})}}},
                                                "304": {"description": "Not modified since the ETag or date you sent"}}}}
    return {"openapi": "3.1.0", "info": {"title": "OpenGovernment UK open data", "version": "1.0.0",
            "description": "The register's published files, read over plain HTTPS GET. No key, no sign-in, no rate limit stated by the host; open to any website (Access-Control-Allow-Origin: *). Send If-None-Match or If-Modified-Since to avoid downloading unchanged files. A pilot, not an official list.",
            "license": {"name": "Open Government Licence v3.0", "url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"}},
            "servers": [{"url": SITE.rstrip("/")}], "externalDocs": {"description": "Developer hub", "url": SITE + "developers.html"}, "paths": paths}


# ---------- the page ----------
def code(text, lang=""):
    return f'<div class="dv-code"><button type="button" class="dv-copy">Copy</button><pre><code class="{E(lang)}">{E(text)}</code></pre></div>'


def table(head, rows):
    return '<div class="dv-tw"><table class="dv-t"><thead><tr>' + "".join(f"<th scope=\"col\">{h}</th>" for h in head) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>"


def a(href, text, ext=None):
    ext = href.startswith("http") if ext is None else ext
    return f'<a href="{E(href)}"' + (' rel="noopener" target="_blank"' if ext else "") + f">{E(text)}" + ('<span class="sr-only"> (opens in a new tab)</span>' if ext else "") + "</a>"


def page(cw):
    reg = SITE + "data/register.csv"
    TASKS = [  # the decision tree: what do you want to do?
        ("Look something up", "A person or an agent answering a question about one body.", [("Search from the masthead on any page, or the register", "index.html#register"), ("Ask an AI assistant with the MCP connector", "#tab=mcp"), ("Ask a question on the portal", "index.html#ask")]),
        ("Analyse the data", "Counts, joins and charts across all bodies.", [("Open the SQLite file in Datasette Lite (nothing to install)", "https://lite.datasette.io/?url=" + SITE + "opengovernment-uk.db"), ("Read the CSVs into Python, R, DuckDB or a spreadsheet", "#tab=connect"), ("Check what each field means", BLOB + "documentation/solution/10-data-dictionary.md")]),
        ("Join it to your own data", "Match your records to UK public bodies by a code you already hold.", [("Find the field in the crosswalks", "#tab=crosswalks"), ("Use the concordance of codes", "concordance.csv"), ("Download the register", "data/register.csv")]),
        ("Harvest it into a catalogue or portal", "Keep a copy in step automatically.", [("Start from the DCAT catalogue", "data/catalogue.jsonld"), ("Follow the harvesting guide", "#tab=harvest"), ("Watch for changes", "data/alerts.json")]),
        ("Load it into an investigative or compliance tool", "OpenSanctions, OpenAleph, yente, BODS tools.", [("FollowTheMoney file", "data/register.ftm.json"), ("BODS 0.4 file", "bods-0.4.json"), ("How the fields map", "#tab=crosswalks")]),
        ("Build an agent or connector", "Give an AI assistant reliable, cited answers.", [("Run the MCP connector", "#tab=mcp"), ("Agent instructions and known-answer questions", BLOB + "agent/SKILL.md"), ("llms.txt", "llms.txt")]),
        ("Test a converter", "Check your BODS or FollowTheMoney code handles public bodies.", [("Public-sector test cases", TREE + "tests/fixtures/bods/public-sector"), ("Validators and checks", "#tab=test")]),
        ("Contribute or correct", "Fix a fact, add a source, build an add-on.", [("Read the contributor charter", BLOB + "documentation/contributor-charter.md"), ("Report a correction", REPO + "/issues/new?template=data-correction.yml"), ("Ways to help", "#tab=contribute")]),
    ]
    start = '<div class="dv-tasks">' + "".join(f'<article class="dv-task"><h3>{E(t)}</h3><p>{E(d)}</p><ol>' + "".join(f"<li>{a(u, lbl)}</li>" for lbl, u in steps) + "</ol></article>" for t, d, steps in TASKS) + "</div>"
    connect = ("<p>The published files are the API. Read them with a plain HTTPS GET: no key, no sign-in, and any website can read them from the browser (the host sends <code>Access-Control-Allow-Origin: *</code>). "
               "Send <code>If-None-Match</code> with the ETag you last saw to get a quick <i>304 Not Modified</i> when nothing changed. Base address: <code>" + E(SITE) + "</code>.</p>"
               + table(["File", "Format", "What it holds"], [[a(p, p, False), E(mt), E(w)] for p, mt, w in ENDPOINTS])
               + "<p>" + a("openapi.json", "OpenAPI 3.1 description", False) + " of these files, for API tools and code generators.</p><h3>Recipes</h3>"
               + "<h4>Command line</h4>" + code(f"curl -sO {reg}\ncurl -s -H 'If-None-Match: \"<etag you saw>\"' -o /dev/null -w '%{{http_code}}\\n' {reg}", "shell")
               + "<h4>Python (standard library)</h4>" + code(f"import csv, io, urllib.request\nrows = list(csv.DictReader(io.StringIO(urllib.request.urlopen(\"{reg}\").read().decode())))\nprint(len(rows), rows[0][\"name\"])", "python")
               + "<h4>pandas or DuckDB</h4>" + code(f"import pandas as pd\nbodies = pd.read_csv(\"{reg}\")\n\n-- DuckDB\nSELECT kind, count(*) FROM read_csv_auto('{reg}') GROUP BY kind ORDER BY 2 DESC;", "python")
               + "<h4>JavaScript (browser or Node)</h4>" + code(f"const res = await fetch(\"{SITE}data/search-index.json\");\nconst bodies = await res.json(); // [key, name, family, open]\nconsole.log(bodies.filter(b => b[1].includes(\"Office\")).length);", "javascript")
               + "<h4>R</h4>" + code(f"bodies <- read.csv(\"{reg}\")\ntable(bodies$kind)", "r")
               + "<h4>Spreadsheets</h4>" + code(f"Google Sheets:  =IMPORTDATA(\"{reg}\")\nExcel:          Data > Get Data > From Web, then paste {reg}", ""))
    harvest = ("<ol class=\"dv-steps\">"
               "<li><b>Start from the catalogue.</b> " + a("data/catalogue.jsonld", "catalogue.jsonld", False) + " is W3C DCAT 3: every dataset, its download address, format, licence and the standard it follows. CKAN, data.gov.uk-style harvesters and most catalogues read it.</li>"
               "<li><b>Or follow the sitemap.</b> " + a("sitemap.xml", "sitemap.xml", False) + " lists every page and file; " + a("robots.txt", "robots.txt", False) + " allows all crawlers. Every page carries a schema.org Dataset in its head for dataset search engines.</li>"
               "<li><b>Describe the tables.</b> " + a("datapackage.json", "datapackage.json", False) + " (Frictionless) and " + a("data/register.csv-metadata.json", "CSVW metadata", False) + " give column names, types and keys.</li>"
               "<li><b>Keep in step cheaply.</b> Re-read on your own schedule with conditional requests (ETag or Last-Modified). " + a("data/alerts.json", "alerts.json", False) + " lists the latest changes; " + a("data/provenance.jsonld", "provenance.jsonld", False) + " lists every source with its fingerprint, so you can tell what changed.</li>"
               "<li><b>Know how fresh it is.</b> " + a("data/source-status.json", "source-status.json", False) + " says when each source was read and what could not be read. The register is rebuilt on demand, not on a fixed schedule.</li>"
               "<li><b>Keep the identifiers.</b> Each body is <code>" + E(SITE) + "id/&lt;register key&gt;</code>, for example <code>id/government-organisation:D9</code>. They are stable names; they do not yet open a page of their own.</li></ol>")
    cols = cw["columns"]
    def cell(k, v):
        if not v: return '<span class="dv-none" aria-label="no equivalent">–</span>'
        if k == "wikidata": return a(f"https://www.wikidata.org/wiki/Property:{v}", v)
        return "<code>" + E(v).replace(".", ".<wbr>").replace("[", "<wbr>[").replace("=", "=<wbr>").replace(":", ":<wbr>").replace("/", "/<wbr>") + "</code>"  # break at the joints, not mid-word
    cross = ("<p>How each field in the register maps to the standards and registers it is published in or joins to. Every cell is checked on every build against the real file or model, so the table can't drift from the data. A dash means there is no equivalent. The table scrolls sideways on smaller screens.</p>"
             + table(["Field"] + [E(t) for _, t in cols] + ["Note"], [[f"<b>{E(r['concept'])}</b>"] + [cell(k, r[k]) for k, _ in cols] + [E(r["note"])] for r in cw["rows"]])
             + "<p>Download: " + a("data/crosswalks.json", "crosswalks.json", False) + " · " + a("data/crosswalks.csv", "crosswalks.csv", False) + " · source and checks: " + a(BLOB + "sources/crosswalks.json", "sources/crosswalks.json") + ", " + a(BLOB + "tools/devhub.py", "tools/devhub.py") + "</p>"
             + "<h3>Where this export departs from a published mapping</h3><p>FollowTheMoney only lets an <code>Ownership</code> point at a company, so the UK's shares in international financial institutions are a <code>Membership</code> whose description gives the share of votes. Public-sector test case 20 sets this out for converter authors.</p>")
    tools = [(f.__name__, (f.__doc__ or "").strip().split("\n")[0]) for f in core.TOOLS]
    mcp = ("<p>A Model Context Protocol connector gives any MCP client (Claude, coding assistants, your own agent) cited answers from the published files. It runs on your own computer, needs no account and costs nothing; it is read-only and reads only the published files.</p>"
           + table(["Tool", "What it answers"], [[f"<code>{E(n)}</code>", E(d)] for n, d in tools])
           + "<h3>Set it up</h3><ol class=\"dv-steps\"><li>Get the code: " + a(REPO, "clone the repository") + " or download " + a(TREE + "integrations/mcp", "integrations/mcp") + ".</li>"
           "<li>Install its one dependency: " + code("pip install -r integrations/mcp/requirements.txt", "shell") + "</li>"
           "<li>Add it to your client. Claude Code:" + code("claude mcp add opengovernment-uk -- python integrations/mcp/server.py", "shell") + "Claude Desktop and other clients that use a JSON settings file:" + code(json.dumps({"mcpServers": {"opengovernment-uk": {"command": "python", "args": ["/path/to/opengovernment-uk/integrations/mcp/server.py"]}}}, indent=2), "json") + "</li>"
           "<li>Optional: set <code>OGUK_DATA</code> to a local copy of <code>docs/</code> to work offline.</li></ol>"
           + "<h3>Agents without MCP</h3><ul><li>" + a(BLOB + "agent/SKILL.md", "Agent instructions") + ": where each answer is and the rules for citing it, with " + a(BLOB + "agent/evals.json", "known-answer questions") + " checked on every build.</li><li>" + a("llms.txt", "llms.txt", False) + ": a plain guide to every page and file.</li><li>The portal's own " + a("index.html#ask", "Ask", False) + " answers only from the register, in your browser.</li></ul>")
    plugins = table(["Add-on", "What you get", "How"], [
        ["Datasette Lite", "Filter, facet and run SQL on every table in your browser", a("https://lite.datasette.io/?url=" + SITE + "opengovernment-uk.db", "Open the register in Datasette Lite")],
        ["Google Sheets", "A live sheet of every body", f"<code>=IMPORTDATA(\"{E(reg)}\")</code>"],
        ["Excel and Power BI", "A refreshable table", "Get Data, From Web, paste the address of any CSV"],
        ["OpenRefine", "Clean and match your own list against the register", "Create project, Web addresses, paste the register CSV address; match on a shared code column. A hosted reconciliation service would need a server, so it isn't offered"],
        ["SQLite tools", "Every table offline", a("opengovernment-uk.db", "Download the SQLite file", False)],
        ["Notebooks (Jupyter, Observable, Colab)", "Reproducible analysis", "Read any CSV or JSON address directly; see the recipes under Connect"],
        ["MCP clients", "Cited answers inside your AI assistant", a("#tab=mcp", "MCP connector", False)],
        ["Build your own", "Your add-on, listed here", a(REPO + "/issues/new?template=reuse.yml", "Tell us about it") + " once it has a public page and repository"]])
    test = ("<ul><li>" + a(TREE + "tests/fixtures/bods/public-sector", "Public-sector BODS test cases") + ": a state's shares in an international body; control by law; sponsorship in an extension. Each has a statement of correct handling, in the shared fixture pack's layout.</li>"
            "<li><b>BODS:</b> the file is checked against the official schema and Open Ownership's lib-cove-bods on every build:" + code("pip install libcovebods\nlibcovebods jsv bods-0.4.json && libcovebods pv bods-0.4.json", "shell") + "</li>"
            "<li><b>FollowTheMoney:</b> every entity is checked against FollowTheMoney's own compiled model (" + a(BLOB + "tools/ftm_export.py", "tools/ftm_export.py") + ").</li>"
            "<li><b>Agent answers:</b> " + a(BLOB + "tools/agent_evals.py", "tools/agent_evals.py") + " answers the known questions from the published files.</li>"
            "<li><b>Everything:</b> the " + a(BLOB + ".github/workflows/ci.yml", "checks workflow") + " runs every check, each with a test that proves it fails when it should.</li></ul>")
    lic = (table(["You want to", "You may", "Condition"], [
        ["Copy, publish or share the data", "Yes, commercially or not", "Attribute (below)"], ["Adapt it, combine it with other data", "Yes", "Attribute; don't imply endorsement"],
        ["Reuse the code", "Yes (MIT)", "Keep the copyright notice"], ["Reuse the documentation, test cases' expectations", "Yes (CC BY 4.0)", "Attribute"],
        ["Say a public body endorses your use", "No", "Neither this project nor any public body endorses reuse"]])
        + "<p>Attribution to use: <q>Contains public sector information licensed under the Open Government Licence v3.0, via OpenGovernment UK.</q></p>"
        + "<p>Each file's licence: " + a("data/LICENCES.md", "LICENCES.md", False) + " (machine-readable in " + a(BLOB + "REUSE.toml", "REUSE.toml") + "). Some facts come from sources with their own terms, for example Wikidata (CC0) and GLEIF (CC0); each source is named in " + a("data/provenance.jsonld", "provenance.jsonld", False) + ". OpenSanctions data (CC BY-NC 4.0) is linked to, never copied in.</p>")
    contrib = ("<p>This is a public good, and it gets better when people who know a part of the state correct it. The " + a(BLOB + "documentation/contributor-charter.md", "contributor charter") + " says what we promise each other.</p>"
               + table(["You can", "How", "Credit"], [
                   ["Correct a fact", a(REPO + "/issues/new?template=data-correction.yml", "Data correction form") + ", citing the official source", "Named (by your choice of handle) in the release notes and CONTRIBUTORS"],
                   ["Suggest a source", a(REPO + "/issues/new?template=feedback.yml", "Feedback form") + " with its address and licence", "As above, and the source page names who found it"],
                   ["Add a test case or crosswalk row", "A pull request against " + a(BLOB + "sources/crosswalks.json", "sources/crosswalks.json") + " or the test cases", "CONTRIBUTORS and the citation file, if you opt in"],
                   ["Build an add-on or integration", "Build on the files or the MCP connector, then " + a(REPO + "/issues/new?template=reuse.yml", "tell us"), "Listed on this page and in CONTRIBUTORS, with a link"],
                   ["Become a steward", "Look after a family of bodies or a nation: review corrections for it", "Named as steward for that area"]])
               + "<p>" + a(BLOB + "CONTRIBUTING.md", "How to contribute") + " · " + a(BLOB + "CONTRIBUTORS.md", "Contributors") + " · " + a(BLOB + "CODE_OF_CONDUCT.md", "Code of conduct") + " · " + a(REPO + "/issues", "Open issues") + "</p>")
    TABS = [("start", "Start here", start), ("connect", "Connect", connect), ("harvest", "Harvest", harvest), ("crosswalks", "Crosswalks", cross), ("mcp", "MCP and agents", mcp), ("plugins", "Plugins and add-ons", plugins), ("test", "Test and validate", test), ("licensing", "Licensing", lic), ("contribute", "Contribute", contrib)]
    css = (".dv{max-width:1200px;margin:0 auto;padding:1.5rem 1.25rem 3rem}.dv h1{margin:0 0 .5rem}.dv .lede{max-width:70ch;color:var(--og-muted)}"
           ".dv-tabs{display:flex;flex-wrap:wrap;gap:.5rem;margin:1.25rem 0 1rem;padding:.5rem;background:var(--og-surface-2);border-radius:var(--og-radius-md)}"
           ".dv-tabs button{min-height:var(--og-target-min);padding:0 1rem;border:1px solid var(--og-line);border-radius:var(--og-radius-pill);background:var(--og-surface);color:var(--og-ink);font:inherit;font-weight:600;cursor:pointer}"
           ".dv-tabs button[aria-selected=\"true\"]{background:var(--og-ink);color:var(--og-surface);border-color:var(--og-ink)}"
           ".dv-panel{background:var(--og-surface);border:1px solid var(--og-line);border-radius:var(--og-radius-md);padding:1.25rem}"
           "#devhub [hidden]{display:none!important}"
           ".dv-tasks{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem}.dv-task{border:1px solid var(--og-line);border-radius:var(--og-radius-md);padding:1rem}.dv-task h3{margin:0 0 .25rem!important;font-size:1.05rem!important}.dv-task p{margin:0 0 .5rem;color:var(--og-muted)}.dv-task ol{margin:0;padding-left:1.25rem}"
           ".dv-tw{position:relative;overflow-x:auto;margin:.75rem 0}.dv-t{border-collapse:collapse;width:100%;font-size:.9rem}.dv-t th,.dv-t td{border-bottom:1px solid var(--og-line);padding:.5rem;text-align:left;vertical-align:top}.dv-t th{background:var(--og-surface-2)}.dv-t code{overflow-wrap:normal;word-break:normal}.dv-t td:first-child{min-width:8rem}"
           ".dv-none{color:var(--og-muted)}.dv-steps li{margin:.5rem 0}"
           ".dv-code{position:relative;margin:.5rem 0}.dv-code pre{margin:0;padding:.75rem;padding-right:4.5rem;overflow-x:auto;background:var(--og-surface-2);border:1px solid var(--og-line);border-radius:var(--og-radius-sm);font-family:var(--og-font-mono);font-size:.85rem}"
           ".dv-copy{position:absolute;top:.35rem;right:.35rem;min-height:2rem;padding:0 .6rem;border:1px solid var(--og-line);border-radius:var(--og-radius-pill);background:var(--og-surface);color:var(--og-ink);font:inherit;font-size:.8rem;cursor:pointer}"
           ".dv-repo{display:flex;flex-wrap:wrap;gap:.75rem;margin:.75rem 0 0}")
    js = ("(()=>{const T=[...document.querySelectorAll('.dv-tabs [role=tab]')],P=id=>document.getElementById('dv-'+id);"
          "const show=(id,push)=>{if(!P(id))id='start';T.forEach(t=>{const on=t.dataset.t===id;t.setAttribute('aria-selected',on);t.tabIndex=on?0:-1;P(t.dataset.t).hidden=!on});if(push)history.replaceState(null,'','#tab='+id)};"
          "const fromHash=()=>{const m=location.hash.match(/tab=([a-z]+)/);show(m?m[1]:'start',false)};"
          "T.forEach((t,i)=>{t.addEventListener('click',()=>show(t.dataset.t,true));t.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const n=T[(i+(e.key==='ArrowRight'?1:T.length-1))%T.length];n.focus();show(n.dataset.t,true)}})});"
          "addEventListener('hashchange',fromHash);fromHash();"
          "document.addEventListener('click',e=>{const b=e.target.closest('.dv-copy');if(!b)return;const t=b.nextElementSibling.textContent;(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1500)}).catch(()=>{b.textContent='Select and copy'})})})();")
    body = ('<main class="dv" id="devhub"><span class="eyebrow">Developer hub</span><h1>Use the data</h1>'
            '<p class="lede">Everything you need to connect to, harvest, crosswalk, test and build on the register: no key, no sign-in, no cost. Every fact cites its source, every file has a licence, and every check runs in the open.</p>'
            '<p class="dv-repo">' + a(REPO, "Repository on GitHub") + a(BLOB + "documentation/interoperability-lessons.md", "What we adopted from other projects") + a(BLOB + "documentation/contributor-charter.md", "Contributor charter") + '</p>'
            '<div class="dv-tabs" role="tablist" aria-label="Developer hub sections">' + "".join(f'<button type="button" role="tab" id="dvt-{k}" data-t="{k}" aria-controls="dv-{k}" aria-selected="false" tabindex="-1">{E(t)}</button>' for k, t, _ in TABS) + "</div>"
            + "".join(f'<section class="dv-panel" role="tabpanel" id="dv-{k}" aria-labelledby="dvt-{k}" hidden><h2>{E(t)}</h2>{c}</section>' for k, t, c in TABS) + "</main>")
    doc = (f'<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Developer hub · OpenGovernment UK</title>'
           f'<meta name="description" content="Connect to, harvest, crosswalk, test and build on the open register of the UK state."><style>{css}</style></head><body>{body}<footer></footer><script>{js}</script></body></html>')
    return design.wrap_page(doc, "devs")


def page_problems(h):
    e = []
    for u in re.findall(r'href="([^"#:]+)"', h):
        if not u.startswith(("http", "mailto")) and u.split("#")[0] != "developers.html" and not (DOCS / u.split("#")[0]).exists(): e.append(f"developers.html links to a file that is not published: {u}")
    for f in core.TOOLS:
        if f">{f.__name__}<" not in h: e.append(f"MCP tool {f.__name__} not listed")
    if "#devhub [hidden]{display:none!important}" not in h: e.append("hidden panels may show (OG-D63 class)")
    return e


def main():
    cw = json.loads((ROOT / "sources/crosswalks.json").read_text())
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(cw)); bad["rows"][1]["ftm"] = "PublicBody.flavour"; bad["rows"][2]["wikidata"] = "P9999999"; bad["rows"][3]["register"] = "register.csv:colour"
        n = len(crosswalk_problems(bad))
        if n < 3: sys.exit(f"devhub negative: only {n} of 3 bad cells caught")
        if not page_problems('<a href="no-such-file.json">x</a>'): sys.exit("devhub negative: a dead link was not caught")
        print("devhub negative: a made-up FollowTheMoney property, Wikidata property and register column are caught; so is a dead link"); return
    e = crosswalk_problems(cw)
    if e: sys.exit("devhub: " + "; ".join(e))
    publish_crosswalks(cw)
    (DOCS / "openapi.json").write_text(json.dumps(openapi(), indent=1) + "\n")
    missing = [p for p, *_ in ENDPOINTS if not (DOCS / p).exists()]
    if missing: sys.exit("devhub: OpenAPI lists files that are not published: " + ", ".join(missing))
    h = page(cw)
    e = page_problems(h)
    if e: sys.exit("devhub: " + "; ".join(e))
    (DOCS / "developers.html").write_text(h)
    print(f"devhub: {len(cw['rows'])} crosswalk rows checked, {len(ENDPOINTS)} files in the OpenAPI description, {len(core.TOOLS)} MCP tools listed")


if __name__ == "__main__":
    main()
