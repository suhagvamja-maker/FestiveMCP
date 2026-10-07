"""GoKwik D2C Festive Benchmark — remote MCP server (Streamable HTTP, stateless, authless).

Run locally:   python server.py           -> http://localhost:8000/mcp
Health check:  GET /health
"""
from __future__ import annotations

import os

import uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse

import logic

INSTRUCTIONS = """\
GoKwik D2C Festive Benchmark: category-level checkout, payment-mix, RTO, basket, product and festive-lift
benchmarks from GoKwik's network of Indian D2C brands (Festive 2025 window, 22 Sep – 5 Nov 2025).

How to use with the brand's own data (e.g. a Meta Ads connector):
1. Identify the brand's category and call get_category_benchmark.
2. Pull the brand's own numbers from their other tools (Meta: spend, purchase ROAS, purchases, purchase value,
   region breakdown, daily spend over last festive season).
3. Call rto_adjusted_roas with the Meta ROAS. Meta counts orders when placed, including ones that later RTO,
   so Meta ROAS overstates delivered revenue for COD-heavy brands.
4. Call compare_brand_to_benchmark ONLY with metrics the brand actually has under the same definition.
   Do not map Meta's initiate-checkout→purchase rate onto checkout_completion_pct; they measure different funnels.
5. Present recommendations with the gap that triggered them, and state that benchmarks are directional.
Never invent a benchmark value that a tool did not return.
"""

mcp = MCPServer(
    name="gokwik-d2c-benchmark",
    title="GoKwik D2C Festive Benchmark",
    instructions=INSTRUCTIONS,
    version="0.1.0",
    website_url="https://www.gokwik.co",
)

def _safe(fn, *args, **kwargs):
    """Surface validation errors (unknown category/metric) to Claude so it can self-correct."""
    try:
        return fn(*args, **kwargs)
    except ValueError as e:
        raise ToolError(str(e)) from e


RO = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)


@mcp.tool(annotations=RO)
def list_categories() -> dict:
    """List the D2C categories covered, the data window, and dataset caveats. Call this first if unsure of the category."""
    return {"meta": logic.meta(), "categories": logic.list_categories(),
            "metrics": {k: {"label": v["label"], "unit": v["unit"], "definition": v["definition"]}
                        for k, v in logic.METRICS.items()}}


@mcp.tool(annotations=RO)
def get_category_benchmark(category: str) -> dict:
    """Full festive benchmark for one category: AOV, payment mix, COD/prepaid/blended RTO, checkout completion,
    cart abandonment, re-buy days, charm price, whale share, Tier-3 share and RTO, festive GMV/order lift,
    COD RTO by basket size, and top-selling products. Accepts names like 'fashion', 'skincare', 'pet'."""
    return _safe(logic.category_profile, category)


@mcp.tool(annotations=RO)
def rank_categories(metric: str) -> dict:
    """Rank all categories on one metric (e.g. 'cod_rto_pct', 'festive_gmv_lift_pct', 'checkout_completion_pct').
    Call list_categories to see metric keys."""
    return _safe(logic.rank_categories, metric)


@mcp.tool(annotations=RO)
def get_festival_timeline() -> dict:
    """Festive season dates and the two demand peaks. Use to plan spend timing."""
    return {"timeline": logic.DATA["festival_timeline"], "peaks_note": logic.meta()["peaks_note"]}


@mcp.tool(annotations=RO)
def compare_brand_to_benchmark(
    category: str,
    aov_inr: float | None = None,
    cod_pct: float | None = None,
    prepaid_pct: float | None = None,
    cod_rto_pct: float | None = None,
    prepaid_rto_pct: float | None = None,
    blended_rto_pct: float | None = None,
    cod_return_pct: float | None = None,
    checkout_completion_pct: float | None = None,
    cart_abandon_pct: float | None = None,
    rebuy_days: float | None = None,
    tier3_orders_pct: float | None = None,
    tier3_rto_pct: float | None = None,
) -> dict:
    """Compare a brand's own metrics to its category benchmark and get prioritised recommendations.
    Pass only metrics the brand actually has, as percentages (e.g. 32.5 for 32.5%). AOV from Meta can be
    computed as purchase value / purchases. Do NOT pass Meta's initiate-checkout→purchase rate as
    checkout_completion_pct; they are different funnels."""
    brand = {k: v for k, v in locals().items() if k != "category" and v is not None}
    return _safe(logic.compare_brand, category, brand)


@mcp.tool(annotations=RO)
def rto_adjusted_roas(
    category: str,
    meta_roas: float,
    cod_pct: float | None = None,
    ppcod_pct: float | None = None,
    cod_rto_pct: float | None = None,
    prepaid_rto_pct: float | None = None,
) -> dict:
    """Convert Meta-reported purchase ROAS into an RTO-adjusted ROAS (revenue actually delivered).
    Uses the brand's payment mix and RTO if given, else category benchmarks. Also shows a what-if for moving
    10 pp of COD orders to prepaid."""
    return _safe(logic.rto_adjusted_roas, category, meta_roas, cod_pct, ppcod_pct, cod_rto_pct, prepaid_rto_pct)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "categories": len(logic.CATEGORIES)})


app = mcp.streamable_http_app(stateless_http=True, json_response=True, host="0.0.0.0")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
