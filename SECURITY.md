# Security Policy

This document outlines security-specific guidelines for using the `cftc-cot` SDK. Because this library interacts with an external public API and processes data into structured formats, users must adhere to the following practices.

## Credential Management

The `COTClient` accepts an optional `app_token` for authenticated Socrata API access to higher rate limits.

- **Never** hardcode your `app_token` in source control.
- **Always** load credentials from environment variables or a secure secret management service.
- **Example (Recommended):**
  ```python
  import os
  from cftc_cot import COTClient
  
  # Use environment variable, fallback to None
  token = os.getenv("CFTC_APP_TOKEN")
  client = COTClient(app_token=token)
  ```

## SODA2 API Injection Risks

The `COTQuery` class builds SODA2 query strings dynamically. Inputs receive different levels of protection depending on the method:

**Automatically protected (safe for user input):**
- `.market()`, `.markets_in()`, `.date_range()`, `.date_after()`, `.date_before()` — string values are quote-escaped (`'` → `''`), so apostrophes and embedded quotes cannot break out of the literal.
- All numeric threshold helpers (`.noncomm_long_gt()`, `.managed_money_long_gt()`, `.long_positions_gt()`, etc.) — the value is coerced to `int`; non-numeric input raises `COTQueryError` instead of being interpolated.

**NOT sanitized — trusted input only (escape hatches):**
- `.where(condition)`, `.select(*columns)`, and `.order_by(column)` interpolate raw SoQL fragments / identifiers verbatim. This is intentional so advanced queries remain possible.
- **Requirement:** **Never** pass untrusted/user-supplied input into `.where()`, `.select()`, or `.order_by()`. If a column name must come from user input, validate it against an allow-list of known fields (see `fields.py`) before passing it in.

## Data Handling and Parsing

The SDK automatically converts raw API responses into `pandas` DataFrames.

- **Unvalidated Schema:** The CFTC API schema can change. When parsing `execute()` results in your application, do not assume specific column types are always present or contain the expected data type. 
- **Type Conversion:** The SDK attempts numeric conversion per column, keeping the original values when a column is not cleanly numeric. If API data is malformed, you may see `object` dtype columns instead of `float`/`int`.
- **Requirement:** Always validate the output DataFrame structure (`df.columns`, `df.dtypes`) in your application logic before performing numerical analysis on specific columns.

## Disk Cache Trust

When `cache="disk"` is enabled, responses are persisted via the `diskcache` package, which serializes values using Python `pickle`. Loading a tampered or attacker-controlled cache file could therefore lead to arbitrary code execution on deserialization.

- **Requirement:** Point `cache_dir` at a directory only your application can write to (e.g. a per-user path). **Never** share a disk cache directory across trust boundaries or load one from an untrusted source. For untrusted/multi-tenant environments, prefer the in-memory backend (`cache="memory"`).

## Vulnerability Reporting

If you believe you have discovered a security vulnerability in this SDK, please report it via the issue tracker using the **Bug Report** template, clearly marking the title with `[SECURITY]`.
