
"""
gold_fundamentals/main.py — entry point for the XAU/USD digest.

Reuses the SAME data-fetching functions as the main Forex analyser
(scraper.py) and the SAME per-currency USD score (analyzer.py) — this file
does not scrape anything new, and does not touch or affect the main Forex
digest (main.py) in any way. Run independently:

    python -m gold_fundamentals.main
"""

import logging

from scraper import get_calendar_events, get_news_headlines
from analyzer import score_calendar_bias, score_news_sentiment, combine_scores
from gold_fundamentals.analyzer import build_gold_analysis
from gold_fundamentals.report import build_gold_report
from gold_fundamentals.market_data import get_real_yield_series, get_dxy_series
from telegram_bot import send_report  # generic Telegram sender, reused as-is

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gold_main")


def run_once():
    logger.info("Fetching economic calendar...")
    events = get_calendar_events()
    logger.info("Fetched %d calendar events.", len(events))

    logger.info("Fetching news headlines...")
    headlines = get_news_headlines()
    logger.info("Fetched %d headlines.", len(headlines))

    # Reuse the main Forex analyser's USD score rather than computing USD
    # strength a second, independent way.
    calendar_scores = score_calendar_bias(events)
    news_scores = score_news_sentiment(headlines)
    combined = combine_scores(calendar_scores, news_scores)
    usd_score = combined.get("USD", {}).get("score")

    logger.info("Fetching real yield (FRED) and DXY (Yahoo Finance) series...")
    real_yield_series = get_real_yield_series()
    dxy_series = get_dxy_series()
    logger.info("Real yield points: %d | DXY points: %d", len(real_yield_series), len(dxy_series))

    logger.info("Building gold fundamentals analysis...")
    analysis = build_gold_analysis(events, headlines, usd_score, real_yield_series, dxy_series)

    report = build_gold_report(analysis)
    logger.info("Gold report:\n%s", report)

    logger.info("Sending gold report to Telegram...")
    ok = send_report(report)
    if ok:
        logger.info("Gold report sent successfully.")
    else:
        logger.error("Gold report failed to send. Check your Telegram config.")


if __name__ == "__main__":
    run_once()
