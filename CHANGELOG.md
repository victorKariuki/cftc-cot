# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-06-21

### Fixed
- `COTQuery.last_n_weeks(n)` now anchors to the dataset's actual most-recent
  report dates instead of a `datetime.now()`-relative window. CFTC publishes
  weekly with a multi-day lag, so the old window could sit entirely newer than
  the latest report and return nothing — e.g. a 1-week lookback came back empty
  while 2 weeks returned data. It now filters to rows on/after the N-th most
  recent `report_date_as_yyyy_mm_dd`, so "N weeks" reliably means the N most
  recent reports and never empties out from publishing lag. Trusting the data's
  own report dates (rather than week arithmetic) also handles holiday-shifted
  dates. Falls back to a now-anchored window only when no data matches.
  `list_markets`, `list_exchanges`, `history`, `compare`, and
  `classifications_for` all inherit the fix.

## [0.5.0] - 2026-06-21

### Added
- `COTAnalysis.cot_index_multi(windows=(26, 52, 156))` — COT Index at several
  rolling windows (`{cat}_cot_index_w{N}`) for a term-structure view; windows
  longer than the available history are skipped.
- `COTAnalysis.masking()` — quantifies how much the coarse (legacy) view hides an
  internal split: gross vs net positioning, masking ratio, and component
  correlation per parent trader group (disaggregated/tff).
- `COTClient.classifications_for(market, weeks=None)` — which classifications
  contain a market.
- `COTClient.compare(markets, classifications=None, weeks=156, windows=())` — a
  tidy long frame (`market, exchange, classification, category, date, net,
  cot_index, zscore` + per-window) for cross-market/cross-classification analysis.

### Changed
- **`COTAnalysis.extremes()` defaults changed** (improves signal quality): default
  `threshold` raised 0.9 → 0.95, the incomplete-window "ramp" is no longer flagged,
  and a new `persistence=2` requires a reading to stay extreme for ≥N consecutive
  weeks. The old behavior flagged ~38% of weeks; pass `persistence=1` for the prior
  no-persistence behavior. The `cftc-cot-mcp` `extremes` tool inherits this.

## [0.4.0] - 2026-06-20

### Added
- `COTQuery.exchange(name, exact=False)` — filter by exchange (the trailing
  component of `market_and_exchange_names`).
- `COTQuery.distinct_values(column)` — fetch a column's distinct values honoring
  the current filters; powers market/exchange discovery within a date window.
- `COTClient.list_markets(dataset, weeks=None, exchange=None)` — optional `weeks`
  restricts the result to markets that reported in the last N weeks (retired
  contracts drop out), plus optional `exchange` filtering.
- `COTClient.list_exchanges(dataset, weeks=None)` and the
  `COTClient.split_market_exchange(name)` helper.

### Changed
- `list_markets` now returns a sorted, de-duplicated list and no longer truncates
  at the SODA2 default page size of 1000.

## [0.3.0] - 2026-06-20

### Added
- **MCP server** (`cftc-cot-mcp`, optional `mcp` extra): a FastMCP stdio server
  exposing COT data and analysis to MCP-compatible LLM clients. Tools for markets,
  reports, history, net positions, COT Index, Z-scores, long/short ratios,
  week-over-week change, percentile rank, and extremes (all with an `exact` flag
  and clear no-match errors); `cot://datasets` and `cot://fields/{classification}`
  resources; and `analyze_market` / `positioning_summary` prompts.
- `exact` parameter on `COTClient.latest()` / `COTClient.history()`.
- PyPI trove classifiers (Python versions, audience, topics) so the
  `pyversions` badge and PyPI metadata populate. Takes effect on the next release.

## [0.2.1] - 2026-06-20

### Security
- Coerce numeric filter thresholds (`*_gt` helpers) to `int`, raising `COTQueryError`
  on non-numeric input to prevent SoQL injection through interpolated query values.
- Document injection-safe methods (`market`, dates, numeric filters) vs. trusted-input-only
  escape hatches (`where`, `select`, `order_by`) in `SECURITY.md`.
- Add disk-cache trust guidance: `diskcache` uses `pickle`, so cache directories must
  not be shared across trust boundaries.

### Added
- "Install from GitHub" instructions (git+https and release-asset wheel) in the README.

### Fixed
- Ignore `.pypirc` and the default `cot_cache/` directory in `.gitignore`.

## [0.2.0] - 2026-06-20

### Added
- COT analysis metrics: `cot_index()`, `extremes()`, `long_short_ratios()`,
  `percentile_rank()`, and `wow_change()` on `COTAnalysis`.
- Working response caching: `MemoryCache` and `DiskCache` backends, wired through
  `COTClient(cache=..., cache_dir=..., cache_ttl=...)`. Disk caching uses the new
  optional `cache` extra (`pip install cftc-cot-soda[cache]`).
- `cftc-cot` command-line interface (`latest`, `history`, `markets`, `index`).
- Automatic retry with exponential backoff on transient API failures (429/5xx).

### Fixed
- Escape single quotes in query literals (e.g. `market("O'Brien")`), preventing
  malformed queries and injection.
- Replace deprecated `pd.to_numeric(errors="ignore")` for pandas 2.2+ compatibility.

### Changed
- `COTAnalysis` now sorts rows chronologically before computing rolling metrics.

## [0.1.1] - 2026-06-17

### Fixed
- Patch `app_token` passthrough in `COTQuery`.
- Optimize `list_markets` to use `SELECT DISTINCT`.

### Added
- Contribution guidelines and Pull Request templates.
- Security policy (`SECURITY.md`).
- Project documentation in GitHub Wiki.
- Data source attribution in README.
- MIT License.

## [0.1.0] - 2026-06-17
