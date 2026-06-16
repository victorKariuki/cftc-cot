from __future__ import annotations
import pandas as pd
import logging
from typing import Optional
from .query import COTQuery

logger = logging.getLogger(__name__)

class COTClient:
    """
    Main entry point for the CFTC COT SDK.

    Args:
        app_token: Optional Socrata API app token for higher rate limits.
        cache: Optional caching mechanism (e.g., "memory", "disk").
    """

    def __init__(self, app_token: Optional[str] = None, cache: Optional[str] = None):
        # sodapy handles app_token internally if passed to Socrata
        self.app_token = app_token
        self.cache = cache

    # Factory methods for COTQuery
    def legacy(self) -> COTQuery: 
        """Return a query builder for Legacy Combined data."""
        return COTQuery("legacy_combined", app_token=self.app_token)
    
    def legacy_futures(self) -> COTQuery: 
        """Return a query builder for Legacy Futures Only data."""
        return COTQuery("legacy_futures", app_token=self.app_token)
    
    def disaggregated(self) -> COTQuery: 
        """Return a query builder for Disaggregated Combined data."""
        return COTQuery("disaggregated_combined", app_token=self.app_token)
    
    def disaggregated_futures(self) -> COTQuery: 
        """Return a query builder for Disaggregated Futures Only data."""
        return COTQuery("disaggregated_futures", app_token=self.app_token)
    
    def tff(self) -> COTQuery: 
        """Return a query builder for TFF Combined data."""
        return COTQuery("tff_combined", app_token=self.app_token)
    
    def tff_futures(self) -> COTQuery: 
        """Return a query builder for TFF Futures Only data."""
        return COTQuery("tff_futures", app_token=self.app_token)

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
        return COTQuery(dataset, app_token=self.app_token).market(market).order_by_date(desc=True).limit(1).execute()

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
        return COTQuery(dataset, app_token=self.app_token).market(market).last_n_weeks(weeks).order_by_date(desc=True).execute()

    def list_markets(self, dataset: str) -> list[str]:
        """
        List all unique available markets for a given dataset.

        Args:
            dataset: The dataset name.

        Returns:
            A list of unique market names.
        """
        query = COTQuery(dataset, app_token=self.app_token)
        # SODA2 query for distinct values
        q = "SELECT DISTINCT market_and_exchange_names"
        
        try:
            results = query.client.get(query.dataset_id, query=q)
            return [r["market_and_exchange_names"] for r in results]
        except Exception as e:
            logger.error(f"Error fetching market list: {e}")
            return []
