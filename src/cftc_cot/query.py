from __future__ import annotations
import pandas as pd
from sodapy import Socrata
from datetime import datetime, timedelta
from typing import Optional, List, Any
import logging
from .exceptions import COTQueryError, COTClassificationError

logger = logging.getLogger(__name__)

class COTQuery:
    """Complete SODA2 query builder for all 6 CFTC COT datasets."""

    DATASETS = {
        "legacy_futures": "6dca-aqww",
        "legacy_combined": "jun7-fc8e",
        "legacy": "jun7-fc8e",
        "disaggregated_futures": "72hh-3qpy",
        "disaggregated_combined": "kh3c-gbw2",
        "disaggregated": "kh3c-gbw2",
        "tff_futures": "gpe5-46if",
        "tff_combined": "yw9f-hn96",
        "tff": "yw9f-hn96",
    }

    def __init__(self, dataset: str = "legacy", app_token: Optional[str] = None):
        """
        Initialize query for a specific CFTC dataset.

        Args:
            dataset: The identifier for the dataset (e.g., "legacy", "disaggregated", "tff").
            app_token: Optional Socrata API app token for higher rate limits.

        Raises:
            ValueError: If the dataset name is not recognized.
        """
        if dataset not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset}")
        
        self.dataset_id = self.DATASETS[dataset]
        self.dataset_name = dataset
        self.classification = self._get_classification(dataset)
        self.client = Socrata("publicreporting.cftc.gov", app_token)
        self._where_clauses: List[str] = []
        self._select_fields: Optional[List[str]] = None
        self._order_by: Optional[str] = None
        self._limit: int = 50000
        self._offset: int = 0

    def _get_classification(self, dataset: str) -> str:
        if "legacy" in dataset:
            return "legacy"
        elif "disaggregated" in dataset:
            return "disaggregated"
        elif "tff" in dataset:
            return "tff"
        return "legacy"

    def where(self, condition: str) -> COTQuery:
        """Add WHERE clause."""
        self._where_clauses.append(condition)
        return self

    def select(self, *columns: str) -> COTQuery:
        """Select specific columns."""
        self._select_fields = list(columns)
        return self

    def order_by(self, column: str, desc: bool = False) -> COTQuery:
        """Sort results."""
        direction = "DESC" if desc else "ASC"
        self._order_by = f"{column} {direction}"
        return self

    def limit(self, n: int) -> COTQuery:
        """Limit results."""
        self._limit = min(n, 50000)
        return self

    def offset(self, n: int) -> COTQuery:
        """Skip rows."""
        self._offset = n
        return self

    def date_range(self, start: str, end: str) -> COTQuery:
        """Filter by date range."""
        self.where(f"report_date_as_yyyy_mm_dd >= '{start}'")
        self.where(f"report_date_as_yyyy_mm_dd <= '{end}'")
        return self

    def date_after(self, date: str) -> COTQuery:
        """Filter to dates >= date."""
        self.where(f"report_date_as_yyyy_mm_dd >= '{date}'")
        return self

    def date_before(self, date: str) -> COTQuery:
        """Filter to dates <= date."""
        self.where(f"report_date_as_yyyy_mm_dd <= '{date}'")
        return self

    def last_n_weeks(self, n: int = 52) -> COTQuery:
        """Filter to last N weeks."""
        start_date = (datetime.now() - timedelta(weeks=n)).strftime("%Y-%m-%d")
        return self.date_after(start_date)

    def market(self, name: str, exact: bool = False) -> COTQuery:
        """Filter by market name (case-insensitive)."""
        name_upper = name.upper()
        if exact:
            self.where(f"upper(market_and_exchange_names) = '{name_upper}'")
        else:
            self.where(f"upper(market_and_exchange_names) like '{name_upper}%'")
        return self

    def markets_in(self, *names: str) -> COTQuery:
        """Filter to multiple markets (case-insensitive)."""
        conditions = [f"upper(market_and_exchange_names) like '{name.upper()}%'" for name in names]
        self.where(f"({' OR '.join(conditions)})")
        return self

    def _check_classification(self, allowed: str) -> None:
        if self.classification != allowed:
            raise COTClassificationError(f"Method only works with {allowed} datasets")

    def noncomm_long_gt(self, amount: int) -> COTQuery:
        """Non-commercial long > amount (Legacy only)."""
        self._check_classification("legacy")
        self.where(f"noncomm_positions_long_all > {amount}")
        return self

    def noncomm_short_gt(self, amount: int) -> COTQuery:
        """Non-commercial short > amount (Legacy only)."""
        self._check_classification("legacy")
        self.where(f"noncomm_positions_short_all > {amount}")
        return self

    def comm_long_gt(self, amount: int) -> COTQuery:
        """Commercial long > amount (Legacy only)."""
        self._check_classification("legacy")
        self.where(f"comm_positions_long_all > {amount}")
        return self

    def comm_short_gt(self, amount: int) -> COTQuery:
        """Commercial short > amount (Legacy only)."""
        self._check_classification("legacy")
        self.where(f"comm_positions_short_all > {amount}")
        return self

    def swap_dealers_long_gt(self, amount: int) -> COTQuery:
        """Swap dealer long > amount (Disaggregated only)."""
        self._check_classification("disaggregated")
        self.where(f"swap_positions_long_all > {amount}")
        return self

    def managed_money_long_gt(self, amount: int) -> COTQuery:
        """Managed money long > amount (Disaggregated only)."""
        self._check_classification("disaggregated")
        self.where(f"m_money_positions_long_all > {amount}")
        return self

    def producer_merchant_short_gt(self, amount: int) -> COTQuery:
        """Producer/merchant short > amount (Disaggregated only)."""
        self._check_classification("disaggregated")
        self.where(f"prod_merc_positions_short > {amount}")
        return self

    def dealer_long_gt(self, amount: int) -> COTQuery:
        """Dealer long > amount (TFF only)."""
        self._check_classification("tff")
        self.where(f"dealer_positions_long_all > {amount}")
        return self

    def asset_manager_long_gt(self, amount: int) -> COTQuery:
        """Asset manager long > amount (TFF only)."""
        self._check_classification("tff")
        self.where(f"asset_mgr_positions_long > {amount}")
        return self

    def leveraged_funds_long_gt(self, amount: int) -> COTQuery:
        """Leveraged funds long > amount (TFF only)."""
        self._check_classification("tff")
        self.where(f"lev_money_positions_long > {amount}")
        return self

    def long_positions_gt(self, amount: int) -> COTQuery:
        """Total reportable long > amount (All datasets)."""
        self.where(f"tot_rept_positions_long_all > {amount}")
        return self

    def short_positions_gt(self, amount: int) -> COTQuery:
        """Total reportable short > amount (All datasets)."""
        self.where(f"tot_rept_positions_short > {amount}")
        return self

    def order_by_date(self, desc: bool = True) -> COTQuery:
        """Sort by date."""
        return self.order_by("report_date_as_yyyy_mm_dd", desc=desc)

    def to_soda2(self) -> str:
        """Get the SODA2 query string."""
        query_parts = []
        if self._select_fields:
            query_parts.append(f"SELECT {', '.join(self._select_fields)}")
        if self._where_clauses:
            query_parts.append(f"WHERE {' AND '.join(self._where_clauses)}")
        if self._order_by:
            query_parts.append(f"ORDER BY {self._order_by}")
        if self._limit:
            query_parts.append(f"LIMIT {self._limit}")
        if self._offset:
            query_parts.append(f"OFFSET {self._offset}")
        return " ".join(query_parts)

    def count(self) -> int:
        """
        Count matching records.

        Returns:
            The number of records as an integer, or 0 if an error occurs.
        """
        query = "SELECT count(*) as cnt"
        if self._where_clauses:
            query += f" WHERE {' AND '.join(self._where_clauses)}"
        try:
            results = self.client.get(self.dataset_id, query=query)
            return int(results[0]["cnt"]) if results else 0
        except Exception as e:
            logger.error(f"Error counting records: {e}")
            return 0

    def execute(self) -> pd.DataFrame:
        """
        Execute query and return DataFrame.

        Returns:
            A pandas DataFrame containing the query results. If the query fails,
            returns an empty DataFrame.
        """
        try:
            results = self.client.get(
                self.dataset_id,
                select=", ".join(self._select_fields) if self._select_fields else None,
                where=" AND ".join(self._where_clauses) if self._where_clauses else None,
                order=self._order_by,
                limit=self._limit,
                offset=self._offset,
            )
            if not results:
                return pd.DataFrame()
            df = pd.DataFrame(results)
            df.columns = df.columns.str.lower()
            if "report_date_as_yyyy_mm_dd" in df.columns:
                df["report_date_as_yyyy_mm_dd"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"])
            numeric_cols = df.select_dtypes(include=['object']).columns
            for col in numeric_cols:
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except Exception:
                    pass
            return df
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return pd.DataFrame()

    def fetch_all_pages(self, page_size: int = 50000) -> pd.DataFrame:
        """Auto-paginate and fetch all results."""
        all_results = []
        offset = 0
        while True:
            self._offset = offset
            df = self.execute()
            if df.empty:
                break
            all_results.append(df)
            if len(df) < page_size:
                break
            offset += page_size
        return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
