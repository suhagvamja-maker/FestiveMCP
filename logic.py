"""Pure benchmark logic. No MCP code here, so it can be unit-tested directly."""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any

DATA = json.loads((pathlib.Path(__file__).parent / "data" / "benchmarks.json").read_text())
CATEGORIES: dict[str, dict] = {c["key"]: c for c in DATA["categories"]}

# Metric dictionary: label, unit, definition, and which direction is "better" for a brand.
# direction: "lower" / "higher" / None (context-dependent, no verdict given)
METRICS: dict[str, dict[str, Any]] = {
    "aov_inr": {"label": "AOV", "unit": "INR", "direction": None,
                "definition": "Average order value for the category."},
    "cod_pct": {"label": "COD share", "unit": "%", "direction": "lower",
                "definition": "Share of orders paid by cash on delivery."},
    "prepaid_pct": {"label": "Prepaid share", "unit": "%", "direction": "higher",
                    "definition": "Share of orders fully prepaid (includes EMI)."},
    "ppcod_pct": {"label": "PPCOD share", "unit": "%", "direction": None,
                  "definition": "Share of orders that are part-prepaid COD."},
    "emi_pct": {"label": "EMI share", "unit": "%", "direction": None,
                "definition": "Share of orders on EMI (a subset of prepaid)."},
    "cod_rto_pct": {"label": "COD RTO", "unit": "%", "direction": "lower",
                    "definition": "Return-to-origin rate on shipped COD orders."},
    "prepaid_rto_pct": {"label": "Prepaid RTO", "unit": "%", "direction": "lower",
                        "definition": "Return-to-origin rate on prepaid orders."},
    "blended_rto_pct": {"label": "Blended RTO", "unit": "%", "direction": "lower",
                        "definition": "Overall RTO rate across the payment mix."},
    "cod_return_pct": {"label": "COD post-delivery returns", "unit": "%", "direction": "lower",
                       "definition": "Post-delivery returns on COD orders."},
    "checkout_completion_pct": {"label": "Checkout completion", "unit": "%", "direction": "higher",
                                "definition": "Share of STARTED CHECKOUTS that finish (GoKwik checkout funnel)."},
    "cart_abandon_pct": {"label": "Cart abandonment", "unit": "%", "direction": "lower",
                         "definition": "Share of carts abandoned before checkout."},
    "rebuy_days": {"label": "Re-buy window", "unit": "days", "direction": "lower",
                   "definition": "Median days from a shopper's 1st order to their 2nd."},
    "charm_price_inr": {"label": "Charm price", "unit": "INR", "direction": None,
                        "definition": "Most common order value in the category."},
    "charm_price_pct": {"label": "Charm-price share", "unit": "%", "direction": None,
                        "definition": "Share of orders whose value ends in 99."},
    "top10_gmv_share_pct": {"label": "Top-10% shopper GMV share", "unit": "%", "direction": None,
                            "definition": "Share of category GMV driven by the top 10% of shoppers."},
    "tier3_orders_pct": {"label": "Tier-3 order share", "unit": "%", "direction": None,
                         "definition": "Share of orders from Tier-3 towns."},
    "tier3_rto_pct": {"label": "Tier-3 COD RTO", "unit": "%", "direction": "lower",
                      "definition": "COD RTO rate on Tier-3 orders."},
    "festive_gmv_lift_pct": {"label": "Festive GMV lift", "unit": "%", "direction": None,
                             "definition": "Festive-window GMV vs a normal month."},
    "festive_orders_lift_pct": {"label": "Festive order lift", "unit": "%", "direction": None,
                                "definition": "Festive-window orders vs a normal month."},
}
COMPARABLE = list(METRICS.keys())

# Tolerance for calling a brand "in line" with the benchmark.
# Percentages: within 2 percentage points. INR / days: within 10% relative.
PP_TOLERANCE = 2.0
REL_TOLERANCE = 0.10


# ---------- lookups ----------

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


