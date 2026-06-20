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
