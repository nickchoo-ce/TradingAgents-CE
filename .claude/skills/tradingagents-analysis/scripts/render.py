"""Render hand-written agent reports into the repo's report tree (Markdown + HTML).

Usage:
    python render.py <reports_dir> <TICKER> <YYYY-MM-DD> <Rating> [--out DIR] [--vendors TEXT]

<reports_dir> holds market.md, sentiment.md, news.md, fundamentals.md, bull.md,
bear.md, manager.md, trader.md, aggressive.md, conservative.md, neutral.md and
decision.md. A missing file leaves its section out, as an unselected analyst does.
"""

import argparse
from pathlib import Path

from tradingagents import __version__
from tradingagents.agents.rating import RATINGS_5_TIER
from tradingagents.reporting import write_report_tree


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("reports_dir", type=Path)
    parser.add_argument("ticker")
    parser.add_argument("trade_date")
    parser.add_argument("rating", choices=RATINGS_5_TIER)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--vendors", default="web search")
    args = parser.parse_args()

    def read(name):
        path = args.reports_dir / f"{name}.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    state = {
        "company_of_interest": args.ticker,
        "trade_date": args.trade_date,
        "market_report": read("market"),
        "sentiment_report": read("sentiment"),
        "news_report": read("news"),
        "fundamentals_report": read("fundamentals"),
        "investment_debate_state": {"bull_history": read("bull"), "bear_history": read("bear")},
        "investment_plan": read("manager"),
        "trader_investment_plan": read("trader"),
        "risk_debate_state": {
            "aggressive_history": read("aggressive"),
            "conservative_history": read("conservative"),
            "neutral_history": read("neutral"),
        },
        "final_trade_decision": read("decision"),
        "final_rating": args.rating,
        "memory_note": "Run by hand in a Claude Code session following the repo's agent prompts "
                       "(.claude/skills/tradingagents-analysis); data sources are cited inline.",
    }
    analysts = [key for key, name in (("market", "market"), ("social", "sentiment"),
                                      ("news", "news"), ("fundamentals", "fundamentals")) if read(name)]
    settings = {
        "version": __version__,
        "llm_provider": "claude-code-session",
        "deep_think_llm": "manual",
        "quick_think_llm": "manual",
        "analysts": analysts,
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
        "data_vendors": {"all": args.vendors},
    }
    out = args.out or Path("analyses") / f"{args.ticker}_{args.trade_date}"
    report = write_report_tree(state, args.ticker, out, settings=settings)
    print(report.parent / "complete_report.html")


if __name__ == "__main__":
    main()
