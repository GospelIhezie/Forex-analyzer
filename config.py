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

# --- Real yields (FRED) and DXY (Yahoo Finance) ---
# FRED_API_KEY is free — request one at https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_REAL_YIELD_SERIES = "DFII10"  # 10-Year Treasury Inflation-Indexed real yield
YAHOO_DXY_URL = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB"

# =====================================================================
# XAU/USD (Gold) fundamentals — see gold_fundamentals/ package.
#
# Honesty note: a serious gold fundamentals model wants real yields, a live
# DXY level, ETF flow $ figures, central-bank purchase tonnage, and
# China/India demand data. Real yields (FRED) and DXY (Yahoo Finance) ARE
# now wired in above. The rest still have no free, reliable feed and are
# reported as "DATA UNAVAILABLE" rather than invented.
# =====================================================================

GOLD_MIN_IMPACT = "Medium"

# How much each computable category counts toward the total gold score.
# Fed/Rates, real yields and DXY are weighted highest since they're the
# most directly gold-relevant measurements available. USD Strength is
# weighted a bit lower than before now that DXY (an actual live price)
# covers similar ground from a different angle — keeping both isn't double
# counting, but it's related information, so it's weighted accordingly.
GOLD_CATEGORY_WEIGHTS = {
    "fed_rates": 2.5,
    "real_yields": 2.5,
    "dxy": 2.0,
    "usd_strength": 1.5,
    "inflation": 2.0,
    "geopolitical_risk": 2.0,
    "employment_growth": 1.0,
    "central_bank_demand": 1.0,
}

# Reported to the user as gaps, never filled in with invented numbers.
GOLD_UNAVAILABLE_FACTORS = [
    "Gold ETF flows (World Gold Council data)",
    "Central bank gold purchase volumes",
    "China gold demand",
    "India gold demand",
    "Gold price momentum/technicals",
]

GOLD_FED_KEYWORDS = ["fed", "fomc", "interest rate", "rate decision", "monetary policy"]
GOLD_INFLATION_KEYWORDS = ["cpi", "pce", "inflation"]
GOLD_GROWTH_KEYWORDS = [
    "nonfarm", "non-farm", "non farm", "payroll", "employment change",
    "unemployment", "gdp", "ism", "retail sales", "wage",
]

# Keyword lexicon for the geopolitical/risk-sentiment category. Same
# transparent, simple-on-purpose approach as the main analyser's news
# sentiment scoring — not a black-box model.
GOLD_BULLISH_NEWS_WORDS = {
    "war", "conflict", "tension", "tensions", "sanctions", "geopolitical",
    "crisis", "safe-haven", "safe haven", "flight to safety", "escalation",
    "escalates",
}
GOLD_BEARISH_NEWS_WORDS = {
    "ceasefire", "peace deal", "de-escalation", "de-escalate", "risk-on",
    "risk rally", "truce",
}

# Keyword lexicon for the (headline-presence-only) central bank / demand
# category — see scoring.py docstring for why this is treated as a weak,
# low-confidence signal rather than a quantified one.
GOLD_DEMAND_KEYWORDS = [
    "central bank gold", "gold reserves", "gold etf", "gold demand",
    "buying gold", "selling gold",
]

# Local-time schedule the user asked for (08:00/12:00/16:00/20:00 WAT,
# UTC+1) converted to UTC for the GitHub Actions cron in
# .github/workflows/gold-bot.yml — cron always runs in UTC.
GOLD_SCHEDULE_HOURS_UTC = [7, 11, 15, 19]
