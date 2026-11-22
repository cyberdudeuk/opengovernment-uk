"""OpenGovernment UK MCP connector: answers about UK public bodies for any MCP client (Claude, IDEs, agents).

Run locally over stdio:  pip install -r integrations/mcp/requirements.txt && python integrations/mcp/server.py
Read-only. It reads only the files the portal publishes (see core.py), from the website or a local copy (OGUK_DATA).
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402  (mcp 2.x)
from mcp.types import ToolAnnotations  # noqa: E402

server = MCPServer("OpenGovernment UK", instructions=(
    "Answers about UK public bodies from OpenGovernment UK's open data: find a body, read its record, see who it answers to, "
    "the UK's agreements with a country, how each source stands, and how fields map to BODS, FollowTheMoney and other standards. "
    "A pilot, not an official list. Cite the file each answer gives. Purpose and activity are worked out, so a few may be wrong."))
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False, idempotentHint=True)
for fn in core.TOOLS:
    server.tool(annotations=READ_ONLY)(fn)

if __name__ == "__main__":
    server.run("stdio")
