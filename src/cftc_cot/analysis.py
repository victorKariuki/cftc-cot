from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List
from .fields import BaseFields, LegacyFields, DisaggregatedFields, TFFFields

class COTAnalysis:
    """
    Computes metrics for CFTC COT datasets.

    Args:
        df: The pandas DataFrame containing the COT data.
        classification: The dataset classification ("legacy", "disaggregated", or "tff").

    Raises:
        ValueError: If an unknown classification is provided.
    """

    # Parent trader groups whose component nets the coarse (legacy) report sums
    # together. Used by :meth:`masking` to expose offsetting positions legacy
    # hides. Legacy itself has no finer split, so it is absent.
    _MASKING_GROUPS = {
        "disaggregated": {
            "commercial": ("prod_merc_net", "swap_net"),
            "non_commercial": ("m_money_net", "other_net"),
        },
        "tff": {
            "reportables": (
                "dealer_net",
                "asset_mgr_net",
                "lev_money_net",
                "other_net",
            ),
        },
    }

    def __init__(self, df: pd.DataFrame, classification: str):
        self.df = df.copy()
        self.classification = classification

        # The client returns rows newest-first; rolling/diff math needs ascending
        # chronological order, so sort by report date when it is available.
        if BaseFields.REPORT_DATE in self.df.columns:
            self.df = self.df.sort_values(BaseFields.REPORT_DATE).reset_index(drop=True)

        if self.classification == "legacy":
            self.net_map = {
                "noncomm_net": (LegacyFields.NONCOMM_LONG, LegacyFields.NONCOMM_SHORT),
                "comm_net": (LegacyFields.COMM_LONG, LegacyFields.COMM_SHORT)
            }
        elif self.classification == "disaggregated":
            self.net_map = {
                "prod_merc_net": (DisaggregatedFields.PROD_MERC_LONG, DisaggregatedFields.PROD_MERC_SHORT),
                "swap_net": (DisaggregatedFields.SWAP_LONG, DisaggregatedFields.SWAP_SHORT),
                "m_money_net": (DisaggregatedFields.M_MONEY_LONG, DisaggregatedFields.M_MONEY_SHORT),
                "other_net": (DisaggregatedFields.OTHER_REPT_LONG, DisaggregatedFields.OTHER_REPT_SHORT)
            }
        elif self.classification == "tff":
            self.net_map = {
                "dealer_net": (TFFFields.DEALER_LONG, TFFFields.DEALER_SHORT),
                "asset_mgr_net": (TFFFields.ASSET_MGR_LONG, TFFFields.ASSET_MGR_SHORT),
                "lev_money_net": (TFFFields.LEV_MONEY_LONG, TFFFields.LEV_MONEY_SHORT),
                "other_net": (TFFFields.OTHER_REPT_LONG, TFFFields.OTHER_REPT_SHORT)
            }
        else:
            raise ValueError(f"Unknown classification: {classification}")

    def net_positions(self) -> pd.DataFrame:
        """
        Calculate net positions (long - short) for each trader category.

        Returns:
            The DataFrame enriched with net position columns.
        """
        for col, (long_f, short_f) in self.net_map.items():
            if long_f in self.df.columns and short_f in self.df.columns:
                self.df[col] = self.df[long_f] - self.df[short_f]
        return self.df

    def z_scores(self, window: int = 52) -> pd.DataFrame:
        """
        Calculate rolling Z-scores for net positions.

        Args:
            window: The rolling window size (number of weeks).

        Returns:
            The DataFrame enriched with Z-score columns.
        """
        self.net_positions()
        for col in self.net_map.keys():
            if col in self.df.columns:
                mean = self.df[col].rolling(window).mean()
                std = self.df[col].rolling(window).std()
                self.df[f"{col}_zscore"] = (self.df[col] - mean) / std
        return self.df

    def cot_index(self, window: int = 156) -> pd.DataFrame:
        """
        Calculate the classic 0-100 COT Index for each net position.

        The COT Index normalizes the current net position against its range over a
        rolling lookback window:
        ``100 * (net - rolling_min) / (rolling_max - rolling_min)``.
        A reading near 100 means the most bullish positioning of the window; near 0,
        the most bearish.

        Args:
            window: The rolling lookback window in weeks (default 156, ~3 years).

        Returns:
            The DataFrame enriched with ``{col}_cot_index`` columns.
        """
        self.net_positions()
        for col in self.net_map.keys():
            if col in self.df.columns:
                roll_min = self.df[col].rolling(window, min_periods=1).min()
                roll_max = self.df[col].rolling(window, min_periods=1).max()
                span = roll_max - roll_min
                # Avoid divide-by-zero when the window is flat.
                self.df[f"{col}_cot_index"] = np.where(
                    span == 0, np.nan, 100 * (self.df[col] - roll_min) / span
                )
        return self.df

    def cot_index_multi(self, windows=(26, 52, 156)) -> pd.DataFrame:
        """
        Compute the COT Index at several rolling windows (a term structure).

        The same position can be an extreme on a short window but mid-range on a
        long one, so charting the index across windows reveals short- vs
        long-term positioning. Emits ``{col}_cot_index_w{N}`` columns; windows
        longer than the available history are skipped.

        Args:
            windows: Iterable of rolling window sizes, in weeks.

        Returns:
            The DataFrame enriched with per-window COT Index columns.
        """
        self.net_positions()
        n = len(self.df)
        for w in windows:
            if w > n:
                continue
            for col in self.net_map.keys():
                if col in self.df.columns:
                    series = self.df[col]
                    roll_min = series.rolling(w, min_periods=1).min()
                    roll_max = series.rolling(w, min_periods=1).max()
                    span = roll_max - roll_min
                    self.df[f"{col}_cot_index_w{w}"] = np.where(
                        span == 0, np.nan, 100 * (series - roll_min) / span
                    )
        return self.df

    def extremes(
        self, threshold: float = 0.95, window: int = 156, persistence: int = 2
    ) -> pd.DataFrame:
        """
        Flag extreme positioning based on the COT Index.

        The COT Index is a rolling min-max normalization, so a trending series
        repeatedly sets new highs/lows and pins to 0/100 — flagging too often. Two
        guards keep the signal meaningful:

        * the first ``window`` rows (an incomplete lookback, where the index is
          degenerate) are never flagged;
        * a reading must stay extreme for at least ``persistence`` consecutive
          weeks before it is flagged.

        Args:
            threshold: Fraction (0-1) marking the bullish cutoff. Values at or above
                ``threshold * 100`` are flagged ``"bullish"``; values at or below
                ``(1 - threshold) * 100`` are flagged ``"bearish"``.
            window: The COT Index lookback window in weeks.
            persistence: Consecutive weeks a reading must remain extreme to flag
                (1 disables the persistence filter).

        Returns:
            The DataFrame enriched with ``{col}_extreme`` columns
            (``"bullish"``/``"bearish"``/``NaN``).

        .. versionchanged:: 0.5.0
            Default ``threshold`` raised to 0.95, ramp rows excluded, and the
            ``persistence`` filter (default 2) added. Earlier versions flagged on
            a bare ``threshold=0.9`` with no ramp/persistence guard.
        """
        self.cot_index(window=window)
        upper = threshold * 100
        lower = (1 - threshold) * 100
        n = len(self.df)
        # Only flag once the rolling window is full (exclude the degenerate ramp).
        full = np.arange(n) >= (window - 1)

        def sustained(mask: np.ndarray) -> np.ndarray:
            if persistence <= 1:
                return mask
            run = pd.Series(mask).rolling(persistence, min_periods=persistence).sum()
            return (run == persistence).to_numpy()

        for col in self.net_map.keys():
            index_col = f"{col}_cot_index"
            if index_col in self.df.columns:
                idx = self.df[index_col].to_numpy()
                bull = sustained((idx >= upper) & full)
                bear = sustained((idx <= lower) & full)
                self.df[f"{col}_extreme"] = np.select(
                    [bull, bear], ["bullish", "bearish"], default=None
                )
        return self.df

    def masking(self) -> pd.DataFrame:
        """
        Quantify how much the coarse (legacy) view masks an internal split.

        For each parent trader group, compare the **gross** positioning
        (``Σ|component net|``) against the **net** (``Σ component net``) the coarse
        report shows. A high ``masking_ratio`` with negatively-correlated
        components means the headline net hides large offsetting positions — e.g.
        producers heavily short while swap dealers are heavily long.

        Only meaningful for the finer classifications; returns an **empty**
        DataFrame for ``legacy`` (it has no sub-split).

        Returns:
            One row per parent group with columns: ``group``, ``components``,
            ``net`` (latest), ``gross`` (latest), ``masking_ratio``
            (mean gross / mean |net| over the series), and ``components_corr``
            (mean pairwise correlation of the component nets).
        """
        self.net_positions()
        groups = self._MASKING_GROUPS.get(self.classification, {})
        rows = []
        for name, comps in groups.items():
            present = [c for c in comps if c in self.df.columns]
            if len(present) < 2:
                continue
            comp_df = self.df[present]
            net = comp_df.sum(axis=1)
            gross = comp_df.abs().sum(axis=1)
            denom = net.abs().mean()
            ratio = float(gross.mean() / denom) if denom else float("nan")
            corrs = [
                comp_df[present[i]].corr(comp_df[present[j]])
                for i in range(len(present))
                for j in range(i + 1, len(present))
            ]
            corr = float(np.nanmean(corrs)) if corrs else float("nan")
            rows.append(
                {
                    "group": name,
                    "components": list(present),
                    "net": float(net.iloc[-1]) if len(net) else float("nan"),
                    "gross": float(gross.iloc[-1]) if len(gross) else float("nan"),
                    "masking_ratio": ratio,
                    "components_corr": corr,
                }
            )
        return pd.DataFrame(rows)

    def long_short_ratios(self) -> pd.DataFrame:
        """
        Calculate long/short ratios for each trader category.

        Returns:
            The DataFrame enriched with ``{category}_ls_ratio`` columns.
        """
        for col, (long_f, short_f) in self.net_map.items():
            if long_f in self.df.columns and short_f in self.df.columns:
                root = col[:-4] if col.endswith("_net") else col
                short = self.df[short_f].replace(0, np.nan)
                self.df[f"{root}_ls_ratio"] = self.df[long_f] / short
        return self.df

    def percentile_rank(self, column: str) -> float:
        """
        Return the current (most recent) value's percentile rank within its history.

        Args:
            column: The column to rank. If it is one of the net-position keys and not
                yet present, net positions are computed first.

        Returns:
            The percentile rank (0.0-1.0) of the last row's value, or ``nan`` if the
            column is unavailable or empty.

        Raises:
            KeyError: If the column cannot be found or derived.
        """
        if column not in self.df.columns and column in self.net_map:
            self.net_positions()
        if column not in self.df.columns:
            raise KeyError(f"Column not found: {column}")
        series = self.df[column].dropna()
        if series.empty:
            return float("nan")
        return float(series.rank(pct=True).iloc[-1])

    def wow_change(self) -> pd.DataFrame:
        """
        Calculate week-over-week change in net positions for each category.

        Rows are assumed to be in ascending chronological order (handled in the
        constructor).

        Returns:
            The DataFrame enriched with ``{col}_wow`` columns.
        """
        self.net_positions()
        for col in self.net_map.keys():
            if col in self.df.columns:
                self.df[f"{col}_wow"] = self.df[col].diff()
        return self.df
