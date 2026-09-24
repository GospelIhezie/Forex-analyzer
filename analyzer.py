"""
Analysis layer.

score_calendar_bias(): compares actual vs forecast for released events and
    produces a per-currency bullish/bearish score.
score_news_sentiment(): simple keyword-based sentiment pass over headlines,
    per currency.
combine_scores(): merges both into one fundamentals verdict per currency.
"""

import re
from itertools import combinations
from config import MIN_IMPACT, IMPACT_WEIGHTS, TRACKED_CURRENCIES

IMPACT_ORDER = {"Low": 0, "Medium": 1, "High": 2}

# Very small keyword lexicon for headline sentiment. This is intentionally
# simple/transparent rather than a black-box model — good enough to flag
# clearly hawkish/dovish or risk-on/risk-off language, not a substitute for
# reading the news yourself.
BULLISH_WORDS = {
    "hike", "hikes", "hawkish", "raises rates", "rate hike", "stronger",
    "beats", "surge", "surges", "growth", "outperform", "tightening",
    "inflation rises", "strong jobs", "expansion",
}
BEARISH_WORDS = {
    "cut", "cuts", "dovish", "lowers rates", "rate cut", "weaker",
    "misses", "slump", "slumps", "recession", "contraction", "easing",
    "inflation falls", "weak jobs", "layoffs", "slowdown",
}

CURRENCY_KEYWORDS = {
    "USD": ["usd", "dollar", "federal reserve", "fed ", "fomc"],
    "EUR": ["eur", "euro", "ecb", "eurozone"],
    "GBP": ["gbp", "pound", "sterling", "boe", "bank of england"],
    "JPY": ["jpy", "yen", "boj", "bank of japan"],
    "AUD": ["aud", "aussie", "rba"],
    "CAD": ["cad", "loonie", "boc", "bank of canada"],
    "CHF": ["chf", "franc", "snb"],
    "NZD": ["nzd", "kiwi", "rbnz"],
}


def _impact_meets_threshold(impact: str) -> bool:
    return IMPACT_ORDER.get(impact, 0) >= IMPACT_ORDER.get(MIN_IMPACT, 0)


def _to_number(value: str):
    """Extract a float from strings like '3.2%', '180K', '1.5M', '-0.4'."""
    if not value:
        return None
    match = re.search(r"-?\d+(\.\d+)?", value.replace(",", ""))
    if not match:
        return None
    num = float(match.group())
    if "K" in value.upper():
        num *= 1_000
    elif "M" in value.upper():
        num *= 1_000_000
    elif "B" in value.upper():
        num *= 1_000_000_000
        combined[currency] = {
            "score": round(total, 3),
            "bias": bias,
            "calendar_events": cal["events"],
            "news_hits": news["hits"],
        }

    return combined


def compute_pair_biases(combined_scores: dict) -> list[dict]:
    """
    Derives a Buy/Sell/Neutral bias for every currency pair from the
    per-currency fundamental scores already computed above (pair score =
    base currency score minus quote currency score). This is plain
    arithmetic on real data — not a separate model — so it's only as
    good as the underlying per-currency scores.

    Returns a list of {"pair": "USD/CAD", "score": float, "bias": str},
    sorted by strength of signal (strongest first).
    """
    results = []
    for base, quote in combinations(TRACKED_CURRENCIES, 2):
        base_score = combined_scores.get(base, {}).get("score", 0.0)
        quote_score = combined_scores.get(quote, {}).get("score", 0.0)
        diff = round(base_score - quote_score, 3)

        if diff > 0.15:
            bias = "Buy"
        elif diff < -0.15:
            bias = "Sell"
        else:
            bias = "Neutral"

        results.append({"pair": f"{base}/{quote}", "score": diff, "bias": bias})

    results.sort(key=lambda r: abs(r["score"]), reverse=True)
    return results
    
