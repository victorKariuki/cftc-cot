"""
Model Context Protocol (MCP) server for the CFTC COT SDK.

Exposes CFTC Commitments of Traders data and analysis as MCP tools, resources,
and prompts so that MCP-compatible LLM clients (Claude Desktop, IDE assistants,
etc.) can query positioning data directly. Runs over stdio transport.

Run it with the installed console script:

    cftc-cot-mcp

or as a module:

    python -m cftc_cot.mcp_server

Requires the optional ``mcp`` dependency (Python >= 3.10):

    pip install cftc-cot-soda[mcp]
"""
from __future__ import annotations
import json
from typing import Any, Callable

import pandas as pd

from .client import COTClient
from .analysis import COTAnalysis
from .cli import classification_for
from .query import COTQuery

try:
    import anyio
    from mcp.server.fastmcp import FastMCP
    from mcp.server.fastmcp.exceptions import ToolError
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise SystemExit(
        "The MCP server requires the 'mcp' package. "
        "Install it with: pip install cftc-cot-soda[mcp]"
    ) from exc

# A single cached client keeps repeated tool calls from re-hitting the API
# (COT data only updates weekly).
_client = COTClient(cache="memory")

_FIELD_CLASSES = {
    "legacy": "LegacyFields",
    "disaggregated": "DisaggregatedFields",
    "tff": "TFFFields",
}

