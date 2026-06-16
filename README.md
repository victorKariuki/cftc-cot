# CFTC COT SDK

[![PyPI](https://img.shields.io/pypi/v/cftc-cot.svg)](https://pypi.org/project/cftc-cot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, verified Python SDK for accessing, querying, and analyzing [CFTC Commitments of Traders (COT)](https://publicreporting.cftc.gov/stories/s/r4w3-av2u) data.

## Overview

The `cftc-cot` SDK provides a fluent, production-ready interface for the CFTC's SODA2 API. It simplifies the complexity of querying 6 different CFTC datasets, handles API-specific naming quirks, and provides powerful post-fetch analysis tools.

## Key Features

- **Fluent API**: Chainable query building for intuitive data retrieval.
- **Production-Tested**: Verified field mappings and API interactions against live CFTC data.
- **Advanced Analysis**: Built-in metrics including Net Positions, Z-Scores, and extreme positioning detection.
- **Robust Field Handling**: Preserves official API quirks (typos, naming inconsistencies) using structured field constants.
- **Production Ready**: Full type hinting, comprehensive exception hierarchy, and rate-limiting support via app tokens.

## Installation

```bash
pip install cftc-cot
```

## Quick Start

```python
from cftc_cot import COTClient, COTAnalysis

# Initialize client
client = COTClient()

# Query: 52-week history of Crude Oil positioning
df = client.legacy().market("Crude Oil").last_n_weeks(52).execute()

# Analyze: Compute net positions and Z-scores
analysis = COTAnalysis(df, classification="legacy")
df_analyzed = analysis.z_scores()

print(df_analyzed[['report_date_as_yyyy_mm_dd', 'noncomm_net', 'noncomm_net_zscore']].tail())
```

## Documentation

For a complete API reference, guides, and dataset specifications, please visit our **[GitHub Wiki](https://github.com/victorKariuki/cftc-cot/wiki)**.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
