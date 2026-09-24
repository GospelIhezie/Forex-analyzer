"""
Analysis layer.

score_calendar_bias(): compares actual vs forecast for released events and
    produces a per-currency bullish/bearish score.
score_news_sentiment(): simple keyword-based sentiment pass over headlines,
    per currency.
combine_scores(): merges both into one fundamentals verdict per currency.
"""

import re
from config import MIN_IMPACT, IMPACT_WEIGHTS, TRACKED_CURRENCIES, STANDARD_FX_PAIRS

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
    return num


def score_calendar_bias(events: list[dict]) -> dict:
    """Returns {currency: {"score": float, "events": [event summaries]}}."""
    result = {c: {"score": 0.0, "events": []} for c in TRACKED_CURRENCIES}

    for e in events:
        currency = e["country"]
        if currency not in result:
            continue
        if not _impact_meets_threshold(e["impact"]):
            continue
        if not e["actual"]:
            continue  # event hasn't been released yet

        actual = _to_number(e["actual"])
        forecast = _to_number(e["forecast"])
        if actual is None or forecast is None or forecast == 0:
            continue

        deviation_pct = (actual - forecast) / abs(forecast)
        weight = IMPACT_WEIGHTS.get(e["impact"], 1)
        contribution = deviation_pct * weight

        result[currency]["score"] += contribution
        result[currency]["events"].append({
            "title": e["title"],
            "impact": e["impact"],
            "actual": e["actual"],
            "forecast": e["forecast"],
            "previous": e["previous"],
            "beat": actual > forecast,
        })

    return result


def score_news_sentiment(headlines: list[dict]) -> dict:
    """Returns {currency: {"score": float, "hits": [headline titles]}}."""
    result = {c: {"score": 0.0, "hits": []} for c in TRACKED_CURRENCIES}

    for item in headlines:
        text = f"{item['title']} {item.get('summary', '')}".lower()

        bullish_hits = sum(1 for w in BULLISH_WORDS if w in text)
        bearish_hits = sum(1 for w in BEARISH_WORDS if w in text)
        net = bullish_hits - bearish_hits
        if net == 0:
            continue

        for currency, keywords in CURRENCY_KEYWORDS.items():
            if any(k in text for k in keywords):
                result[currency]["score"] += net
                result[currency]["hits"].append(item["title"])

    return result


def combine_scores(calendar_scores: dict, news_scores: dict) -> dict:
    """
    Merges calendar and news scores into one verdict per currency:
    {"score": float, "bias": "Bullish"|"Bearish"|"Neutral", ...details}
    """
    combined = {}
    for currency in TRACKED_CURRENCIES:
        cal = calendar_scores.get(currency, {"score": 0.0, "events": []})
        news = news_scores.get(currency, {"score": 0.0, "hits": []})
        total = cal["score"] + news["score"] * 0.5  # news weighted lighter than hard data

        if total > 0.15:
            bias = "Bullish"
        elif total < -0.15:
            bias = "Bearish"
        else:
            bias = "Neutral"

        combined[currency] = {
            "score": round(total, 3),
            "bias": bias,
            "calendar_events": cal["events"],
            "news_hits": news["hits"],
        }

    return combined


def compute_pair_biases(combined_scores: dict) -> list[dict]:
    """
    Derives a Buy/Sell/Neutral bias for each STANDARD_FX_PAIRS entry from the
    per-currency fundamental scores already computed above.

    PAIR SCORE = BASE currency score - QUOTE currency score
        > 0  -> base is fundamentally stronger -> Buy the pair
        < 0  -> base is fundamentally weaker    -> Sell the pair
        ~0   -> Neutral

    This only uses the fixed, correctly-oriented pairs in
    config.STANDARD_FX_PAIRS (e.g. EUR/USD, not the reverse USD/EUR) — it
    does not invent pairs by combining every currency with every other one,
    since that produces pairs the market doesn't actually quote that way.

    Returns a list of dicts with base/quote scores, the differential, the
    Buy/Sell/Neutral bias, and a Strong/Moderate/Weak strength label (a
    plain bucketing of the real differential — not a fabricated confidence
    score), sorted strongest signal first.
    """
    results = []
    for base, quote in STANDARD_FX_PAIRS:
        base_score = combined_scores.get(base, {}).get("score", 0.0)
        quote_score = combined_scores.get(quote, {}).get("score", 0.0)
        diff = round(base_score - quote_score, 3)

        if diff > 0.15:
            bias = "Buy"
        elif diff < -0.15:
            bias = "Sell"
        else:
            bias = "Neutral"

        abs_diff = abs(diff)
        if abs_diff >= 1.0:
            strength = "Strong"
        elif abs_diff >= 0.3:
            strength = "Moderate"
        else:
            strength = "Weak"

        results.append({
            "pair": f"{base}/{quote}",
            "base": base,
            "quote": quote,
            "base_score": base_score,
            "quote_score": quote_score,
            "score": diff,
            "bias": bias,
            "strength": strength,
        })

    results.sort(key=lambda r: abs(r["score"]), reverse=True)
    return results
        
