"""
Data collection layer.

- get_calendar_events(): pulls this week's economic calendar (ForexFactory JSON feed).
- get_news_headlines(): pulls recent forex headlines from public RSS feeds.

No HTML scraping of protected pages is done here on purpose — calendar and
news data are pulled from feeds designed for programmatic consumption, which
is far more reliable than parsing rendered HTML and won't get blocked by
anti-bot protections.
"""

import logging
from datetime import datetime, timezone

import requests
import feedparser

from config import FF_CALENDAR_URL, NEWS_FEEDS, NEWS_ITEMS_PER_SOURCE

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ForexFundamentalsBot/1.0)"
}


def get_calendar_events() -> list[dict]:
    """
    Returns a list of dicts like:
    {
        "title": "Non-Farm Payrolls",
        "country": "USD",
        "date": datetime,
        "impact": "High" | "Medium" | "Low",
        "forecast": "180K" | "",
        "previous": "175K" | "",
        "actual": "190K" | "",  # empty if event hasn't happened yet
    }
    """
    try:
        resp = requests.get(FF_CALENDAR_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        raw_events = resp.json()
    except Exception as e:
        logger.error("Failed to fetch economic calendar: %s", e)
        return []

    events = []
    for e in raw_events:
        try:
            events.append({
                "title": e.get("title", "").strip(),
                "country": e.get("country", "").strip(),
                "date": _parse_date(e.get("date")),
                "impact": e.get("impact", "Low").strip(),
                "forecast": (e.get("forecast") or "").strip(),
                "previous": (e.get("previous") or "").strip(),
                "actual": (e.get("actual") or "").strip(),
            })
        except Exception as parse_err:
            logger.warning("Skipping malformed calendar entry: %s", parse_err)

    return events


def _parse_date(raw: str):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def get_news_headlines() -> list[dict]:
    """
    Returns a list of dicts like:
    {"source": "FXStreet", "title": "...", "summary": "...", "published": datetime|None}
    """
    all_items = []
    for source_name, url in NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                logger.warning("Feed %s returned no usable entries", source_name)
                continue
            for entry in feed.entries[:NEWS_ITEMS_PER_SOURCE]:
                all_items.append({
                    "source": source_name,
                    "title": getattr(entry, "title", "").strip(),
                    "summary": getattr(entry, "summary", "").strip(),
                    "published": getattr(entry, "published", None),
                })
        except Exception as e:
            logger.error("Failed to fetch news feed %s: %s", source_name, e)

    return all_items