mcp = FastMCP("cftc-cot")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to JSON-safe records (ISO dates, null for NaN)."""
    if df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


async def _run(fn: Callable[..., Any], *args: Any) -> Any:
    """Run a blocking client/analysis call off the event loop."""
    return await anyio.to_thread.run_sync(fn, *args)


def _validate_dataset(dataset: str) -> None:
    """Raise a clear ToolError if the dataset name is not recognized."""
    if dataset not in COTQuery.DATASETS:
        valid = ", ".join(sorted(COTQuery.DATASETS))
        raise ToolError(f"Unknown dataset {dataset!r}. Valid datasets: {valid}.")


def _require(df: pd.DataFrame, market: str, dataset: str) -> pd.DataFrame:
    """Raise a clear ToolError when a market fetch comes back empty."""
    if df.empty:
        raise ToolError(
            f"No data for market {market!r} in dataset {dataset!r}. "
            f"Use the list_markets tool to see valid market names, "
            f"or try exact=false for a prefix match."
        )
    return df


def _history(dataset: str, market: str, weeks: int, exact: bool) -> pd.DataFrame:
    """Validated, non-empty history fetch shared by the analysis tools."""
    _validate_dataset(dataset)
    return _require(_client.history(dataset, market, weeks=weeks, exact=exact), market, dataset)


# --------------------------------------------------------------------------- #
# Tools — data access
# --------------------------------------------------------------------------- #
@mcp.tool()
async def list_markets(dataset: str = "legacy") -> list[str]:
    """
    List the available markets for a CFTC dataset.

    Args:
        dataset: One of "legacy", "disaggregated", or "tff" (and their
            "_futures"/"_combined" variants).
    """
    _validate_dataset(dataset)
    return await _run(_client.list_markets, dataset)


@mcp.tool()
async def latest_report(
    market: str, dataset: str = "legacy", exact: bool = False
) -> list[dict[str, Any]]:
    """
    Fetch the most recent COT report for a market.

    Args:
        market: Market name (e.g. "Crude Oil").
        dataset: One of "legacy", "disaggregated", or "tff".
        exact: If True, match the market name exactly; otherwise prefix match
            (which may return multiple contracts).
    """
    _validate_dataset(dataset)
    df = await _run(lambda: _client.latest(dataset, market, exact=exact))
    return _records(_require(df, market, dataset))


@mcp.tool()
async def history(
    market: str, dataset: str = "legacy", weeks: int = 12, exact: bool = False
) -> list[dict[str, Any]]:
    """
    Fetch N weeks of COT history for a market, newest first.

    Args:
        market: Market name.
        dataset: One of "legacy", "disaggregated", or "tff".
        weeks: Number of weeks of history to return (default 12).
        exact: If True, match the market name exactly; otherwise prefix match.
    """
    df = await _run(_history, dataset, market, weeks, exact)
    return _records(df)


# --------------------------------------------------------------------------- #
# Tools — analysis
# --------------------------------------------------------------------------- #
@mcp.tool()
async def net_positions(
    market: str, dataset: str = "legacy", weeks: int = 12, exact: bool = False
) -> list[dict[str, Any]]:
    """
    Net (long - short) positions per trader category, newest rows last.

    Args:
        market: Market name.
        dataset: One of "legacy", "disaggregated", or "tff".
        weeks: Weeks of history to fetch (default 12).
        exact: Exact vs prefix market match.
    """
    def work() -> list[dict[str, Any]]:
        df = _history(dataset, market, weeks, exact)
        out = COTAnalysis(df, classification_for(dataset)).net_positions()
        cols = [c for c in out.columns if c == "report_date_as_yyyy_mm_dd" or c.endswith("_net")]
        return _records(out[cols] if cols else out)
    return await _run(work)


@mcp.tool()
async def cot_index(
    market: str,
    dataset: str = "legacy",
    window: int = 156,
    weeks: int = 156,
    tail: int = 12,
    exact: bool = False,
) -> list[dict[str, Any]]:
    """
    Compute the classic 0-100 COT Index over a rolling window.

    A reading near 100 is the most bullish positioning of the window; near 0,
    the most bearish.

    Args:
        market: Market name.
        dataset: One of "legacy", "disaggregated", or "tff".
        window: Rolling lookback window in weeks (default 156, ~3 years).
        weeks: Weeks of history to fetch (default 156).
        tail: Number of most-recent rows to return (default 12).
        exact: Exact vs prefix market match.
    """
    def work() -> list[dict[str, Any]]:
        df = _history(dataset, market, weeks, exact)
        out = COTAnalysis(df, classification_for(dataset)).cot_index(window=window)
        cols = [c for c in out.columns if c == "report_date_as_yyyy_mm_dd" or c.endswith("_cot_index")]
        return _records((out[cols] if cols else out).tail(tail))
    return await _run(work)


@mcp.tool()
async def z_scores(
    market: str,
    dataset: str = "legacy",
    window: int = 52,
    weeks: int = 104,
    tail: int = 12,
    exact: bool = False,
) -> list[dict[str, Any]]:
    """
    Rolling Z-scores of net positions, newest rows last.

    Args:
        market: Market name.
        dataset: One of "legacy", "disaggregated", or "tff".
        window: Rolling window in weeks (default 52).
        weeks: Weeks of history to fetch (default 104).
        tail: Number of most-recent rows to return (default 12).
        exact: Exact vs prefix market match.
    """
    def work() -> list[dict[str, Any]]:
        df = _history(dataset, market, weeks, exact)
        out = COTAnalysis(df, classification_for(dataset)).z_scores(window=window)
        cols = [c for c in out.columns if c == "report_date_as_yyyy_mm_dd" or c.endswith("_zscore")]
        return _records((out[cols] if cols else out).tail(tail))
    return await _run(work)


@mcp.tool()
async def long_short_ratios(
    market: str, dataset: str = "legacy", weeks: int = 12, exact: bool = False
) -> list[dict[str, Any]]:
    """
    Long/short ratios per trader category, newest rows last.

    Args:
        market: Market name.
        dataset: One of "legacy", "disaggregated", or "tff".
        weeks: Weeks of history to fetch (default 12).
        exact: Exact vs prefix market match.
    """
    def work() -> list[dict[str, Any]]:
        df = _history(dataset, market, weeks, exact)
        out = COTAnalysis(df, classification_for(dataset)).long_short_ratios()
        cols = [c for c in out.columns if c == "report_date_as_yyyy_mm_dd" or c.endswith("_ls_ratio")]
        return _records(out[cols] if cols else out)
    return await _run(work)


@mcp.tool()
async def wow_change(
    market: str, dataset: str = "legacy", weeks: int = 12, exact: bool = False
) -> list[dict[str, Any]]:
    """
    Week-over-week change in net positions, newest rows last.

    Args:
        market: Market name.
        dataset: One of "legacy", "disaggregated", or "tff".
        weeks: Weeks of history to fetch (default 12).
        exact: Exact vs prefix market match.
    """
    def work() -> list[dict[str, Any]]:
        df = _history(dataset, market, weeks, exact)
        out = COTAnalysis(df, classification_for(dataset)).wow_change()
        cols = [c for c in out.columns if c == "report_date_as_yyyy_mm_dd" or c.endswith("_wow")]
        return _records(out[cols] if cols else out)
    return await _run(work)


@mcp.tool()
async def percentile_rank(
    market: str,
    column: str,
    dataset: str = "legacy",
    weeks: int = 156,
    exact: bool = False,
) -> float:
    """
    Percentile rank (0-1) of the most recent value of a net-position column.

    Args:
        market: Market name.
        column: Net-position column, e.g. "noncomm_net" (legacy), "m_money_net"
            (disaggregated), "lev_money_net" (tff).
        dataset: One of "legacy", "disaggregated", or "tff".
        weeks: Weeks of history to fetch (default 156).
        exact: Exact vs prefix market match.
    """
    def work() -> float:
        df = _history(dataset, market, weeks, exact)
        analysis = COTAnalysis(df, classification_for(dataset))
        try:
            return analysis.percentile_rank(column)
        except KeyError as exc:
            valid = ", ".join(analysis.net_map.keys())
            raise ToolError(f"Unknown column {column!r}. Valid columns: {valid}.") from exc
    return await _run(work)


@mcp.tool()
async def extremes(
    market: str,
    dataset: str = "legacy",
    threshold: float = 0.9,
    weeks: int = 156,
    exact: bool = False,
) -> list[dict[str, Any]]:
    """
    Flag the most recent bullish/bearish extreme positioning for a market.

    Args:
        market: Market name.
        dataset: One of "legacy", "disaggregated", or "tff".
        threshold: Fraction (0-1) marking the bullish cutoff on the COT Index;
            >= threshold*100 is bullish, <= (1-threshold)*100 is bearish.
        weeks: Weeks of history to fetch (default 156).
        exact: Exact vs prefix market match.
    """
    def work() -> list[dict[str, Any]]:
        df = _history(dataset, market, weeks, exact)
        out = COTAnalysis(df, classification_for(dataset)).extremes(threshold=threshold)
        cols = [c for c in out.columns if c == "report_date_as_yyyy_mm_dd" or c.endswith("_extreme")]
        return _records((out[cols] if cols else out).tail(1))
    return await _run(work)


# --------------------------------------------------------------------------- #
# Resources
# --------------------------------------------------------------------------- #
@mcp.resource("cot://datasets")
def datasets_resource() -> str:
    """The available CFTC datasets and their Socrata dataset ids."""
    return json.dumps(
        {
            "datasets": COTQuery.DATASETS,
            "classifications": sorted(_FIELD_CLASSES),
            "note": "Pass a dataset name to any tool's `dataset` argument.",
        },
        indent=2,
    )


@mcp.resource("cot://fields/{classification}")
def fields_resource(classification: str) -> str:
    """Field-name reference (constant -> API field) for a classification."""
    from . import fields as fields_mod

    cls_name = _FIELD_CLASSES.get(classification)
    if cls_name is None:
        raise ValueError(
            f"Unknown classification {classification!r}. "
            f"Valid: {', '.join(sorted(_FIELD_CLASSES))}."
        )
    cls = getattr(fields_mod, cls_name)
    mapping = {
        attr: getattr(cls, attr)
        for attr in dir(cls)
        if attr.isupper() and isinstance(getattr(cls, attr), str)
    }
    return json.dumps({"classification": classification, "fields": mapping}, indent=2)


# --------------------------------------------------------------------------- #
# Prompts
# --------------------------------------------------------------------------- #
@mcp.prompt()
def analyze_market(market: str, dataset: str = "legacy") -> str:
    """Guide an analysis of a market's current positioning."""
    return (
        f"Analyze CFTC COT positioning for {market!r} in the {dataset!r} dataset.\n"
        f"1. Call cot_index(market={market!r}, dataset={dataset!r}, exact=true) for the "
        f"0-100 positioning index.\n"
        f"2. Call extremes(market={market!r}, dataset={dataset!r}) to flag bullish/bearish extremes.\n"
        f"3. Call wow_change(market={market!r}, dataset={dataset!r}) for the latest weekly shift.\n"
        f"Summarize whether speculative traders are stretched long or short and what changed this week."
    )


@mcp.prompt()
def positioning_summary(market: str, dataset: str = "legacy") -> str:
    """Produce a concise positioning summary for a market."""
    return (
        f"Give a concise positioning summary for {market!r} ({dataset!r}). "
        f"Use latest_report and net_positions (exact=true), then state the net position "
        f"of each trader category and whether it is unusually long or short versus history "
        f"(use percentile_rank for the key category)."
    )


def main() -> None:
    """Entry point for the ``cftc-cot-mcp`` console script (stdio transport)."""
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
