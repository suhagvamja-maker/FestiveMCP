# GoKwik D2C Festive Benchmark — remote MCP server

Remote MCP connector that lets Claude users query GoKwik's festive D2C category benchmarks and combine them
with their own data (typically the Meta Ads connector) for personalised recommendations.

## Layout
- `data/benchmarks.json` — the dataset (12 categories). Source: Google Sheet "Festive Report 2026 Raw Data".
- `logic.py` — all calculations (lookups, brand-vs-benchmark, RTO-adjusted ROAS, playbook). Pure Python, no MCP.
- `server.py` — MCP server (official `mcp` SDK v2, `MCPServer`), Streamable HTTP at `/mcp`, stateless, authless.
  `/health` for the host's health check.
- `scripts/sync_from_xlsx.py` — refresh the JSON from an .xlsx download of the sheet.
- `scripts/build_data.py` — original hand-transcription (kept for reference; prefer sync_from_xlsx).
- `tests/e2e_test.py` — starts nothing; calls every tool against a running server.

## Commands
- Setup: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Run: `python server.py` (port from $PORT, default 8000)
- Test: in a second terminal `python tests/e2e_test.py` (or pass a deployed URL ending in /mcp)
- Inspect interactively: `npx @modelcontextprotocol/inspector` → Streamable HTTP → http://localhost:8000/mcp
- Deploy: push to `main`; Render auto-deploys via `render.yaml`.

## Rules
- Note: `mcp` is pinned to 2.x, where FastMCP is renamed `MCPServer` (`mcp.server.mcpserver`). Don't use v1 examples.
- Keep tool outputs aggregated. Never add merchant names, IDs, emails, phone numbers or any PII to the data.
- Never commit secrets or API keys. If auth is added later, read secrets from environment variables.
- Do not switch to live Google Sheets reads; the data is a seasonal report and a bundled JSON is deliberate.
- Validation errors must raise `ValueError` in logic.py (server.py converts them to `ToolError` so Claude sees them).
- Every metric must have a definition in `logic.METRICS`; keep the "different funnel" warnings for Meta comparisons.
- Run `tests/e2e_test.py` against a local server before every push.
