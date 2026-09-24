"""
Configuration for the Forex Fundamentals Analyser.

Copy `.env.example` to `.env` and fill in your own values.
Nothing here should be committed with real secrets in it.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # channel/group/user id, e.g. "@your_channel" or "-1001234567890"

# --- Economic calendar source ---
# ForexFactory publishes a free, unauthenticated JSON feed of the week's calendar.
# This is the same data their website widget uses.
FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# --- News sources (public RSS feeds — no scraping/anti-bot issues) ---
NEWS_FEEDS = {
    "FXStreet": "https://www.fxstreet.com/rss/news",
    "Investing.com Forex News": "https://www.investing.com/rss/news_1.rss",
    "DailyFX": "https://www.dailyfx.com/feeds/all",
}

# --- Analysis thresholds ---
# Only events at/above this impact level are scored in the fundamentals bias.
MIN_IMPACT = "Medium"  # "Low", "Medium", or "High"

# How much weight an actual-vs-forecast beat/miss carries, per impact level.
IMPACT_WEIGHTS = {
    "High": 3,
    "Medium": 1.5,
    "Low": 0.5,
}

# Currencies to track and report on.
TRACKED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]

# Standard FX market pair conventions — (base, quote) in the order the market
# actually quotes them. This matters: EUR/USD and USD/EUR are NOT the same
# pair, and getting the base/quote backwards flips the correct trade
# direction. This list intentionally does not include every possible
# combination of TRACKED_CURRENCIES — only the pairs as the market quotes
# them (majors here; add crosses like EUR/GBP or EUR/JPY if you want them).
STANDARD_FX_PAIRS = [
    ("EUR", "USD"),
    ("GBP", "USD"),
    ("AUD", "USD"),
    ("NZD", "USD"),
    ("USD", "JPY"),
    ("USD", "CAD"),
    ("USD", "CHF"),
]

# How many news headlines per source to pull for sentiment scoring.
NEWS_ITEMS_PER_SOURCE = 8

# Run interval in minutes when running in continuous/scheduled mode.
RUN_INTERVAL_MINUTES = 60
