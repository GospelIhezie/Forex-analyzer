"""
gold_fundamentals/market_data.py

Fetches the two market-data series the gold analyser needs that the
existing scraper.py doesn't provide:

- get_real_yield_series(): US 10-Year real yield (TIPS), from FRED —
  requires a free API key (config.FRED_API_KEY). Get one at
  https://fred.stlouisfed.org/docs/api/api_key.html
- get_dxy_series(): US Dollar Index (DXY) daily closes, from Yahoo
  Finance's public chart endpoint — no API key needed. Note this is an
  unofficial, unauthenticated endpoint (not a published/supported Yahoo
  API); it's free and widely used, but Yahoo could change or block it
  without notice. If it starts failing, that's why.

Both functions fail soft: on any error (missing key, network issue,
unexpected response shape) they log a warning and return an empty list,
which the scoring functions in scoring.py treat as "unavailable" rather
than crashing the whole run.
"""

import logging
import requests

from config import FRED_API_KEY, FRED_REAL_YIELD_SERIES, YAHOO_DXY_URL

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ForexFundamentalsBot/1.0)"
}

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"


def get_real_yield_series() -> list[dict]:
    """
    Returns the last ~10 observations of the FRED real-yield series as
    [{"date": "2026-09-24", "value": 1.85}, ...] sorted oldest to newest.
    FRED marks missing days (holidays/weekends) with "." — those are
    dropped rather than treated as 0.
    """
    if not FRED_API_KEY:
        logger.warning("FRED_API_KEY not set — skipping real yield fetch.")
        return []

    params = {
        "series_id": FRED_REAL_YIELD_SERIES,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 10,
    }

    try:
        resp = requests.get(FRED_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("Failed to fetch FRED real yield series: %s", e)
        return []

    observations = data.get("observations", [])
    series = []
    for obs in observations:
        value = obs.get("value")
        if value in (None, ".", ""):
            continue
        try:
            series.append({"date": obs["date"], "value": float(value)})
        except (TypeError, ValueError):
            continue

    series.reverse()  # FRED gave us newest-first; scoring wants oldest-first
    return series


def get_dxy_series() -> list[dict]:
    """
    Returns the last ~5 daily closes of DXY as
    [{"date": "2026-09-24", "value": 103.45}, ...] sorted oldest to newest.
    """
    params = {"interval": "1d", "range": "10d"}

    try:
        resp = requests.get(YAHOO_DXY_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("Failed to fetch DXY series from Yahoo Finance: %s", e)
        return []

    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Unexpected DXY response shape: %s", e)
        return []

    from datetime import datetime, timezone

    series = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        series.append({"date": date_str, "value": round(float(close), 3)})

    return series
