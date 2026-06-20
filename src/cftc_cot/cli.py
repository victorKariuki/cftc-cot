"""
Command-line interface for the CFTC COT SDK.

Examples:
    cftc-cot latest  --dataset legacy --market "Crude Oil"
    cftc-cot history --dataset legacy --market "Crude Oil" --weeks 52
    cftc-cot markets --dataset legacy
    cftc-cot index   --dataset legacy --market "Crude Oil" --window 156
"""
from __future__ import annotations
import argparse
import sys
from typing import Optional, Sequence

import pandas as pd

from .client import COTClient
from .analysis import COTAnalysis


def _print_df(df: pd.DataFrame, fmt: str) -> None:
    """Render a DataFrame to stdout in the requested format."""
    if df.empty:
        print("No data returned.", file=sys.stderr)
        return
    if fmt == "csv":
        print(df.to_csv(index=False))
    elif fmt == "json":
        print(df.to_json(orient="records", date_format="iso"))
    else:
        print(df.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser for the ``cftc-cot`` command."""
    # Shared options usable either before or after the subcommand.
    # SUPPRESS defaults so a value given before the subcommand isn't clobbered by
    # the subparser's copy of the same option; real defaults are applied in main().
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--app-token", default=argparse.SUPPRESS, help="Socrata API app token.")
    common.add_argument(
        "--cache", choices=["memory", "disk"], default=argparse.SUPPRESS,
        help="Enable response caching.",
    )
    common.add_argument(
        "--format", choices=["table", "csv", "json"], default=argparse.SUPPRESS,
        help="Output format (default: table).",
    )

    parser = argparse.ArgumentParser(
        prog="cftc-cot",
        description="Query and analyze CFTC Commitments of Traders data.",
        parents=[common],
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_latest = sub.add_parser("latest", parents=[common], help="Latest report for a market.")
    p_latest.add_argument("--dataset", default="legacy")
    p_latest.add_argument("--market", required=True)

    p_history = sub.add_parser("history", parents=[common], help="N-week history for a market.")
    p_history.add_argument("--dataset", default="legacy")
    p_history.add_argument("--market", required=True)
    p_history.add_argument("--weeks", type=int, default=52)

    p_markets = sub.add_parser("markets", parents=[common], help="List available markets for a dataset.")
    p_markets.add_argument("--dataset", default="legacy")

    p_index = sub.add_parser("index", parents=[common], help="COT Index history for a market.")
    p_index.add_argument("--dataset", default="legacy")
    p_index.add_argument("--market", required=True)
    p_index.add_argument("--window", type=int, default=156)
    p_index.add_argument("--weeks", type=int, default=156, help="Weeks of history to fetch.")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the ``cftc-cot`` console script."""
    parser = build_parser()
    args = parser.parse_args(argv)

    app_token = getattr(args, "app_token", None)
    cache = getattr(args, "cache", None)
    fmt = getattr(args, "format", "table")

    client = COTClient(app_token=app_token, cache=cache)

    if args.command == "latest":
        df = client.latest(args.dataset, args.market)
        _print_df(df, fmt)
    elif args.command == "history":
        df = client.history(args.dataset, args.market, weeks=args.weeks)
        _print_df(df, fmt)
    elif args.command == "markets":
        markets = client.list_markets(args.dataset)
        _print_df(pd.DataFrame({"market": markets}), fmt)
    elif args.command == "index":
        df = client.history(args.dataset, args.market, weeks=args.weeks)
        if df.empty:
            _print_df(df, fmt)
            return 1
        classification = classification_for(args.dataset)
        analyzed = COTAnalysis(df, classification).cot_index(window=args.window)
        cols = [c for c in analyzed.columns
                if c == "report_date_as_yyyy_mm_dd" or c.endswith("_cot_index")]
        _print_df(analyzed[cols] if cols else analyzed, fmt)

    return 0


def classification_for(dataset: str) -> str:
    """Map a dataset name to its analysis classification."""
    if "disaggregated" in dataset:
        return "disaggregated"
    if "tff" in dataset:
        return "tff"
    return "legacy"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
