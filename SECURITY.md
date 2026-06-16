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

The `COTQuery` class builds SODA2 query strings dynamically by appending user-provided strings to `WHERE` clauses in methods like `.where()`, `.market()`, and `.markets_in()`.

- The SDK **does not** automatically sanitize inputs provided to these methods.
- If you expose these filtering methods directly to user-provided input in a web application or public API, **you are vulnerable to API injection**.
- **Requirement:** If user input is passed into any `.where()`, `.market()`, or `.markets_in()` call, you **must** validate and sanitize that input to ensure it matches expected formats (e.g., regex checks for alphanumeric market names, strict date formatting) before passing it to the SDK.

## Data Handling and Parsing

The SDK automatically converts raw API responses into `pandas` DataFrames.

- **Unvalidated Schema:** The CFTC API schema can change. When parsing `execute()` results in your application, do not assume specific column types are always present or contain the expected data type. 
- **Type Conversion:** The SDK attempts to force numeric conversion using `pd.to_numeric(..., errors='ignore')`. If API data is malformed (e.g., unexpected strings in a numeric column), this may result in `object` dtype columns in your DataFrame instead of `float` or `int`.
- **Requirement:** Always validate the output DataFrame structure (`df.columns`, `df.dtypes`) in your application logic before performing numerical analysis on specific columns.

## Vulnerability Reporting

If you believe you have discovered a security vulnerability in this SDK, please report it via the issue tracker using the **Bug Report** template, clearly marking the title with `[SECURITY]`.
