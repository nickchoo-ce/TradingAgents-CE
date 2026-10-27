# Dashboard page

One self-contained HTML page that presents a saved analysis: the call, the order plan, two charts, and every agent's report behind it. It is published as a claude.ai page; the file also opens in any browser.

## Build

From the repo root, with the package installed:

```bash
python dashboard/build.py analyses/NVDA_2026-10-27
```

This writes `dashboard/NVDA_2026-10-27.html`. Pass `--out` to write somewhere else.

## What is filled in, and what is not

- **Filled in by `build.py`:** the 12 agent reports, read from the analysis folder (`1_analysts/` to `5_portfolio/`) and rendered with the repo's Markdown renderer (raw HTML off).
- **Written by hand in `template.html`:** the top half, which is specific to the NVDA 2026-10-27 call. That covers the heading, rating, stat tiles, order plan, the price levels and revenue values in the two charts, the upgrade and downgrade triggers, the data caveats and the source list.

For a new analysis, update those parts of the template first, then run the build.
