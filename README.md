# CFTC COT SDK

[![PyPI](https://img.shields.io/pypi/v/cftc-cot-soda.svg)](https://pypi.org/project/cftc-cot-soda/)
[![GitHub release](https://img.shields.io/github/v/release/victorKariuki/cftc-cot.svg)](https://github.com/victorKariuki/cftc-cot/releases/latest)
[![Python versions](https://img.shields.io/pypi/pyversions/cftc-cot-soda.svg)](https://pypi.org/project/cftc-cot-soda/)
[![Downloads](https://img.shields.io/pypi/dm/cftc-cot-soda.svg)](https://pypi.org/project/cftc-cot-soda/)
[![Wheel](https://img.shields.io/pypi/wheel/cftc-cot-soda.svg)](https://pypi.org/project/cftc-cot-soda/)
[![Publish to PyPI](https://github.com/victorKariuki/cftc-cot/actions/workflows/publish.yml/badge.svg)](https://github.com/victorKariuki/cftc-cot/actions/workflows/publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, verified Python SDK for accessing, querying, and analyzing [CFTC Commitments of Traders (COT)](https://publicreporting.cftc.gov/stories/s/r4w3-av2u) data.

## Overview

The `cftc-cot` SDK provides a fluent, production-ready interface for the CFTC's SODA2 API. It simplifies the complexity of querying 6 different CFTC datasets, handles API-specific naming quirks, and provides powerful post-fetch analysis tools.

## Key Features

- **Fluent API**: Chainable query building for intuitive data retrieval.
- **Production-Tested**: Verified field mappings and API interactions against live CFTC data.
- **Advanced Analysis**: Net Positions, Z-Scores, the classic 0–100 **COT Index**, extreme positioning detection, long/short ratios, percentile ranks, and week-over-week change.
- **Caching**: Optional in-memory or persistent disk caching of API responses (COT data updates weekly, so a 24h TTL eliminates redundant requests).
- **Resilient Networking**: Automatic retry with exponential backoff on transient API failures (429/5xx).
- **Command-Line Interface**: A `cftc-cot` CLI for quick lookups without writing Python.
- **Robust Field Handling**: Preserves official API quirks (typos, naming inconsistencies) using structured field constants.
- **Production Ready**: Full type hinting, comprehensive exception hierarchy, and rate-limiting support via app tokens.

## Installation

```bash
pip install cftc-cot-soda

# With disk caching support:
pip install cftc-cot-soda[cache]
```

### Install from GitHub

```bash
# Latest tagged release, straight from the source repo
pip install git+https://github.com/victorKariuki/cftc-cot.git@v0.2.0

# Or the wheel attached to a GitHub Release
pip install https://github.com/victorKariuki/cftc-cot/releases/download/v0.2.0/cftc_cot_soda-0.2.0-py3-none-any.whl
```

## Quick Start

```python
from cftc_cot import COTClient, COTAnalysis

# Initialize client
client = COTClient()

# Query: 52-week history of Crude Oil positioning
df = client.legacy().market("Crude Oil").last_n_weeks(52).execute()

# Analyze: Compute net positions and the COT Index
analysis = COTAnalysis(df, classification="legacy")
df_analyzed = analysis.cot_index(window=52)

print(df_analyzed[['report_date_as_yyyy_mm_dd', 'noncomm_net', 'noncomm_net_cot_index']].tail())
```

### Caching

```python
# In-memory cache (per-process) or persistent disk cache.
client = COTClient(cache="memory")
client = COTClient(cache="disk", cache_dir="./cot_cache", cache_ttl=86400)
```

### Command-Line Interface

```bash
cftc-cot latest  --dataset legacy --market "Crude Oil"
cftc-cot history --dataset legacy --market "Crude Oil" --weeks 52
cftc-cot markets --dataset legacy
cftc-cot index   --dataset legacy --market "Crude Oil" --window 156

# Choose output format and enable caching:
cftc-cot --format json --cache memory latest --dataset legacy --market "Gold"
```

### MCP Server

Expose COT data to MCP-compatible LLM clients (Claude Desktop, IDE assistants) over
stdio. Install the extra and run the `cftc-cot-mcp` command:

```bash
pip install cftc-cot-soda[mcp]   # requires Python >= 3.10
cftc-cot-mcp
```

- **Tools**: `list_markets`, `latest_report`, `history`, `net_positions`, `cot_index`, `z_scores`, `long_short_ratios`, `wow_change`, `percentile_rank`, `extremes` (all support an `exact` flag and return clear errors when a market doesn't match).
- **Resources**: `cot://datasets`, `cot://fields/{classification}`.
- **Prompts**: `analyze_market`, `positioning_summary`.

Example Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cftc-cot": {
      "command": "cftc-cot-mcp"
    }
  }
}
```

## Documentation

For a complete API reference, guides, and dataset specifications, please visit our **[GitHub Wiki](https://github.com/victorKariuki/cftc-cot/wiki)**.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
