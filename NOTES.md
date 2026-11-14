# NOTES.md — overnight crew checkpoint (not for commit)

## Team Rules (read before acting)

Set by Nick, 2026-11-14 02:10 UTC.

1. **Scope / done**: the crew hunts for real defects. An issue exists only once a
   failing test proves it. Done = failing-then-passing test, green full suite,
   reviewed diff, draft PR. Maximum 4 fixes tonight.
2. **Off-limits**: nothing beyond the standing rules — no secrets, production
   data, migrations, billing or anything public without Nick's yes.
3. **Proof gate (mirror CI)**: `pip install -e ".[dev]"`, `pytest -q` (full
   suite), and the ruff check from `.github/workflows/ci.yml`. No live LLM or
   market-data calls.
4. **Budget**: brief due 07:30 UTC. Max 4 parallel builders. Stuck 20 minutes →
   write one question, park, move on.

Standing rules: never weaken, skip or delete a test. No new dependency without a
reason in the PR. No refactors beyond the issue. Smallest change that turns the
test green wins. Handoffs use ISSUE / TEST / EVIDENCE / NEXT STEP.

## Status

- 02:10 UTC — intake complete. Waiting for Nick's go. Nothing mapped, no
  baseline run yet.

## Map

Mapper, appended 08:10 UTC by the container clock (`date -u`; it reads later than the 02:20 the lead logged).
Read: backtest, date_window, memory/*, graph/trading_graph+checkpointer+propagation, symbols, portfolio,
default_config, dataflows/config+router+files, yahoo/*, sec_edgar, alpha_vantage (not indicator), fred,
polymarket, cli/main+run and the ticker/date part of cli/prompts. Only skimmed: llm_clients/*, agents/*
prompts and schemas, cli/display+selections+prefs+updates, report_html, stocktwits/reddit beyond windowing.

### Commands
- Install: `pip install -e ".[dev]"` (done).
- Tests: `python -m pytest -q`, NOT bare `pytest` (the one on PATH is an isolated uv tool without project deps).
  Baseline 02:20 UTC: 1412 passed, 1 skipped, 1 deselected, in UTC and with `TZ=America/New_York`; ~20 s.
  Also green at 08:01 UTC with `TZ=Pacific/Pago_Pago` (local date one behind UTC).
- Lint: `ruff check .` — baseline clean.
- Offline probes: fake `settlement.get_closes`, or drop a `<SYM>-YFin-data.csv` into a temp `data_cache_dir`.

### Module seams
- `tradingagents/default_config.py` — DEFAULT_CONFIG built at import, TRADINGAGENTS_* env folded in (`_coerce`). Imported everywhere.
- `dataflows/config.py` — process config plus per-run ContextVar (`run_config`); every vendor reads `get_config()`.
- `dataflows/date_window.py` — point-in-time rules (`as_of`, `as_of_window`, `in_window`, `coverage_gap`, `withhold_*`). Pure; used by tools and every vendor.
- `dataflows/symbols.py` — `normalize_symbol`, `crypto_base`, `safe_ticker_component`. Pure; used by CLI, vendors, checkpointer, portfolio, settlement.
- `dataflows/router.py` — `route_to_vendor`: vendor chain and NO_DATA / DATA_UNAVAILABLE sentinels. Imports all vendors.
- `dataflows/files.py` — `replace_file` (atomic cache write), `locked` (flock). Used by the OHLCV cache, SEC cache, memory log.
- `dataflows/vendors/yahoo/` — `ohlcv.py` (5y per-symbol CSV cache, look-ahead filter, stale guard), `market.py` (prices, indicators, `get_closes`), `news.py`, `fundamentals.py`, `snapshot.py`. Only place allowed to import yfinance (tests/test_layering.py).
- `dataflows/vendors/{sec_edgar,fred,polymarket,stocktwits,reddit}.py`, `alpha_vantage/` — one vendor each, independent of each other.
- `agents/tools.py` — LangChain tools; clamp model-supplied dates to state `trade_date`, then call the router.
- `agents/rating.py` — 5-tier rating parser, REVIEW sentinel. Used by memory log, backtest, reporting, CLI.
- `agents/context.py` — instrument identity, language, portfolio prompt blocks. `agents/{analysts,researchers,managers,risk_mgmt,trader}` — one node each; `schemas.py`/`structured.py` structured output.
- `graph/trading_graph.py` — orchestrator: `propagate`, checkpoint begin/end, `_memory_step`, `record_decision`, `_log_state`. `setup.py` wiring, `conditional_logic.py` round counts, `checkpointer.py` per-ticker SQLite.
- `memory/log.py` — markdown memory log (store, settle, rotate, parse). `memory/settlement.py` — returns and alpha vs benchmark. `memory/reflection.py` — LLM lesson.
- `backtest.py` — grid, sweep into a run-private log, `summarize`. Depends on graph + memory log.
- `portfolio.py` — caller's book rendered for the agents; fingerprint feeds the checkpoint signature.
- `reporting.py` / `report_html.py` — report tree and single HTML page.
- `llm_clients/` — provider factory, per-provider clients, capabilities table, model catalog, ChatGPT sign-in.
- `cli/` — `main.py` (typer: analyze, backtest, login/logout), `run.py` (live run), `selections.py`+`prompts.py` (questions, ticker/date parsing), `prefs.py`, `updates.py`, `display.py`.

### Risky files
- `dataflows/date_window.py` — mixes local date (`get_current_date`, `is_historical`) with UTC now (`in_window`, `coverage_gap`); every dated tool depends on it.
- `memory/settlement.py` — entry/exit bar selection, tz-aware vs naive indexes, "today's bar is unsettled". Heavily tested; behaved correctly on every synthetic case tried.
- `memory/log.py` — hand-rolled text format (tag line, `DECISION:`, `REFLECTION:`, separator); both writers must stay in step with `_parse_entry`.
- `dataflows/vendors/yahoo/ohlcv.py` — cache freshness by mtime and TTL, 5-year window anchored on today, look-ahead filter.
- `dataflows/symbols.py` — changes ripple into cache filenames, checkpoint DB names, benchmark choice, portfolio matching.
- `graph/trading_graph.py` — `_run_signature` (any config key changes the checkpoint thread id), `_NOT_IN_SIGNATURE`.
- `default_config.py` / `cli/run.py::_build_run_config` — env vs flag vs prompt precedence; tests pin it (test_cli_config_precedence, test_env_overrides).
- `agents/rating.py` — regexes decide whether a run is tradeable or REVIEW.

### Bug-hunt leads (ranked; no existing test covers any of these paths)
The money core (backtest.py, settlement.py, as_of/as_of_window) held up under probing; the leads sit around it.
1. CONFIRMED — `dataflows/vendors/yahoo/ohlcv.py:183` + `market.py:217,282`: the cache holds 5 years back from
   today, and indicators run on whatever is cached, so a backtest dated near the start of that window gets
   long averages over a truncated history. Cache starting 2021-11-15, `close_200_sma` for 2022-01-10 returned
   10.15 from ~40 bars, labelled as a 200 SMA. The "verified snapshot" (`snapshot.py:78`) has the same input.
2. CONFIRMED — same path, date before the cached window: `load_ohlcv("ZZZ","2020-06-01")` returns 0 rows and
   `get_indicators` prints every day, trading days included, as "N/A: Not a trading day (weekend or holiday)"
   instead of NO_DATA_AVAILABLE (`market.py:172`).
3. CONFIRMED — `portfolio.py:57,60,67`: quantities use `:,.4g`. 12345 units renders "1.234e+04 units", 100000
   renders "1e+05", 1500.5 renders "1,500"; average price 0.00001234 renders "0.00". The sizing agents get
   a wrong or unreadable position. Tests only use quantities of 1 and 2.
4. CONFIRMED — `backtest.py:226` with `memory/log.py:164-165`: alpha is stored rounded to 0.1pp and
   `a * direction > 0` scores a rounded 0.0 as a miss. Four Buy calls with alpha +0.02% to +0.04% give
   `hit_rate=0.0`. Docstring admits the 0.1pp precision but not that it flips hits to misses.
5. CONFIRMED — `memory/log.py:17-18,338-341`: a decision containing a line `REFLECTION:` (the PM is shown past
   entries in exactly that format) is cut there: `decision` loses its tail, and after settlement `reflection`
   becomes the tail plus a second `REFLECTION:` block. The truncated decision is also what the reflector is sent.
   Mechanically confirmed; how often a model quotes the label is unknown.
6. CONFIRMED — `dataflows/symbols.py:43-45` vs `cli/prompts.py:135-141`: asset type is decided by suffix
   (`-USD`, `-BTC`, ...) but `crypto_base` knows 11 coins. SHIB-USD, BNB-USD, MATIC-USD, ETH-BTC run as crypto,
   yet StockTwits is asked for `SHIB-USD` (the form its own docstring says 404s) and Reddit searches
   wallstreetbets/stocks/investing. `stocktwits.py:70`, `reddit.py:89,278`.
7. CONFIRMED — `dataflows/date_window.py:63` (`coverage_gap`): run date is validated against the local date,
   the gap check against the UTC date. At 08:30 in Tokyo (23:30 UTC the day before) a live run's empty window
   reports "unavailable ... the window extends past today" instead of "no messages". Simulated by patching
   the clock; no test runs east of UTC.
8. SUSPECTED — `cli/main.py:138-150`: `backtest` passes tickers raw. The analyze path runs `parse_ticker`
   (normalise + path-safety) and auto-detects crypto; backtest does neither, so `nvda,NVDA` are two cells,
   `BTC-USD` runs the stock pipeline unless `--asset-type crypto`, and a path-unsafe ticker is only rejected
   in `_log_state` after the whole graph has run for every date. Read from code, not executed.
9. CONFIRMED (payload-dependent) — `polymarket.py:62-64`: a date-only `endDate` ("2027-01-31") raises
   TypeError (naive vs aware), which the `except ValueError` misses; the router then degrades the whole
   call to DATA_UNAVAILABLE. Whether Gamma ever sends a date-only `endDate` is unverified.
10. CONFIRMED (low) — `agents/rating.py:37-49`: `__Rating__: __Buy__` parses as REVIEW because `\w+` swallows
    the underscores, as do `Rating: [Buy]` and a backticked Buy. Fallback path only: the PM's structured
    output normally supplies `final_rating`.
Not defects, noted so nobody re-walks them: lower-case tickers through `propagate()` make separate log
entries from upper-case (CLI normalises first); `in_window` is UTC by documented design, so a US-evening live
run drops articles stamped after 00:00 UTC.

## Run log (lead)

- Clock correction: the go ("Option A") arrived about 07:50 UTC, not 02:20. Baseline was run about 07:55 UTC.
  The 07:30 UTC brief time had already passed at go. Lead is proceeding with a tight run and will say so in the brief.
- 08:10 UTC — Map done. Issues chosen (one worktree and branch each, cut from origin/main):
  - A `claude/fix-portfolio-quantity-format` at /home/user/wt-portfolio-quantity-format — lead 3. Owns `tradingagents/portfolio.py`.
  - B `claude/fix-indicator-history-guard` at /home/user/wt-indicator-history-guard — leads 2 and 1. Owns `tradingagents/dataflows/vendors/yahoo/market.py` (+ `snapshot.py` only if needed).
  - C `claude/fix-crypto-sentiment-base` at /home/user/wt-crypto-sentiment-base — lead 6. Owns `tradingagents/dataflows/vendors/stocktwits.py`, `reddit.py`.
  - D `claude/fix-memory-reflection-marker` at /home/user/wt-memory-reflection-marker — lead 5. Owns `tradingagents/memory/log.py`.
- Parked: lead 4 (needs Nick's design decision), 7, 8, 9, 10 (lower value or unverified; not attempted).
- Next: Breaker commits one failing test per issue on its branch.
