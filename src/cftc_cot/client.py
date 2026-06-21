from __future__ import annotations
import pandas as pd
import logging
from typing import Optional, Union
from .query import COTQuery
from .cache import COTCache, DEFAULT_TTL, build_cache

logger = logging.getLogger(__name__)

class COTClient:
    """
    Main entry point for the CFTC COT SDK.

    Args:
        app_token: Optional Socrata API app token for higher rate limits.
        cache: Optional caching backend: "memory", "disk", a COTCache instance, or None.
        cache_dir: Directory for the disk cache backend (default "./cot_cache").
        cache_ttl: Time-to-live for cached responses, in seconds (default 24h).
    """

    def __init__(
        self,
        app_token: Optional[str] = None,
        cache: Optional[Union[str, COTCache]] = None,
        cache_dir: Optional[str] = None,
        cache_ttl: int = DEFAULT_TTL,
    ):
        self.app_token = app_token
        self.cache = build_cache(cache, cache_dir)
        self.cache_ttl = cache_ttl

    def _query(self, dataset: str) -> COTQuery:
        """Build a COTQuery wired with this client's token and cache settings."""
        return COTQuery(
            dataset,
            app_token=self.app_token,
            cache=self.cache,
            cache_ttl=self.cache_ttl,
        )

    # Factory methods for COTQuery
    def legacy(self) -> COTQuery:
        """Return a query builder for Legacy Combined data."""
        return self._query("legacy_combined")

    def legacy_futures(self) -> COTQuery:
        """Return a query builder for Legacy Futures Only data."""
        return self._query("legacy_futures")

    def disaggregated(self) -> COTQuery:
        """Return a query builder for Disaggregated Combined data."""
        return self._query("disaggregated_combined")

    def disaggregated_futures(self) -> COTQuery:
        """Return a query builder for Disaggregated Futures Only data."""
        return self._query("disaggregated_futures")

    def tff(self) -> COTQuery:
        """Return a query builder for TFF Combined data."""
        return self._query("tff_combined")

    def tff_futures(self) -> COTQuery:
        """Return a query builder for TFF Futures Only data."""
        return self._query("tff_futures")

    # High-level convenience methods
    def latest(self, dataset: str, market: str, exact: bool = False) -> pd.DataFrame:
        """
        Fetch the latest report for a specified market.

        Args:
            dataset: The dataset name (e.g., "legacy", "disaggregated", "tff").
            market: The market name.
            exact: If True, match the market name exactly; otherwise prefix match.

        Returns:
            A pandas DataFrame with the latest report record.
        """
        return self._query(dataset).market(market, exact=exact).order_by_date(desc=True).limit(1).execute()

    def history(self, dataset: str, market: str, weeks: int = 52, exact: bool = False) -> pd.DataFrame:
        """
        Fetch N-week history for a specified market.

        Args:
            dataset: The dataset name.
            market: The market name.
            weeks: Number of weeks of historical data to fetch.
            exact: If True, match the market name exactly; otherwise prefix match.

        Returns:
            A pandas DataFrame with historical records.
        """
        return self._query(dataset).market(market, exact=exact).last_n_weeks(weeks).order_by_date(desc=True).execute()

    def list_markets(
        self,
        dataset: str,
        weeks: Optional[int] = None,
        exchange: Optional[str] = None,
    ) -> list[str]:
        """
        List the unique markets for a dataset.

        By default this spans the dataset's full history, which includes retired
        markets. Pass ``weeks`` to restrict the result to markets that actually
        reported within the last N weeks — so the pool tracks the same window you
        intend to query and stale, delisted contracts drop out.

        Args:
            dataset: The dataset name.
            weeks: If given, only include markets reporting within the last N weeks.
            exchange: If given, only include markets on this exchange (exact match
                on the segment after the final " - ").

        Returns:
            A sorted list of unique market names.
        """
        query = self._query(dataset)
        if weeks is not None:
            query.last_n_weeks(weeks)
        if exchange:
            query.exchange(exchange, exact=True)

        return sorted(set(query.distinct_values("market_and_exchange_names")))

    def list_exchanges(self, dataset: str, weeks: Optional[int] = None) -> list[str]:
        """
        List the unique exchanges for a dataset.

        Exchanges are derived from the trailing component of each market name.

        Args:
            dataset: The dataset name.
            weeks: If given, only include exchanges active within the last N weeks.

        Returns:
            A sorted list of unique exchange names.
        """
        exchanges = set()
        for full in self.list_markets(dataset, weeks=weeks):
            _, exchange = self.split_market_exchange(full)
            if exchange:
                exchanges.add(exchange)
        return sorted(exchanges)

    @staticmethod
    def split_market_exchange(name: str) -> tuple[str, str]:
        """
        Split a ``market_and_exchange_names`` value into ``(market, exchange)``.

        The format is ``"<MARKET> - <EXCHANGE>"``; market names may contain a bare
        hyphen (e.g. ``"WHEAT-SRW"``), so the split uses the final " - " separator.
        Returns ``(name, "")`` when no separator is present.

        Args:
            name: The combined market-and-exchange name.

        Returns:
            A ``(market, exchange)`` tuple.
        """
        market, sep, exchange = name.rpartition(" - ")
        if not sep:
            return name, ""
        return market, exchange

    # Classification families a market can appear in. legacy is the superset;
    # disaggregated (physical commodities) and tff (financials) never overlap.
    CLASSIFICATIONS = ("legacy", "disaggregated", "tff")

    def classifications_for(
        self, market: str, weeks: Optional[int] = None
    ) -> list[str]:
        """
        Return which classifications contain a market (exact name match).

        A market is in ``legacy`` plus at most one finer set, so the result is
        typically ``["legacy", "disaggregated"]`` (commodities) or
        ``["legacy", "tff"]`` (financials).

        Args:
            market: The exact ``market_and_exchange_names`` value.
            weeks: If given, only consider markets reporting in the last N weeks.

        Returns:
            The subset of ``CLASSIFICATIONS`` containing the market.
        """
        return [
            cls
            for cls in self.CLASSIFICATIONS
            if market in set(self.list_markets(cls, weeks=weeks))
        ]

    def compare(
        self,
        markets,
        classifications: Optional[list[str]] = None,
        weeks: int = 156,
        windows=(),
    ) -> pd.DataFrame:
        """
        Build a tidy long frame for cross-market / cross-classification analysis.

        Each market is fetched and analyzed independently per classification, then
        reshaped to one row per ``(market, classification, category, date)`` — the
        canonical shape for comparison views (correlations, heatmaps, etc.).

        Args:
            markets: A market name or list of names (exact match).
            classifications: Classifications to include; defaults to those that
                actually contain each market (via :meth:`classifications_for`).
            weeks: Weeks of history to analyze (also raised to cover ``windows``).
            windows: Extra COT Index windows to include as ``cot_index_w{N}`` cols.

        Returns:
            Long-form DataFrame with columns ``market, exchange, classification,
            category, date, net, cot_index, zscore`` (+ one ``cot_index_w{N}`` per
            window). Empty if nothing resolved.
        """
        from .analysis import COTAnalysis

        if isinstance(markets, str):
            markets = [markets]

        # Fetch enough rows that the longest window is computable (weekly reports
        # mean ~N rows per N weeks, so add a buffer for the off-by-one + gaps).
        fetch_weeks = max([weeks, *windows]) + 12 if windows else weeks
        date_col = "report_date_as_yyyy_mm_dd"
        frames = []

        for full in markets:
            market_short, exchange = self.split_market_exchange(full)
            cls_list = classifications or self.classifications_for(full, weeks=weeks)

            for cls in cls_list:
                df = self.history(cls, full, weeks=fetch_weeks, exact=True)
                if df.empty:
                    continue

                classification = COTQuery(cls).classification
                analysis = COTAnalysis(df, classification)
                analysis.net_positions()
                analysis.z_scores()
                analysis.cot_index()
                if windows:
                    analysis.cot_index_multi(windows=windows)
                adf = analysis.df

                for cat in analysis.net_map.keys():
                    if cat not in adf.columns:
                        continue
                    rec = pd.DataFrame(
                        {
                            "market": market_short,
                            "exchange": exchange,
                            "classification": classification,
                            "category": cat,
                            "date": adf[date_col],
                            "net": adf[cat],
                            "cot_index": adf.get(f"{cat}_cot_index"),
                            "zscore": adf.get(f"{cat}_zscore"),
                        }
                    )
                    for w in windows:
                        rec[f"cot_index_w{w}"] = adf.get(f"{cat}_cot_index_w{w}")
                    frames.append(rec)

        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)
