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
    def latest(self, dataset: str, market: str) -> pd.DataFrame:
        """
        Fetch the latest report for a specified market.

        Args:
            dataset: The dataset name (e.g., "legacy", "disaggregated", "tff").
            market: The market name.

        Returns:
            A pandas DataFrame with the latest report record.
        """
        return self._query(dataset).market(market).order_by_date(desc=True).limit(1).execute()

    def history(self, dataset: str, market: str, weeks: int = 52) -> pd.DataFrame:
        """
        Fetch N-week history for a specified market.

        Args:
            dataset: The dataset name.
            market: The market name.
            weeks: Number of weeks of historical data to fetch.

        Returns:
            A pandas DataFrame with historical records.
        """
        return self._query(dataset).market(market).last_n_weeks(weeks).order_by_date(desc=True).execute()

    def list_markets(self, dataset: str) -> list[str]:
        """
        List all unique available markets for a given dataset.

        Args:
            dataset: The dataset name.

        Returns:
            A list of unique market names.
        """
        query = self._query(dataset)
        # SODA2 query for distinct values
        q = "SELECT DISTINCT market_and_exchange_names"

        try:
            results = query._request_with_retry(query=q)
            return [r["market_and_exchange_names"] for r in results]
        except Exception as e:
            logger.error(f"Error fetching market list: {e}")
            return []
