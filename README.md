# GoKwik D2C Festive Benchmark — MCP connector

A remote MCP server. Anyone adds its URL in Claude as a custom connector, then asks questions about GoKwik's
festive D2C benchmarks — alone, or together with their own Meta Ads data.

## Tools
| Tool | What it does |
|---|---|
| `list_categories` | Categories, metric definitions, data window, caveats |
| `get_category_benchmark` | Full profile for one category (accepts "skincare", "pet", "fashion"…) |
| `rank_categories` | Ranks all 12 categories on any metric |
| `get_festival_timeline` | Season dates and the two demand peaks |
| `compare_brand_to_benchmark` | Brand's numbers vs category, gaps, verdicts, prioritised recommendations |
| `rto_adjusted_roas` | Turns Meta ROAS into delivered-revenue ROAS using COD mix and RTO, plus a COD→prepaid what-if |

## Go-live steps (open this folder in Claude Code and say: "follow README go-live steps 2–3")
1. **Data sign-off (you).** The sheet's own note says the figures are estimates to sense-check before external
   sharing — a public connector is external sharing. Also check the "Others" rows in Basket Risk
   (63/21/12/4 and 32/30/24/28): they look like placeholder values.
2. **Push to GitHub (Claude Code can do this).** Private repo is fine.
3. **Deploy on Render (needs your login once).** render.com → New → Blueprint → select the repo → Apply.
   You get a URL like `https://gokwik-d2c-benchmark-mcp.onrender.com`. Check `/health` returns `{"ok":true}`.
4. **Add to Claude.** Settings → Connectors → Add custom connector → URL ending in `/mcp`.
   On a Team/Enterprise plan only an org Owner can add custom connectors.
5. **Test with Meta.** Enable this connector and the Meta Ads connector in one chat, then ask:
   > "My brand is in fashion. Pull my last 30 days from Meta Ads, compare me to the festive benchmark,
   > and tell me my RTO-adjusted ROAS and the top 3 things to fix before the sale week."

## Updating data
Download the sheet as .xlsx → `python scripts/sync_from_xlsx.py file.xlsx` → run tests → push. Render redeploys.

## Local run
```
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
python server.py                      # http://localhost:8000/mcp
python tests/e2e_test.py              # in a second terminal
```
