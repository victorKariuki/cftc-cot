from __future__ import annotations
import pandas as pd
from typing import Optional
from .query import COTQuery

class COTClient:
    """Main entry point for the CFTC COT SDK."""

    def __init__(self, app_token: Optional[str] = None, cache: Optional[str] = None):
        # sodapy handles app_token internally if passed to Socrata
        self.app_token = app_token
        self.cache = cache

    # Factory methods for COTQuery
    def legacy(self) -> COTQuery: return COTQuery("legacy_combined", app_token=self.app_token)
    def legacy_futures(self) -> COTQuery: return COTQuery("legacy_futures", app_token=self.app_token)
    def disaggregated(self) -> COTQuery: return COTQuery("disaggregated_combined", app_token=self.app_token)
    def disaggregated_futures(self) -> COTQuery: return COTQuery("disaggregated_futures", app_token=self.app_token)
    def tff(self) -> COTQuery: return COTQuery("tff_combined", app_token=self.app_token)
    def tff_futures(self) -> COTQuery: return COTQuery("tff_futures", app_token=self.app_token)

    # High-level convenience methods
    def latest(self, dataset: str, market: str) -> pd.DataFrame:
        """Fetch latest report for a market."""
        return COTQuery(dataset, app_token=self.app_token).market(market).order_by_date(desc=True).limit(1).execute()

    def history(self, dataset: str, market: str, weeks: int = 52) -> pd.DataFrame:
        """Fetch N-week history for a market."""
        return COTQuery(dataset, app_token=self.app_token).market(market).last_n_weeks(weeks).order_by_date(desc=True).execute()

    def list_markets(self, dataset: str) -> list[str]:
        """List all unique available markets."""
        query = COTQuery(dataset, app_token=self.app_token)
        # SODA2 query for distinct values
        q = f"SELECT DISTINCT market_and_exchange_names"
        
        try:
            results = query.client.get(query.dataset_id, query=q)
            return [r["market_and_exchange_names"] for r in results]
        except Exception as e:
            logger.error(f"Error fetching market list: {e}")
            return []