ALIASES = {
    "apparel": "fashion", "clothing": "fashion", "jewellery": "fashion", "jewelry": "fashion",
    "beautypersonalcare": "beauty", "skincare": "beauty", "cosmetics": "beauty", "personalcare": "beauty",
    "homeliving": "home", "homedecor": "home", "furniture": "home", "kitchen": "home",
    "health": "wellness", "supplements": "wellness", "nutrition": "wellness",
    "electronic": "electronics", "gadgets": "electronics", "mobileaccessories": "electronics",
    "fnb": "food", "foodbeverages": "food", "foodandbeverages": "food", "snacks": "food", "beverages": "food",
    "toysgamessports": "toys", "sports": "toys", "games": "toys",
    "babykids": "baby", "kids": "baby",
    "booksstationery": "books", "stationery": "books",
    "pets": "pet", "petsupplies": "pet", "petcare": "pet",
    "hardware": "hardware_auto", "auto": "hardware_auto", "automotive": "hardware_auto", "hardwareauto": "hardware_auto",
    "other": "others", "general": "others",
}


def resolve_category(category: str) -> dict:
    """Match a free-text category to a benchmark category. Raises ValueError with options if no match."""
    n = _norm(category)
    for key, c in CATEGORIES.items():
        if n in (_norm(key), _norm(c["name"])):
            return c
    if n in ALIASES:
        return CATEGORIES[ALIASES[n]]
    for key, c in CATEGORIES.items():  # substring fallback, e.g. "fashion apparel brand"
        if _norm(key) in n or (len(n) >= 4 and n in _norm(c["name"])):
            return c
    options = ", ".join(f'{c["name"]} ({k})' for k, c in CATEGORIES.items())
    raise ValueError(f"Unknown category '{category}'. Available: {options}")


def meta() -> dict:
    return DATA["meta"]


def list_categories() -> list[dict]:
    return [{"key": c["key"], "name": c["name"], "rides_festive": c["rides_festive"]} for c in CATEGORIES.values()]


def category_profile(category: str) -> dict:
    c = resolve_category(category)
    metrics = {k: c[k] for k in COMPARABLE}
    riskiest = next(b for b in c["basket_risk"] if b["riskiest"])
    return {
        "category": c["name"],
        "key": c["key"],
        "window": DATA["meta"]["window"],
        "metrics": metrics,
        "rides_festive": c["rides_festive"],
        "riskiest_cod_basket": riskiest,
        "basket_risk": c["basket_risk"],
        "top_products": c["top_products"] or "Not available for this category.",
        "network_rank": {k: rank_of(c["key"], k) for k in ("cod_rto_pct", "checkout_completion_pct",
                                                           "festive_gmv_lift_pct", "aov_inr")},
        "caveat": DATA["meta"]["caveat"],
    }


def rank_of(key: str, metric: str) -> str:
    vals = sorted(CATEGORIES.values(), key=lambda c: c[metric], reverse=True)
    pos = [c["key"] for c in vals].index(key) + 1
    return f"{pos} of {len(vals)} (1 = highest)"


def rank_categories(metric: str) -> dict:
    if metric not in METRICS:
        raise ValueError(f"Unknown metric '{metric}'. Available: {', '.join(COMPARABLE)}")
    rows = sorted(({"category": c["name"], "value": c[metric]} for c in CATEGORIES.values()),
                  key=lambda r: r["value"], reverse=True)
    vals = sorted(r["value"] for r in rows)
    mid = len(vals) // 2
    median = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
    return {"metric": metric, **METRICS[metric], "ranking_high_to_low": rows,
            "network_median_across_categories": round(median, 2)}


# ---------- brand vs benchmark ----------

def _verdict(metric: str, brand: float, bench: float) -> tuple[str, str]:
    m = METRICS[metric]
    diff = brand - bench
    if m["unit"] == "%":
        gap = f"{diff:+.1f} pp"
        in_line = abs(diff) <= PP_TOLERANCE
    else:
        rel = diff / bench if bench else 0
        gap = f"{rel * 100:+.0f}%"
        in_line = abs(rel) <= REL_TOLERANCE
    if m["direction"] is None:
        return gap, "context-dependent (no verdict)"
    if in_line:
        return gap, "in line"
    better = (diff < 0) if m["direction"] == "lower" else (diff > 0)
    return gap, "better than benchmark" if better else "worse than benchmark"


