# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-17

### Added
- Initial release of the `cftc-cot` SDK.
- Support for all 6 CFTC COT datasets (Legacy, Disaggregated, TFF - both Combined and Futures Only).
- Fluent `COTQuery` builder API with verified field mappings.
- `COTAnalysis` module for net positions and Z-scores.
- `COTClient` high-level entry point with caching support.
- Comprehensive test suite covering live API integration and unit tests.
