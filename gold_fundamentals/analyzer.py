"""
gold_fundamentals/analyzer.py

Combines the individual factor scores from scoring.py into:
- a total XAU/USD fundamental score, normalized to -10..+10
- a bias classification (VERY BULLISH / BULLISH / NEUTRAL / BEARISH / VERY BEARISH)
- a confidence level based on how much of the weighted model actually had
  data this run (unavailable factors reduce confidence, they don't get a
  score of 0 silently averaged in)
- conflict detection between factors pulling in opposite directions
"""

from config import GOLD_CATEGORY_WEIGHTS, GOLD_UNAVAILABLE_FACTORS
from gold_fundamentals.scoring import (
    score_fed_rates, score_inflation, score_employment_growth,
    score_usd_strength, score_geopolitical_risk, score_central_bank_demand,
    score_real_yields, score_dxy,
)

CATEGORY_LABELS = {
    "fed_rates": "Fed / Rates",
    "real_yields": "US Real Yields (10Y TIPS)",
    "dxy": "US Dollar Index (DXY)",
    "usd_strength": "USD Strength",
    "inflation": "Inflation",
    "geopolitical_risk": "Geopolitical & Risk Sentiment",
    "employment_growth": "Employment / Growth",
    "central_bank_demand": "Central Bank & Gold Demand (headline-only)",
}


def build_gold_analysis(
    calendar_events: list[dict],
    headlines: list[dict],
    usd_currency_score,
    real_yield_series: list[dict] | None = None,
    dxy_series: list[dict] | None = None,
) -> dict:
    factor_results = {
        "fed_rates": score_fed_rates(calendar_events),
        "real_yields": score_real_yields(real_yield_series or []),
        "dxy": score_dxy(dxy_series or []),
        "usd_strength": score_usd_strength(usd_currency_score),
        "inflation": score_inflation(calendar_events),
        "geopolitical_risk": score_geopolitical_risk(headlines),
        "employment_growth": score_employment_growth(calendar_events),
        "central_bank_demand": score_central_bank_demand(headlines),
    }

    weight_total = sum(GOLD_CATEGORY_WEIGHTS.values())
    weighted_sum = 0.0
    weight_used = 0.0

    categories = {}
    for key, result in factor_results.items():
        weight = GOLD_CATEGORY_WEIGHTS.get(key, 0)
        categories[key] = {**result, "label": CATEGORY_LABELS[key], "weight": weight}
        if result["available"]:
            weighted_sum += result["raw_score"] * weight
            weight_used += weight

    # Average raw score across available, weighted factors, scaled from the
    # -2..+2 raw band up to the -10..+10 total-score band the user wants.
    total_score = round((weighted_sum / weight_used) * 5, 2) if weight_used else 0.0

    if total_score >= 7:
        bias = "VERY BULLISH"
    elif total_score >= 3:
        bias = "BULLISH"
    elif total_score <= -7:
        bias = "VERY BEARISH"
    elif total_score <= -3:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    data_coverage = (weight_used / weight_total) if weight_total else 0.0
    if data_coverage >= 0.8:
        confidence = "HIGH"
    elif data_coverage >= 0.5:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Conflict = at least one category meaningfully bullish AND at least one
    # meaningfully bearish (small noise near zero doesn't count as a side).
    bullish_factors = [c for c in categories.values() if c["available"] and c["raw_score"] > 0.3]
    bearish_factors = [c for c in categories.values() if c["available"] and c["raw_score"] < -0.3]
    conflict = bool(bullish_factors) and bool(bearish_factors)

    return {
        "total_score": total_score,
        "bias": bias,
        "confidence": confidence,
        "data_coverage_pct": round(data_coverage * 100),
        "categories": categories,
        "bullish_factors": bullish_factors,
        "bearish_factors": bearish_factors,
        "conflict": conflict,
        "unavailable_factors": GOLD_UNAVAILABLE_FACTORS,
    }

