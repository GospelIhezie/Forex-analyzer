"""
gold_fundamentals/main.py — entry point for the XAU/USD digest.

Reuses the SAME calendar/news fetchers as the main Forex analyser
(scraper.py) — this file does not scrape anything new there. It also pulls
its own market data (FRED real yields, and Yahoo Finance DXY/VIX/gold/oil)
via market_data.py. Does not touch or affect the main Forex digest
(main.py) in any way. Run independently:

    python -m gold_fundamentals.main
"""

import logging

from scraper import get_calendar_events, get_news_headlines
from gold_fundamentals.analyzer import build_gold_analysis
from gold_fundamentals.report import build_gold_report
from gold_fundamentals.market_data import (
    get_real_yield_series, get_dxy_series, get_vix_series,
    get_gold_price_series, get_oil_price_series,
)
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

    logger.info("Fetching market data (FRED real yields, Yahoo DXY/VIX/gold/oil)...")
    real_yield_series = get_real_yield_series()
    dxy_series = get_dxy_series()
    vix_series = get_vix_series()
    gold_price_series = get_gold_price_series()
    oil_price_series = get_oil_price_series()
    logger.info(
        "Real yield: %d pts | DXY: %d pts | VIX: %d pts | Gold: %d pts | Oil: %d pts",
        len(real_yield_series), len(dxy_series), len(vix_series),
        len(gold_price_series), len(oil_price_series),
    )

    logger.info("Building gold fundamentals analysis...")
    analysis = build_gold_analysis(
        calendar_events=events,
        headlines=headlines,
        real_yield_series=real_yield_series,
        dxy_series=dxy_series,
        vix_series=vix_series,
        gold_price_series=gold_price_series,
        oil_price_series=oil_price_series,
    )

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
