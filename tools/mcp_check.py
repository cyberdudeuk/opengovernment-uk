"""Check the MCP connector's answers (integrations/mcp/core.py) against the published files in docs/, with known answers

Runs with no extra dependency (the connector's logic is standard-library Python). If the `mcp` package is installed,
it also starts the real server over stdio and lists its tools as a client would (skipped otherwise, and says so).

  python tools/mcp_check.py             run
  python tools/mcp_check.py --negative  prove the guards refuse what they should
"""
import os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ["OGUK_DATA"] = str(ROOT / "docs")
sys.path.insert(0, str(ROOT / "integrations/mcp"))
import core  # noqa: E402


def known():
    e = []
    s = core.search_bodies("met office")
    if not any(r["name"] == "Met Office" for r in s["results"]): e.append("search_bodies: no Met Office")
    if not s["licence"].startswith("Contains public sector information"): e.append("answers must carry the attribution")
    w = core.who_answers("Met Office")
    if w.get("accountable_owner") != "Department for Science, Innovation and Technology": e.append(f"who_answers: {w}")
    b = core.get_body("Met Office")
    if b.get("body", {}).get("id") != "government-organisation:EA46": e.append("get_body: wrong record")
    c = core.uk_and_country("Albania")
    if "UK-Albania Partnership, Trade and Cooperation Agreement" not in c.get("trade_agreements_in_effect", []): e.append("uk_and_country: Albania trade agreement")
    if not any(g["source"] == "International Monetary Fund" for g in core.source_status()["not_read"]): e.append("source_status: IMF not read")
    if not core.crosswalk("Legal Entity")["rows"]: e.append("crosswalk: LEI row")
    if not any((d["file"] or "").endswith("register.csv") for d in core.list_datasets()["datasets"]): e.append("list_datasets: register.csv")
    if "error" not in core.get_body("No such body anywhere"): e.append("get_body must answer an unknown body with an error, not a guess")
    return e


def negatives():
    caught = []
    for bad in ("../README.md", "data/../../etc/passwd", "index.html", "data/x.py"):
        try: core._read(bad); caught.append(False)
        except ValueError: caught.append(True)
    os.environ["OGUK_DATA"] = "http://example.com/"; core._cache.clear()
    try: core._base(); caught.append(False)
    except ValueError: caught.append(True)
    os.environ["OGUK_DATA"] = str(ROOT / "docs")
    return all(caught)


def live():
    try: import mcp  # noqa: F401
    except ImportError: return "skipped (mcp not installed; see integrations/mcp/requirements.txt)"
    import asyncio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    async def run():
        p = StdioServerParameters(command=sys.executable, args=[str(ROOT / "integrations/mcp/server.py")], env={**os.environ})
        async with stdio_client(p) as (r, w), ClientSession(r, w) as s:
            await s.initialize()
            names = sorted(t.name for t in (await s.list_tools()).tools)
            res = await s.call_tool("who_answers", {"key_or_name": "Met Office"})
            return names, str(res.content[0].text if res.content else res)
    names, text = asyncio.run(run())
    want = sorted(f.__name__ for f in core.TOOLS)
    if names != want: sys.exit(f"mcp live: tools {names} != {want}")
    if "Department for Science, Innovation and Technology" not in text: sys.exit(f"mcp live: who_answers gave {text[:200]}")
    return f"live server: {len(names)} tools listed and called over stdio"


def main():
    if "--negative" in sys.argv:
        if not negatives(): sys.exit("mcp negative: a path outside the published files or a non-https base was not refused")
        print("mcp negative: paths outside the published files and a non-https base are refused"); return
    e = known()
    if e: sys.exit("mcp: " + "; ".join(e))
    print(f"mcp: {len(core.TOOLS)} tools give the known answers from the published files; {live()}")


if __name__ == "__main__":
    main()
