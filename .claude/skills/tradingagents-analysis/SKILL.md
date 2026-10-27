---
name: tradingagents-analysis
description: Run a full TradingAgents-style investment analysis of one stock or crypto ticker by playing every agent role yourself — four analysts, bull/bear debate, research manager, trader, three risk analysts, portfolio manager — and save it in the repo's own report format (Markdown tree + HTML page). Use when asked to analyze, rate, or give a buy/hold/sell view on a ticker (e.g. "analyze NVDA", "should I buy 0700.HK", "run TradingAgents on BTC-USD"), especially when no LLM API key is configured or the repo's data vendors are unreachable, so `tradingagents` / `propagate()` cannot run.
---

# TradingAgents analysis, run by hand

This repo's graph (`tradingagents/graph/`) runs each role as an LLM call over data from its vendors. This skill does the same pipeline in-session: **you** are each agent, and data comes from whatever you can reach.

The source of truth for every role is its prompt under `tradingagents/agents/`. Re-read the relevant file before writing that role if anything below seems out of date.

## 0. Prefer the real thing

If an LLM key is set (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …) **and** `query1.finance.yahoo.com` is reachable, run the actual framework instead:

```bash
tradingagents --ticker NVDA --date 2026-10-27 --analysts market,social,news,fundamentals --save --no-show
```

Otherwise continue with this skill.

## 1. Inputs to confirm

- **Ticker** with exchange suffix (`AAPL`, `0700.HK`, `7203.T`, `BTC-USD`). Crypto skips the fundamentals analyst.
- **Analysis date**: default today. It is "now" for every role; never use data published after it.
- **Holdings**: none, or shares + cost. If held, trader/risk/PM advise on the actual position.

## 2. Gather data

Try the repo's vendors first (`tradingagents/dataflows/vendors/`). If blocked, use web search, run in parallel:

| Analyst | Needs |
|---|---|
| Market | last close + intraday, 52w range, recent swing high/low, 50/200 SMA, 10 EMA, RSI, MACD, Bollinger, ATR, support/resistance |
| Fundamentals | last 4 quarters revenue/segments/margins/EPS, current guidance, buybacks/dividend, valuation (mkt cap, fwd P/E, P/S), analyst targets, insider transactions (Form 4) |
| News | past-week company news, sector moves, macro (policy rate, CPI/PCE, next central-bank meeting + market-implied odds), geopolitics/regulation, next earnings date |
| Sentiment | StockTwits gauge / bull-bear ratio, Reddit (wallstreetbets, stocks, investing), news tone |

**Data integrity rules (from the repo — non-negotiable):**
- Cite a source and date for every number. Where sources conflict, show the range and say which is better supported; never invent a reconciled figure.
- If a figure cannot be found (often ATR, insider trades), say **unavailable** — do not estimate it silently. Derived numbers are labeled "derived".
- Open each analyst report with a **Data note** stating which vendors were unreachable and what replaced them.

## 3. Write the roles, in order

Write each to `<scratch>/<TICKER>/<file>.md`. Every analyst report ends with a Markdown summary table.

1. **Market Analyst** → `market.md`. Choose ≤8 complementary indicators (no redundant pairs), explain why each fits the current regime, read trend/momentum/levels, give up/down trigger prices.
2. **Sentiment Analyst** → `sentiment.md`. Header line: `**Overall band:** <Bullish|Mildly Bullish|Neutral|Mixed|Mildly Bearish|Bearish> | **Score:** <0–10> | **Confidence:** <low|medium|high>`. Source-by-source, cross-source divergences, dominant narrative, catalysts/risks. Low confidence when feeds were summarized rather than read.
3. **News Analyst** → `news.md`. Company, sector, macro, policy; each with a one-line "read" of what it means for the ticker.
4. **Fundamentals Analyst** → `fundamentals.md`. Quarterly trajectory table, margins, guidance, capital return, valuation table, insider activity.
5. **Bull Researcher** → `bull.md`, prefixed `Bull Analyst:`. Conversational, evidence-based; pre-empt the bear.
6. **Bear Researcher** → `bear.md`, prefixed `Bear Analyst:`. Rebut the bull point by point.
7. **Research Manager** → `manager.md`. `**Recommendation:** <Buy|Overweight|Hold|Underweight|Sell>`, then Rationale, then Strategic Actions. Conflict alone is not a Hold — pick the stronger side, size by how decisively it wins.
8. **Trader** → `trader.md`. `**Action:** <Buy|Hold|Sell>` (Overweight→Buy, Underweight→Sell, smaller size). Entry and stop as **absolute prices**, grounded in the market report's levels; position sizing with risk-to-stop as % of portfolio.
9. **Aggressive / Conservative / Neutral risk analysts** → `aggressive.md`, `conservative.md`, `neutral.md`, prefixed `<Name> Analyst:`, plain conversational prose, each rebutting the other two on the trader's plan.
10. **Portfolio Manager** → `decision.md`. `**Rating:** <5-tier>`, then **Executive summary** (how to act), then **Investment thesis** (what decided it, and explicit downgrade/upgrade triggers). End with a not-investment-advice line.

Keep numbers consistent across roles (entry, stop, sizing, triggers): the PM's plan must be arithmetically consistent with the trader's.

## 4. Render with the repo's writer

```bash
python .claude/skills/tradingagents-analysis/scripts/render.py <scratch>/<TICKER> <TICKER> <YYYY-MM-DD> <Rating> \
  --out analyses/<TICKER>_<YYYY-MM-DD> --vendors "web search (…blocked list…)"
```

It calls `tradingagents.reporting.write_report_tree`, producing `complete_report.md`, `complete_report.html` and the `1_analysts/ … 5_portfolio/` tree exactly as a real run would. Send the user the HTML.

## 5. Report back

Give the rating, the action plan (entry / stop / sizing / triggers) and the main reasons in a few lines, and state plainly which data was unverified or unavailable. Never present the result as financial advice.
