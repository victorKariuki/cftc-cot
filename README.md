# CFTC COT SDK

A Python SDK for accessing, querying, and analyzing CFTC Commitments of Traders (COT) data.

## Data Source
This SDK provides programmatic access to data sourced from the [CFTC Public Reporting Portal](https://publicreporting.cftc.gov/stories/s/r4w3-av2u).

## Installation

```bash
pip install cftc-cot
```

## Quick Start

```python
from cftc_cot import COTClient, COTAnalysis

client = COTClient()

# Get 52 weeks of Crude Oil data
df = client.legacy().market("Crude Oil").last_n_weeks(52).execute()

# Compute net positions
analysis = COTAnalysis(df, classification="legacy")
df = analysis.net_positions()

print(df[['report_date_as_yyyy_mm_dd', 'noncomm_net']].head())
```

## Documentation

- **`COTClient`**: Main entry point. Supports `app_token` for higher rate limits.
- **`COTQuery`**: Fluent query builder for filtering and selecting data.
- **`COTAnalysis`**: Post-fetch metrics (Net Positions, Z-scores).
- **`cftc_cot.fields`**: Constants for all dataset fields (e.g., `LegacyFields.NONCOMM_LONG`).

## Caching

```python
# Enable disk caching to reduce API calls
client = COTClient(cache="disk", cache_dir="./cot_cache")
```

## Contributing
See `CHANGELOG.md` for version history.

## License
MIT
