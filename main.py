"""
Forex Fundamentals Analyser — entry point.

Usage:
    python main.py            # run once and exit
    python main.py --loop     # run continuously on RUN_INTERVAL_MINUTES
"""

import argparse
import logging
import time

from scraper import get_calendar_events, get_news_headlines
from analyzer import score_calendar_bias, score_news_sentiment, combine_scores, compute_pair_biases
from telegram_bot import build_report, send_report
from config import RUN_INTERVAL_MINUTES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


def run_once():
    logger.info("Fetching economic calendar...")
    events = get_calendar_events()
    logger.info("Fetched %d calendar events.", len(events))

    logger.info("Fetching news headlines...")
    headlines = get_news_headlines()
    logger.info("Fetched %d headlines.", len(headlines))

    logger.info("Scoring calendar and news...")
    calendar_scores = score_calendar_bias(events)
    news_scores = score_news_sentiment(headlines)
    combined = combine_scores(calendar_scores, news_scores)
    pair_biases = compute_pair_biases(combined)

    report = build_report(combined, pair_biases)
    logger.info("Report:\n%s", report)

    logger.info("Sending report to Telegram...")
    ok = send_report(report)
    if ok:
        logger.info("Report sent successfully.")
    else:
        logger.error("Report failed to send. Check your Telegram config.")


def main():
    parser = argparse.ArgumentParser(description="Forex Fundamentals Analyser")
    parser.add_argument("--loop", action="store_true", help="Run continuously on a schedule")
    args = parser.parse_args()

    if not args.loop:
        run_once()
        return

    logger.info("Starting continuous mode: every %d minutes.", RUN_INTERVAL_MINUTES)
    while True:
        try:
            run_once()
        except Exception as e:
            logger.exception("Unhandled error in run cycle: %s", e)
        time.sleep(RUN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
