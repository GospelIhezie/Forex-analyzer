"""
Telegram delivery layer.

Sends a formatted fundamentals report to a Telegram channel/group via the
Bot API. Create a bot with @BotFather, add it as an admin to your channel,
and set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in your .env file.
"""

import logging
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/sendMessage"

BIAS_EMOJI = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "⚪"}


def build_report(combined_scores: dict) -> str:
    lines = ["*📊 Forex Fundamentals Digest*", ""]

    # Sort strongest bias first (absolute score)
    ranked = sorted(combined_scores.items(), key=lambda kv: abs(kv[1]["score"]), reverse=True)

    for currency, data in ranked:
        emoji = BIAS_EMOJI.get(data["bias"], "⚪")
        lines.append(f"{emoji} *{currency}* — {data['bias']} (score: {data['score']:+.2f})")

        for ev in data["calendar_events"][:3]:
            arrow = "↑" if ev["beat"] else "↓"
            lines.append(
                f"    {arrow} {ev['title']} ({ev['impact']}): "
                f"actual {ev['actual']} vs fcst {ev['forecast']}"
            )

        for headline in data["news_hits"][:2]:
            lines.append(f"    📰 {headline}")

        lines.append("")

    lines.append("_Automated fundamentals summary — not financial advice._")
    return "\n".join(lines)


def send_report(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set. Check your .env file.")
        return False

    # Telegram messages are capped at 4096 characters; split if needed.
    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)] or [text]

    for chunk in chunks:
        try:
            resp = requests.post(
                API_URL.format(token=TELEGRAM_BOT_TOKEN),
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": chunk,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            resp.raise_for_status()
        except Exception as e:
            logger.error("Failed to send Telegram message: %s", e)
            return False

    return True
