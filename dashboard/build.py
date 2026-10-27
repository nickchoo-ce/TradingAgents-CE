"""Build the dashboard page from a saved analysis.

Fills ``dashboard/template.html`` with the 12 agent reports of one analysis,
rendered by the repo's own Markdown renderer, and writes one self-contained page.

    python dashboard/build.py analyses/NVDA_2026-10-27
    python dashboard/build.py analyses/NVDA_2026-10-27 --out dashboard/NVDA.html

The page's summary half (rating, order plan, chart values, triggers, sources)
lives in the template itself; update it there for a new analysis. See README.md.
"""

import argparse
import json
from pathlib import Path

from tradingagents.report_html import _markdown, _render_agent_text

HERE = Path(__file__).resolve().parent

# Report tree written by tradingagents.reporting.write_report_tree.
FILES = {
    "market": "1_analysts/market.md", "sentiment": "1_analysts/sentiment.md",
    "news": "1_analysts/news.md", "fundamentals": "1_analysts/fundamentals.md",
    "bull": "2_research/bull.md", "bear": "2_research/bear.md", "manager": "2_research/manager.md",
    "trader": "3_trading/trader.md",
    "aggressive": "4_risk/aggressive.md", "conservative": "4_risk/conservative.md",
    "neutral": "4_risk/neutral.md", "decision": "5_portfolio/decision.md",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("analysis", type=Path, help="a saved analysis folder, e.g. analyses/NVDA_2026-10-27")
    parser.add_argument("--template", type=Path, default=HERE / "template.html")
    parser.add_argument("--out", type=Path, help="default: dashboard/<analysis folder name>.html")
    args = parser.parse_args()

    missing = [rel for rel in FILES.values() if not (args.analysis / rel).exists()]
    if missing:
        parser.error(f"{args.analysis} is missing: {', '.join(missing)}")

    md = _markdown()
    reports = {key: _render_agent_text(md, (args.analysis / rel).read_text(encoding="utf-8"))
               for key, rel in FILES.items()}
    # </ inside a JSON string must not close the <script> element.
    payload = json.dumps(reports, ensure_ascii=False).replace("</", "<\\/")
    html = args.template.read_text(encoding="utf-8").replace("/*__REPORTS__*/", payload, 1)

    out = args.out or HERE / f"{args.analysis.name}.html"
    out.write_text(html, encoding="utf-8")
    print(f"{out} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
