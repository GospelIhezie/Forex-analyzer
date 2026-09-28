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

# --- Real yields, USD index (FRED) and DXY/gold/oil/VIX (Yahoo Finance) ---
# FRED_API_KEY is free — request one at https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_REAL_YIELD_SERIES = "DFII10"  # 10-Year Treasury Inflation-Indexed real yield
YAHOO_DXY_URL = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB"
YAHOO_GOLD_URL = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"   # COMEX gold futures — momentum only, not scored
YAHOO_OIL_URL = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F"    # WTI crude — context only, not scored
YAHOO_VIX_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"  # CBOE VIX — used for risk-sentiment scoring

# =====================================================================
# XAU/USD (Gold) fundamentals — see gold_fundamentals/ package.
#
# Honesty note: a serious gold fundamentals model wants real yields, a live
# DXY level, VIX/risk sentiment, ETF flow $ figures, central-bank purchase
# tonnage, China/India demand, CFTC positioning, and CME FedWatch-style
# rate-cut probabilities. Real yields, DXY, and VIX are wired in via free
# sources (FRED, Yahoo Finance). The rest genuinely have no free API this
# project has integrated yet:
#   - World Gold Council (ETF flows, central-bank tonnage, China/India
#     demand): no public API, only manual PDF/CSV reports — not automatable
#     without a paid data vendor.
#   - CME FedWatch: proprietary, no free API.
#   - CFTC gold futures positioning: DOES have a free public dataset
#     (Socrata), not yet integrated here — a reasonable next addition.
#   - BLS (CPI/NFP/wages) and BEA (PCE/GDP): both have free APIs requiring
#     their own signup — not yet integrated, since the ForexFactory
#     calendar already covers releases of these same indicators; adding
#     BLS/BEA would mainly improve precision, not add a wholly new signal.
# These stay reported as "DATA UNAVAILABLE" rather than invented.
# =====================================================================

GOLD_MIN_IMPACT = "Medium"

# How much each computable category counts toward the total gold score.
#
# IMPORTANT: earlier versions of this file had a separate "usd_strength"
# factor (derived from the Forex analyser's calendar+news-based USD score)
# ALONGSIDE "dxy" (a live market price). Both were measuring the same
# underlying thing — dollar strength — from two angles, which silently
# double-counted USD's influence on the total score. usd_strength has been
# removed; DXY (backed by an actual traded price) is now the sole
# dollar-strength input, with its weight increased to reflect that it's
# doing that job alone.
GOLD_CATEGORY_WEIGHTS = {
    "fed_rates": 2.5,
    "real_yields": 2.5,
    "dxy": 3.0,
    "inflation": 2.0,
    "geopolitical_risk": 2.0,
    "risk_sentiment": 1.5,
    "employment_growth": 1.0,
    "central_bank_demand": 1.0,
}

# Reported to the user as gaps, never filled in with invented numbers.
GOLD_UNAVAILABLE_FACTORS = [
    "Gold ETF flows (World Gold Council data — no public API)",
    "Central bank gold purchase volumes (World Gold Council — no public API)",
    "China gold demand (World Gold Council — no public API)",
    "India gold demand (World Gold Council — no public API)",
    "CFTC gold futures positioning (free data exists, not yet integrated)",
    "CME FedWatch rate-cut/hike probabilities (proprietary, no free API)",
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
