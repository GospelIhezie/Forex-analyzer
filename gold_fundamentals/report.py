
"""
gold_fundamentals/report.py

Formats the XAU/USD fundamental analysis into a plain-text Telegram
message. Plain text on purpose, same reason as the main Forex digest:
headline text is unpredictable and breaks Telegram's Markdown parser if it
contains stray *, _, [, ] characters.
"""

from datetime import datetime, timezone

CATEGORY_ORDER = [
    "fed_rates", "real_yields", "dxy", "usd_strength", "inflation",
    "geopolitical_risk", "employment_growth", "central_bank_demand",
]
BIAS_EMOJI = {
    "VERY BULLISH": "🟢", "BULLISH": "🟢", "NEUTRAL": "⚪",
    "BEARISH": "🔴", "VERY BEARISH": "🔴",
}


def build_gold_report(analysis: dict) -> str:
    lines = ["\U0001F947 XAU/USD FUNDAMENTALS DIGEST", ""]

    emoji = BIAS_EMOJI.get(analysis["bias"], "⚪")
    lines.append(f"{emoji} {analysis['bias']}")
    lines.append(f"Score: {analysis['total_score']:+.1f} / 10")
    lines.append(f"Confidence: {analysis['confidence']} (data coverage: {analysis['data_coverage_pct']}%)")
    lines.append("")

    lines.append("CATEGORY BREAKDOWN")
    for key in CATEGORY_ORDER:
        cat = analysis["categories"][key]
        if cat["available"]:
            if cat["raw_score"] > 0.15:
                sign = "🟢"
            elif cat["raw_score"] < -0.15:
                sign = "🔴"
            else:
                sign = "⚪"
            lines.append(f"  {sign} {cat['label']}: {cat['raw_score']:+.2f}")
        else:
            lines.append(f"  ⚪ {cat['label']}: DATA UNAVAILABLE")
    lines.append("")

    if analysis["bullish_factors"]:
        lines.append("MAIN BULLISH FACTORS")
        for f in analysis["bullish_factors"]:
            lines.append(f"  - {f['label']}: {f['reason']}")
        lines.append("")

    if analysis["bearish_factors"]:
        lines.append("MAIN BEARISH FACTORS")
        for f in analysis["bearish_factors"]:
            lines.append(f"  - {f['label']}: {f['reason']}")
        lines.append("")

    if analysis["conflict"]:
        lines.append("WARNING: FUNDAMENTAL CONFLICT")
        lines.append("  Bullish side:")
        for f in analysis["bullish_factors"]:
            lines.append(f"    - {f['label']}")
        lines.append("  Bearish side:")
        for f in analysis["bearish_factors"]:
            lines.append(f"    - {f['label']}")
        lines.append("")

    lines.append("DATA NOT AVAILABLE (excluded from the score, not invented):")
    for name in analysis["unavailable_factors"]:
        lines.append(f"  - {name}")
    lines.append("")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"Last updated: {now}")
    lines.append("Automated fundamentals summary — not financial advice.")

    return "\n".join(lines)
