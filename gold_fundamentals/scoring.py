
"""
gold_fundamentals/scoring.py

Computes individual XAU/USD fundamental factor scores. Most factors reuse
the SAME economic-calendar and news data the main Forex analyser already
fetches (see scraper.py) — nothing new scraped there. Two factors
(real yields, DXY) use their own small, focused data fetched by
gold_fundamentals/market_data.py: FRED (Federal Reserve) for real yields,
Yahoo Finance's public JSON chart endpoint for the dollar index.

Honesty notes (read before trusting these numbers):

1. Real yields and DXY are live-fetched via market_data.py — everything
   else still marked in config.GOLD_UNAVAILABLE_FACTORS (ETF flow $
   figures, central-bank purchase tonnage, China/India demand) genuinely
   has no free, reliable feed wired into this project. Those stay
   unscored, never invented.

2. The sign conventions below (e.g. "hotter-than-expected inflation is
   treated as hawkish, which is bearish for gold") are a documented,
   debatable simplification. In reality, an inflation surprise can push
   gold either way depending on context (inflation hedge demand vs. Fed
   rate-hike expectations) — a keyword+deviation script cannot genuinely
   resolve that ambiguity. Treat this as a transparent, consistent
   heuristic, not a claim of real macro judgment.

3. The central-bank/demand score only checks whether relevant headlines
   exist at all — it cannot quantify tonnage or dollar flows without World
   Gold Council-type data, so it's deliberately capped at a small
   magnitude and flagged low_confidence.

4. Yahoo Finance's chart endpoint used for DXY is not an officially
   published/supported API — it's a widely-used, stable, unauthenticated
   JSON endpoint, but Yahoo could change its shape without notice. If it
   ever breaks, this factor fails closed (DATA UNAVAILABLE), not silently
   wrong.
"""

from analyzer import _to_number, IMPACT_ORDER
from config import (
    GOLD_MIN_IMPACT,
    GOLD_FED_KEYWORDS,
    GOLD_INFLATION_KEYWORDS,
    GOLD_GROWTH_KEYWORDS,
    GOLD_BULLISH_NEWS_WORDS,
    GOLD_BEARISH_NEWS_WORDS,
    GOLD_DEMAND_KEYWORDS,
)

_IMPACT_WEIGHT = {"High": 3, "Medium": 1.5, "Low": 0.5}


def _meets_threshold(impact: str) -> bool:
    return IMPACT_ORDER.get(impact, 0) >= IMPACT_ORDER.get(GOLD_MIN_IMPACT, 0)


def _bucket_magnitude(abs_change: float, small: float, medium: float, large: float) -> float:
    """Maps a real-world change magnitude to the 0..2 raw-score band."""
    if abs_change >= large:
        return 2.0
    if abs_change >= medium:
        return 1.0
    if abs_change >= small:
        return 0.5
    return 0.0


def _calendar_category_score(events: list[dict], keywords: list[str]) -> dict:
    """
    Filters released, USD, at-or-above-threshold-impact calendar events
    whose title matches any of `keywords`, scores each by actual-vs-forecast
    deviation (same math as the main analyser), then applies the gold sign
    convention: a stronger/hotter-than-forecast USD print is treated as
    hawkish -> bearish gold (and a miss as dovish -> bullish gold).
    """
    matched = []
    weighted_total = 0.0
    weight_sum = 0.0

    for e in events:
        if e["country"] != "USD" or not _meets_threshold(e["impact"]):
            continue
        if not any(k in e["title"].lower() for k in keywords):
            continue
        if not e["actual"]:
            continue

        actual = _to_number(e["actual"])
        forecast = _to_number(e["forecast"])
        if actual is None or forecast is None or forecast == 0:
            continue

        deviation_pct = (actual - forecast) / abs(forecast)
        weight = _IMPACT_WEIGHT.get(e["impact"], 1)
        gold_contribution = -deviation_pct * weight  # beat forecast -> hawkish -> bearish gold

        weighted_total += gold_contribution
        weight_sum += weight
        matched.append({
            "title": e["title"], "impact": e["impact"],
            "actual": e["actual"], "forecast": e["forecast"],
        })

    if not matched:
        return {"available": False, "raw_score": 0.0, "events": [],
                "reason": "No matching released USD events this period"}

    avg = weighted_total / weight_sum if weight_sum else 0.0
    raw_score = max(-2.0, min(2.0, avg * 5))  # scale into the -2..+2 factor band

    return {
        "available": True,
        "raw_score": round(raw_score, 2),
        "events": matched,
        "reason": f"Derived from {len(matched)} released USD event(s): "
                  + ", ".join(m["title"] for m in matched[:3]),
    }


def score_fed_rates(events: list[dict]) -> dict:
    return _calendar_category_score(events, GOLD_FED_KEYWORDS)


def score_inflation(events: list[dict]) -> dict:
    return _calendar_category_score(events, GOLD_INFLATION_KEYWORDS)


def score_employment_growth(events: list[dict]) -> dict:
    return _calendar_category_score(events, GOLD_GROWTH_KEYWORDS)


