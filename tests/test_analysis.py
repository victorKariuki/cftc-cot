import math
import numpy as np
import pandas as pd
import pytest
from cftc_cot.analysis import COTAnalysis
from cftc_cot.fields import LegacyFields, DisaggregatedFields

def test_net_positions():
    data = {
        LegacyFields.NONCOMM_LONG: [100, 200],
        LegacyFields.NONCOMM_SHORT: [50, 150]
    }
    df = pd.DataFrame(data)
    analysis = COTAnalysis(df, classification="legacy")
    df_result = analysis.net_positions()

    assert "noncomm_net" in df_result.columns
    assert df_result["noncomm_net"].tolist() == [50, 50]


def _legacy_df(longs, shorts, dates=None):
    data = {
        LegacyFields.NONCOMM_LONG: longs,
        LegacyFields.NONCOMM_SHORT: shorts,
    }
    if dates is not None:
        data[LegacyFields.REPORT_DATE] = pd.to_datetime(dates)
    return pd.DataFrame(data)


def test_constructor_sorts_by_date():
    # Newest-first input (as returned by the client) must be sorted ascending.
    df = _legacy_df([300, 200, 100], [0, 0, 0],
                    dates=["2024-03-01", "2024-02-01", "2024-01-01"])
    analysis = COTAnalysis(df, classification="legacy")
    dates = analysis.df[LegacyFields.REPORT_DATE].tolist()
    assert dates == sorted(dates)


def test_cot_index_min_and_max():
    # Net = [200, 100, 300]: the first row has no range yet (NaN); once the window
    # has seen a spread, the window-min maps to 0 and the window-max to 100.
    df = _legacy_df([200, 100, 300], [0, 0, 0])
    analysis = COTAnalysis(df, classification="legacy")
    idx = analysis.cot_index(window=52)["noncomm_net_cot_index"]
    assert math.isnan(idx.iloc[0])  # single observation -> undefined range
    assert idx.iloc[1] == 0.0       # window-min
    assert idx.iloc[2] == 100.0     # window-max


def test_extremes_excludes_ramp_and_requires_persistence():
    # Monotonic rising net -> COT index pins to 100 once the window has a spread.
    # window=3 => ramp is the first 2 rows (incomplete window); persistence=2 means
    # a flag needs two consecutive post-ramp extremes.
    df = _legacy_df([10, 20, 30, 40, 50], [0, 0, 0, 0, 0])
    analysis = COTAnalysis(df, classification="legacy")
    ex = analysis.extremes(threshold=0.95, window=3, persistence=2)["noncomm_net_extreme"]
    assert pd.isna(ex.iloc[0])  # ramp (window not full)
    assert pd.isna(ex.iloc[1])  # ramp
    assert pd.isna(ex.iloc[2])  # first full window, but not yet sustained 2 weeks
    assert ex.iloc[3] == "bullish"  # sustained
    assert ex.iloc[4] == "bullish"


def test_extremes_persistence_one_flags_first_full_window():
    df = _legacy_df([10, 20, 30, 40, 50], [0, 0, 0, 0, 0])
    analysis = COTAnalysis(df, classification="legacy")
    ex = analysis.extremes(threshold=0.95, window=3, persistence=1)["noncomm_net_extreme"]
    assert pd.isna(ex.iloc[1])      # still in the ramp
    assert ex.iloc[2] == "bullish"  # first full window flags immediately


def test_extremes_bearish_on_falling_net():
    df = _legacy_df([50, 40, 30, 20, 10], [0, 0, 0, 0, 0])
    analysis = COTAnalysis(df, classification="legacy")
    ex = analysis.extremes(threshold=0.95, window=3, persistence=2)["noncomm_net_extreme"]
    assert ex.iloc[3] == "bearish"
    assert ex.iloc[4] == "bearish"


def test_cot_index_multi_emits_per_window_and_skips_oversized():
    df = _legacy_df([10, 20, 30, 40, 50], [0, 0, 0, 0, 0])
    analysis = COTAnalysis(df, classification="legacy")
    out = analysis.cot_index_multi(windows=(3, 99))
    assert "noncomm_net_cot_index_w3" in out.columns
    assert "noncomm_net_cot_index_w99" not in out.columns  # window > history -> skipped
    assert out["noncomm_net_cot_index_w3"].iloc[-1] == 100.0


def _disagg_df(pm_long, pm_short, swap_long, swap_short):
    return pd.DataFrame(
        {
            DisaggregatedFields.PROD_MERC_LONG: pm_long,
            DisaggregatedFields.PROD_MERC_SHORT: pm_short,
            DisaggregatedFields.SWAP_LONG: swap_long,
            DisaggregatedFields.SWAP_SHORT: swap_short,
        }
    )


def test_masking_detects_offsetting_components():
    # producers net short, swaps net long -> headline "commercial" net is small but
    # gross is large, and the two components are negatively correlated.
    df = _disagg_df(pm_long=[0, 0], pm_short=[100, 200],
                    swap_long=[120, 180], swap_short=[0, 0])
    m = COTAnalysis(df, classification="disaggregated").masking()
    row = m[m["group"] == "commercial"].iloc[0]
    assert row["masking_ratio"] > 5          # gross >> |net|
    assert row["components_corr"] < 0         # components offset
    # non_commercial group is absent (its component columns weren't provided)
    assert "non_commercial" not in set(m["group"])


def test_masking_empty_for_legacy():
    df = _legacy_df([100, 200], [50, 50])
    m = COTAnalysis(df, classification="legacy").masking()
    assert m.empty


def test_long_short_ratios():
    df = _legacy_df([200, 300], [100, 100])
    analysis = COTAnalysis(df, classification="legacy")
    result = analysis.long_short_ratios()
    assert "noncomm_ls_ratio" in result.columns
    assert result["noncomm_ls_ratio"].tolist() == [2.0, 3.0]


def test_percentile_rank():
    df = _legacy_df([100, 200, 300, 400], [0, 0, 0, 0])
    analysis = COTAnalysis(df, classification="legacy")
    # Last net is the largest -> percentile rank 1.0
    assert analysis.percentile_rank("noncomm_net") == 1.0


def test_wow_change():
    df = _legacy_df([100, 250, 200], [0, 0, 0])
    analysis = COTAnalysis(df, classification="legacy")
    result = analysis.wow_change()
    wow = result["noncomm_net_wow"]
    assert math.isnan(wow.iloc[0])
    assert wow.iloc[1] == 150
    assert wow.iloc[2] == -50