def compare_brand(category: str, brand_metrics: dict[str, float]) -> dict:
    c = resolve_category(category)
    unknown = [k for k in brand_metrics if k not in METRICS]
    rows = []
    for k, v in brand_metrics.items():
        if k in unknown or v is None:
            continue
        gap, verdict = _verdict(k, float(v), float(c[k]))
        rows.append({"metric": k, "label": METRICS[k]["label"], "brand": v, "benchmark": c[k],
                     "gap": gap, "verdict": verdict})
    worse = [r["metric"] for r in rows if r["verdict"] == "worse than benchmark"]
    return {
        "category": c["name"],
        "comparison": rows,
        "worse_than_benchmark": worse,
        "ignored_unknown_metrics": unknown,
        "recommendations": playbook(c, brand_metrics),
        "definition_warning": (
            "Only compare like-for-like. Meta's 'initiate checkout → purchase' rate is NOT the same as "
            "checkout_completion_pct, and Meta ROAS counts orders that later RTO. Use rto_adjusted_roas for ROAS."
        ),
    }


# ---------- RTO-adjusted ROAS ----------

def rto_adjusted_roas(category: str, meta_roas: float, cod_pct: float | None = None,
                      ppcod_pct: float | None = None, cod_rto_pct: float | None = None,
                      prepaid_rto_pct: float | None = None, include_cod_returns: bool = True) -> dict:
    """Meta's pixel fires when an order is PLACED, so its ROAS includes revenue that later
    returns to origin. This estimates the share of attributed revenue actually delivered."""
    c = resolve_category(category)
    assumptions = []

    def pick(name, given):
        if given is None:
            assumptions.append(f"{name} = {c[name]} (category benchmark; brand value not supplied)")
            return float(c[name])
        return float(given)

    cod = pick("cod_pct", cod_pct) / 100
    ppcod = pick("ppcod_pct", ppcod_pct) / 100
    prepaid = max(0.0, 1 - cod - ppcod)
    cod_rto = pick("cod_rto_pct", cod_rto_pct) / 100
    pre_rto = pick("prepaid_rto_pct", prepaid_rto_pct) / 100
    assumptions.append("PPCOD orders assumed to RTO at the COD rate (conservative; PPCOD RTO is not in the dataset).")
    assumptions.append("Revenue share approximated by order share (assumes similar AOV across payment types).")

    delivered = cod * (1 - cod_rto) + ppcod * (1 - cod_rto) + prepaid * (1 - pre_rto)
    adjusted = meta_roas * delivered
    result = {
        "category": c["name"],
        "meta_reported_roas": meta_roas,
        "delivered_revenue_share_pct": round(delivered * 100, 1),
        "rto_adjusted_roas": round(adjusted, 2),
    }
    if include_cod_returns:
        ret = c["cod_return_pct"] / 100
        delivered_net = delivered - (cod + ppcod) * (1 - cod_rto) * ret
        result["rto_and_return_adjusted_roas"] = round(meta_roas * delivered_net, 2)
        assumptions.append(f"COD post-delivery returns = {c['cod_return_pct']}% (category benchmark).")
    # What-if: move 10pp of COD to prepaid
    shift = min(0.10, cod)
    delivered_shift = (cod - shift) * (1 - cod_rto) + ppcod * (1 - cod_rto) + (prepaid + shift) * (1 - pre_rto)
    result["what_if_10pp_cod_to_prepaid"] = {
        "rto_adjusted_roas": round(meta_roas * delivered_shift, 2),
        "uplift_pct": round((delivered_shift / delivered - 1) * 100, 1),
    }
    result["assumptions"] = assumptions
    result["not_included"] = "Forward + reverse shipping cost on RTO orders, which makes the real hit larger."
    return result


# ---------- playbook ----------

