# cftc-cot Development & Architectural Guide

## AI Context Summary (for LLM/MCP integration)
- **Project Goal:** Python SDK for the CFTC Commitments of Traders (COT) SODA2 API.
- **Core Principle:** Strict preservation of API-verified field names (including quirks) is paramount.
- **Architecture:** 
    - `COTClient`: Main entry point (Factory).
    - `COTQuery`: Fluent builder for SODA2 queries (delegates to `sodapy`).
    - `COTAnalysis`: Post-fetch DataFrame metrics (Net, Z-Scores).
    - `fields.py`: Source of truth for API field constants.
- **Critical Constraints:**
    - `select` arg in `sodapy.get` MUST be a comma-separated string (`", ".join(list)`).
    - Market filtering MUST use `upper()` for case-insensitivity against ALL CAPS API data.
    - All field constants MUST match the API exact string (no fixing typos/quirks).

---

## Architecture Overview

### 1. `client.py` (COTClient)
Primary interface. Manages connection configuration and acts as a factory for specific dataset query objects. Convenience methods (`latest`, `history`) wrap query building and execution.

### 2. `query.py` (COTQuery)
Fluent API for building SODA2 queries. 
- Accumulates state (`_where_clauses`, `_select_fields`, etc.).
- `execute()` handles:
    - SODA2 parameter formatting.
    - Conversion of response to `pandas.DataFrame`.
    - Automated date and numeric type conversion.
- `_check_classification()`: Enforces dataset-specific constraints (e.g., Legacy-only helper methods cannot be called on TFF queries).

### 3. `analysis.py` (COTAnalysis)
Provides post-fetch computed metrics.
- Operates on a copied `pd.DataFrame`.
- Maps fields via `fields.py` constants to ensure robust mapping of (long, short) columns.

### 4. `fields.py`
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
