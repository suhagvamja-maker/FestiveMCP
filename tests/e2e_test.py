"""End-to-end test against a running server.  Usage:  python tests/e2e_test.py [http://localhost:8000/mcp]"""
import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/mcp"

CALLS = [
    ("list_categories", {}),
    ("get_category_benchmark", {"category": "skincare"}),
    ("rank_categories", {"metric": "festive_gmv_lift_pct"}),
    ("get_festival_timeline", {}),
    ("compare_brand_to_benchmark", {"category": "fashion", "aov_inr": 1350, "cod_pct": 68, "cod_rto_pct": 36,
                                    "cart_abandon_pct": 61, "checkout_completion_pct": 33}),
    ("rto_adjusted_roas", {"category": "fashion", "meta_roas": 3.2, "cod_pct": 68, "cod_rto_pct": 36}),
    ("get_category_benchmark", {"category": "jet engines"}),  # expected: graceful error
]


def _streams(t):
    return (t.read_stream, t.write_stream) if hasattr(t, "read_stream") else (t[0], t[1])


async def main():
    async with streamable_http_client(URL) as t:
        read, write = _streams(t)
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("TOOLS:", [x.name for x in tools.tools])
            for name, args in CALLS:
                r = await s.call_tool(name, args)
                text = r.content[0].text if r.content else ""
                print(f"\n=== {name} {args} | is_error={r.is_error if hasattr(r, 'is_error') else r.isError}")
                print(text[:1400])


asyncio.run(main())
