# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