def playbook(c: dict, brand: dict[str, float] | None = None) -> list[dict]:
    """Rule-based recommendations. With brand metrics, rules fire on gaps; without, on category traits."""
    b = brand or {}
    recs: list[dict] = []

    def gap(metric):
        return (float(b[metric]) - c[metric]) if b.get(metric) is not None else None

    def add(area, why, action, gokwik=None):
        r = {"area": area, "why": why, "action": action}
        if gokwik:
            r["relevant_gokwik_product"] = gokwik
        recs.append(r)

    g = gap("cod_rto_pct")
    if g is not None and g > PP_TOLERANCE:
        add("RTO", f"COD RTO is {g:+.1f} pp vs the {c['name']} benchmark ({c['cod_rto_pct']}%), while prepaid RTO "
                   f"is only ~{c['prepaid_rto_pct']}%.",
            "Prioritise moving COD to prepaid (prepaid discounts, PPCOD/partial-COD on risky orders) and risk-score COD "
            "orders before shipping.", "Kwik Checkout (RTO suite, PPCOD)")
    g = gap("cod_pct")
    if g is not None and g > PP_TOLERANCE:
        add("Payment mix", f"COD share is {g:+.1f} pp above benchmark ({c['cod_pct']}%).",
            "Test a prepaid incentive and surface UPI first at checkout.", "Kwik Checkout")
    g = gap("checkout_completion_pct")
    if g is not None and g < -PP_TOLERANCE:
        add("Checkout", f"Checkout completion is {g:+.1f} pp below benchmark ({c['checkout_completion_pct']}%).",
            "Audit checkout friction: steps, forced login, address entry, payment options.", "Kwik Checkout")
    g = gap("cart_abandon_pct")
    if g is not None and g > PP_TOLERANCE:
        add("Cart recovery", f"Cart abandonment is {g:+.1f} pp above benchmark ({c['cart_abandon_pct']}%).",
            "Run abandoned-cart recovery on WhatsApp within the first hour, then retarget.", "Kwik Engage")
    g = gap("aov_inr")
    if g is not None and g < -c["aov_inr"] * REL_TOLERANCE:
        add("AOV", f"AOV is ₹{-g:,.0f} below the category (₹{c['aov_inr']:,}).",
            f"Bundle and set free-shipping thresholds near the category charm price (₹{c['charm_price_inr']}).")
    g = gap("cod_return_pct")
    if g is not None and g > 1.0:
        add("Returns", f"COD post-delivery returns are {g:+.1f} pp above benchmark ({c['cod_return_pct']}%).",
            "Push exchanges over refunds and capture return reasons.", "Return Prime")

    # Category traits (always useful context)
    riskiest = next(x for x in c["basket_risk"] if x["riskiest"])
    if riskiest["basket_size"] == "1 item":
        add("Basket", f"In {c['name']}, single-item COD orders are the riskiest basket ({riskiest['cod_rto_pct']}% RTO, "
                      f"{riskiest['pct_of_orders']}% of orders).",
            "Nudge to 2+ items (bundles, add-ons) and apply stricter COD rules to single-item orders.")
    else:
        add("Basket", f"In {c['name']}, {riskiest['basket_size']} COD orders are the riskiest basket "
                      f"({riskiest['cod_rto_pct']}% RTO).",
            f"Apply extra COD verification to {riskiest['basket_size']} orders rather than to all orders.")
    if not c["rides_festive"]:
        add("Festive budget", f"{c['name']} does NOT ride the festive wave (GMV {c['festive_gmv_lift_pct']:+.0f}% vs a normal month).",
            "Don't scale Meta spend on the festive calendar alone; competition raises CPMs while category demand dips.")
    else:
        add("Festive timing", f"{c['name']} rides festive (GMV {c['festive_gmv_lift_pct']:+.0f}% vs a normal month). "
                              "The network's biggest day is the sale week, not Diwali day.",
            "Front-load spend into the Navratri/sale week and the Dhanteras→Diwali gifting run; taper on Diwali day.")
    add("Retention", f"Median re-buy in {c['name']} is {c['rebuy_days']} days; top 10% of shoppers drive "
                     f"{c['top10_gmv_share_pct']}% of GMV.",
        f"Time the second-purchase campaign just before day {c['rebuy_days']} and build a VIP track for top spenders.",
        "Kwik Engage")
    return recs