def score_usd_strength(usd_currency_score) -> dict:
    """
    Reuses the existing per-currency USD fundamental score already computed
    by the main Forex analyser (analyzer.combine_scores) instead of
    recomputing USD strength a second, independent way — avoids two
    slightly-different "USD scores" disagreeing with each other. Stronger
    USD -> bearish gold, so the sign is inverted here.
    """
    if usd_currency_score is None:
        return {"available": False, "raw_score": 0.0, "reason": "USD score not available"}

    raw_score = max(-2.0, min(2.0, -usd_currency_score))
    return {
        "available": True,
        "raw_score": round(raw_score, 2),
        "reason": f"Inverse of the Forex analyser's USD score ({usd_currency_score:+.2f})",
    }


def score_geopolitical_risk(headlines: list[dict]) -> dict:
    bullish_hits, bearish_hits = [], []

    for item in headlines:
        text = f"{item['title']} {item.get('summary', '')}".lower()
        if any(w in text for w in GOLD_BULLISH_NEWS_WORDS):
            bullish_hits.append(item["title"])
        if any(w in text for w in GOLD_BEARISH_NEWS_WORDS):
            bearish_hits.append(item["title"])

    if not bullish_hits and not bearish_hits:
        return {"available": False, "raw_score": 0.0, "headlines": [],
                "reason": "No geopolitical/risk-sentiment headlines this period"}

    net = len(bullish_hits) - len(bearish_hits)
    raw_score = max(-2.0, min(2.0, net * 0.5))
    return {
        "available": True,
        "raw_score": round(raw_score, 2),
        "headlines": (bullish_hits + bearish_hits)[:5],
        "reason": f"{len(bullish_hits)} risk-escalation headline(s) vs "
                  f"{len(bearish_hits)} de-escalation headline(s)",
    }


def score_real_yields(real_yield_series: list[dict]) -> dict:
    """
    Uses the two most recent valid FRED 10Y real-yield observations
    (real_yield_series, as returned by market_data.get_real_yield_series())
    to determine direction of change. Falling real yields make gold (which
    pays no yield) relatively more attractive -> bullish. Rising real
    yields -> bearish. Thresholds are tuned to typical daily moves in this
    series (a few basis points is routine; 7+ bp is a notably large day).
    """
    if len(real_yield_series) < 2:
        return {"available": False, "raw_score": 0.0,
                "reason": "FRED real yield data unavailable (missing API key or fetch failed)"}

    latest = real_yield_series[-1]
    previous = real_yield_series[-2]
    change = round(latest["value"] - previous["value"], 4)

    magnitude = _bucket_magnitude(abs(change), small=0.01, medium=0.03, large=0.07)
    if change > 0:
        raw_score = -magnitude
        direction = "rose"
    elif change < 0:
        raw_score = magnitude
        direction = "fell"
    else:
        raw_score = 0.0
        direction = "unchanged"

    return {
        "available": True,
        "raw_score": round(raw_score, 2),
        "reason": f"10Y real yield {direction} {abs(change):.3f} pts to {latest['value']:.2f}% "
                  f"({previous['date']} -> {latest['date']})",
    }


def score_dxy(dxy_series: list[dict]) -> dict:
    """
    Uses the two most recent DXY daily closes (dxy_series, as returned by
    market_data.get_dxy_series()). A rising dollar index is bearish for
    gold (priced in USD); a falling one is bullish. Thresholds are tuned to
    typical daily DXY moves (~0.1-0.3% is routine; 0.6%+ is a notably large
    day).
    """
    if len(dxy_series) < 2:
        return {"available": False, "raw_score": 0.0,
                "reason": "DXY data unavailable (fetch failed)"}

    latest = dxy_series[-1]
    previous = dxy_series[-2]
    if previous["value"] == 0:
        return {"available": False, "raw_score": 0.0, "reason": "Invalid previous DXY value"}

    pct_change = (latest["value"] - previous["value"]) / previous["value"] * 100

    magnitude = _bucket_magnitude(abs(pct_change), small=0.1, medium=0.3, large=0.6)
    if pct_change > 0:
        raw_score = -magnitude
        direction = "rose"
    elif pct_change < 0:
        raw_score = magnitude
        direction = "fell"
    else:
        raw_score = 0.0
        direction = "unchanged"

    return {
        "available": True,
        "raw_score": round(raw_score, 2),
        "reason": f"DXY {direction} {abs(pct_change):.2f}% to {latest['value']:.2f} "
                  f"({previous['date']} -> {latest['date']})",
    }


def score_central_bank_demand(headlines: list[dict]) -> dict:
    hits = []
    for item in headlines:
        text = f"{item['title']} {item.get('summary', '')}".lower()
        if any(k in text for k in GOLD_DEMAND_KEYWORDS):
            hits.append(item["title"])

    if not hits:
        return {"available": False, "raw_score": 0.0, "headlines": [],
                "reason": "No central-bank/demand headlines this period",
                "low_confidence": True}

    # Presence-only signal, deliberately small and capped — see module
    # docstring on why this can't be genuinely quantified from free data.
    return {
        "available": True,
        "raw_score": 0.5,
        "headlines": hits[:3],
        "reason": f"{len(hits)} relevant headline(s) found "
                  f"(headline-presence only, not a quantified flow figure)",
        "low_confidence": True,
    }
