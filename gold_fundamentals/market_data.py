"""
gold_fundamentals/market_data.py

Fetches the market-data series the gold analyser needs that the existing
scraper.py doesn't provide:

- get_real_yield_series(): US 10-Year real yield (TIPS), from FRED —
  requires a free API key (config.FRED_API_KEY).
- get_dxy_series() / get_gold_price_series() / get_oil_price_series() /
  get_vix_series(): daily closes from Yahoo Finance's public chart
  endpoint — no API key needed. This is an unofficial, unauthenticated
  endpoint (not a published/supported Yahoo API); free and widely used,
  but Yahoo could change or block it without notice. If it starts
  failing, that's why.

Every function fails soft: on any error (missing key, network issue,
unexpected response shape) it logs a warning and returns an empty list,
which the scoring functions in scoring.py treat as "unavailable" rather
than crashing the whole run.

Gold and oil prices are fetched for the MOMENTUM section of the report
only — per the review that pointed this out, price/technical data is kept
separate from the fundamentals score, not blended into it.
"""

import logging
from datetime import datetime, timezone

import requests

from config import (
    FRED_API_KEY, FRED_REAL_YIELD_SERIES,
    YAHOO_DXY_URL, YAHOO_GOLD_URL, YAHOO_OIL_URL, YAHOO_VIX_URL,
)

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


def _fetch_yahoo_series(url: str, range_: str = "10d") -> list[dict]:
    """
    Shared fetcher for Yahoo Finance's public chart JSON endpoint. Returns
    [{"date": "2026-09-24", "value": 103.45}, ...] sorted oldest to newest,
    or [] on any failure.
    """
    params = {"interval": "1d", "range": range_}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("Failed to fetch Yahoo Finance series from %s: %s", url, e)
        return []

    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Unexpected Yahoo Finance response shape from %s: %s", url, e)
        return []

    series = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        series.append({"date": date_str, "value": round(float(close), 3)})

    return series


def get_dxy_series() -> list[dict]:
    """US Dollar Index (DXY) daily closes — used for the DXY scoring factor."""
    return _fetch_yahoo_series(YAHOO_DXY_URL)


def get_gold_price_series() -> list[dict]:
    """
    COMEX gold futures (GC=F) daily closes — used ONLY for the report's
    separate, unscored Momentum section (1D/5D price change), never fed
    into the fundamentals score itself.
    """
    return _fetch_yahoo_series(YAHOO_GOLD_URL, range_="15d")


def get_oil_price_series() -> list[dict]:
    """
    WTI crude futures (CL=F) daily closes — shown as context in the
    Momentum section only. Oil's relationship to gold (via inflation
    expectations) is genuinely ambiguous enough that this project doesn't
    attempt to score it as bullish/bearish; it's informational only.
    """
    return _fetch_yahoo_series(YAHOO_OIL_URL, range_="15d")


def get_vix_series() -> list[dict]:
    """CBOE Volatility Index (VIX) daily closes — used for risk-sentiment scoring."""
    return _fetch_yahoo_series(YAHOO_VIX_URL)
