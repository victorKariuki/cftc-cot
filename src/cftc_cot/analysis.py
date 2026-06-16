from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List
from .fields import LegacyFields, DisaggregatedFields, TFFFields

class COTAnalysis:
    """Computes metrics for CFTC COT datasets."""

    def __init__(self, df: pd.DataFrame, classification: str):
        self.df = df.copy()
        self.classification = classification
        
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
        """Calculate net positions (long - short)."""
        for col, (long_f, short_f) in self.net_map.items():
            if long_f in self.df.columns and short_f in self.df.columns:
                self.df[col] = self.df[long_f] - self.df[short_f]
        return self.df

    def z_scores(self, window: int = 52) -> pd.DataFrame:
        """Calculate Z-scores for net positions."""
        self.net_positions()
        for col in self.net_map.keys():
            if col in self.df.columns:
                mean = self.df[col].rolling(window).mean()
                std = self.df[col].rolling(window).std()
                self.df[f"{col}_zscore"] = (self.df[col] - mean) / std
        return self.df
