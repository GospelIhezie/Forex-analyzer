# Forex Fundamentals Analyser

Pulls economic calendar events + forex news, scores a bullish/bearish
fundamentals bias per currency, and posts a digest to a Telegram channel.

## How it works

1. **scraper.py** pulls:
   - This week's economic calendar from ForexFactory's public JSON feed
   - Recent forex headlines from FXStreet, Investing.com, and DailyFX RSS feeds
2. **analyzer.py**:
   - Compares actual vs. forecast for released events (weighted by impact:
     High/Medium/Low) → per-currency calendar bias score
   - Runs a lightweight keyword sentiment pass over headlines → per-currency
     news bias score
   - Combines both into a Bullish / Bearish / Neutral verdict per currency
3. **telegram_bot.py** formats and sends the report to your channel.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a Telegram bot:
   - Message **@BotFather** on Telegram → `/newbot` → follow the prompts
   - Copy the token it gives you

3. Add the bot to your channel:
   - Add the bot as an **admin** of your channel (needed to post)
   - Get your channel's chat ID:
     - Public channel: use `@your_channel_username` directly
     - Private channel: forward a message from it to `@userinfobot`, or use
       `https://api.telegram.org/bot<TOKEN>/getUpdates` after posting a
       message in the channel to find the numeric chat ID (looks like
       `-1001234567890`)

4. Configure environment variables:
   ```
   cp .env.example .env
   # then edit .env with your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
   ```

5. Run once:
   ```
   python main.py
   ```

   Or run continuously (checks every `RUN_INTERVAL_MINUTES`, set in `config.py`):
   ```
   python main.py --loop
   ```

   For production, it's more reliable to run `python main.py` on a cron job
   (e.g. every hour) rather than `--loop` in a long-lived process — cron
   survives crashes and reboots without extra supervision code.

## Customizing

- `config.py` → adjust `MIN_IMPACT`, `IMPACT_WEIGHTS`, `TRACKED_CURRENCIES`,
  `NEWS_FEEDS`, and `RUN_INTERVAL_MINUTES`
- `analyzer.py` → the sentiment lexicon (`BULLISH_WORDS`/`BEARISH_WORDS`) is
  intentionally simple and readable. Swap in a proper NLP model (e.g. a
  finance-tuned sentiment classifier) if you want more nuance.

## Notes on data sources

- The ForexFactory calendar feed and the RSS feeds used here are public,
  unauthenticated endpoints meant for programmatic consumption — this avoids
  the fragility and ToS risk of scraping rendered HTML pages directly.
- If a feed changes its URL or format, `scraper.py` is the only file you
  need to touch — it logs errors clearly rather than crashing the whole run.
- This tool produces an automated summary of publicly available data. It is
  not financial advice, and fundamentals scoring here is a simple heuristic,
  not a trading signal generator — use it as a starting point for your own
  analysis.
