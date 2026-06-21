# cftc-cot Development & Architectural Guide

## AI Context Summary (for LLM/MCP integration)
- **Project Goal:** Python SDK for the CFTC Commitments of Traders (COT) SODA2 API.
- **Core Principle:** Strict preservation of API-verified field names (including quirks) is paramount.
- **Architecture:** 
    - `COTClient`: Main entry point (Factory). Builds the cache and threads it into every query.
    - `COTQuery`: Fluent builder for SODA2 queries (delegates to `sodapy`). Handles caching and retry/backoff.
    - `COTAnalysis`: Post-fetch DataFrame metrics (Net, Z-Scores, COT Index, extremes, long/short ratios, percentile rank, week-over-week).
    - `cache.py`: Pluggable cache backends (`MemoryCache`, `DiskCache`) behind the `COTCache` protocol.
    - `cli.py`: `argparse`-based `cftc-cot` console entry point.
    - `fields.py`: Source of truth for API field constants.
- **Critical Constraints:**
    - `select` arg in `sodapy.get` MUST be a comma-separated string (`", ".join(list)`).
    - Market filtering MUST use `upper()` for case-insensitivity against ALL CAPS API data.
    - All field constants MUST match the API exact string (no fixing typos/quirks).

---

## Architecture Overview

### 1. `client.py` (COTClient)
Primary interface. Manages connection configuration and acts as a factory for specific dataset query objects. Convenience methods (`latest`, `history`) wrap query building and execution. Builds a cache backend once (via `cache.build_cache`) and passes it, plus the app token, into every `COTQuery` through the private `_query()` helper.

### 2. `query.py` (COTQuery)
Fluent API for building SODA2 queries. 
- Accumulates state (`_where_clauses`, `_select_fields`, etc.).
- `_q()`: module-level helper that escapes single quotes in string literals (`'` → `''`) — applied to every user-supplied value to prevent malformed/injected queries.
- `_request_with_retry()`: wraps `sodapy`'s `get` with exponential backoff on HTTP 429/5xx and connection errors; raises `COTConnectionError` once attempts are exhausted. Client errors (4xx other than 429) are not retried.
- `_cache_key()`: SHA1 of the dataset id + request parameters. `execute()`/`count()` check the cache before hitting the API and store results (raw records) on a miss.
- `execute()` handles:
    - SODA2 parameter formatting.
    - Conversion of response to `pandas.DataFrame` (via `_to_dataframe`).
    - Automated date and numeric type conversion (numeric coercion only adopts a column when no real values would be lost — pandas 2.2+ removed the old `errors="ignore"` shortcut).
- `_check_classification()`: Enforces dataset-specific constraints (e.g., Legacy-only helper methods cannot be called on TFF queries).

### 3. `analysis.py` (COTAnalysis)
Provides post-fetch computed metrics.
- Operates on a copied `pd.DataFrame`, **sorted ascending by report date** so rolling/diff metrics are correct (the client returns rows newest-first).
- Maps fields via `fields.py` constants to ensure robust mapping of (long, short) columns.
- Metrics: `net_positions`, `z_scores`, `cot_index`, `extremes`, `long_short_ratios`, `percentile_rank`, `wow_change`.

### 4. `cache.py` (COTCache / MemoryCache / DiskCache)
Pluggable caching. `COTCache` is a runtime-checkable `Protocol` (`get`, `set`). `MemoryCache` is a stdlib dict with per-entry expiry; `DiskCache` lazily imports the optional `diskcache` package (the `[cache]` extra) and raises `COTError` if it is missing. `build_cache()` maps the `"memory"`/`"disk"` selector strings to instances.

### 5. `cli.py`
`argparse`-based entry point exposed as the `cftc-cot` console script. Subcommands: `latest`, `history`, `markets`, `index`. Shared flags (`--app-token`, `--cache`, `--format`) use `argparse.SUPPRESS` defaults so they work either before or after the subcommand.

### 6. `fields.py`
Authoritative constants module. **Do not modify field strings** unless the CFTC API itself changes.

---

## Conventions & Style

- **Naming:** Follow PEP 8 (snake_case functions/vars, PascalCase classes).
- **Docstrings:** Required for all public methods (Google Style).
- **Type Hints:** Mandatory for all parameters and return types (`from __future__ import annotations`).
- **Logging:** Use `logging` module, not `print`. 
- **Error Handling:** Use custom exceptions defined in `exceptions.py`.

---

## Extending Functionality

### Adding New Fields
1.  Verify the exact field name from the live API (including typos).
2.  Add to the appropriate class (`LegacyFields`, `DisaggregatedFields`, or `TFFFields`) in `src/cftc_cot/fields.py`.
3.  Add a comment noting any quirks (typos, missing suffixes).

### Adding Analysis Metrics
1.  Define the mapping of fields (e.g., long_col, short_col) in `COTAnalysis.__init__` for the relevant classification.
2.  Implement the calculation method in `COTAnalysis`.

---

## Development Workflow

This project uses **Git-Flow**.
- `master`: Production-ready code.
- `develop`: Integration branch.
- Feature/Bugfix branches: Created from `develop`, merged back via `git flow finish`.

For cutting a version, tagging, and publishing to PyPI (including the current
manual-`twine` fallback while CI is billing-locked), see [RELEASING.md](RELEASING.md).
