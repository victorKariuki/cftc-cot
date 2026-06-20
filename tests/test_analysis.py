import math
import numpy as np
import pandas as pd
import pytest
from cftc_cot.analysis import COTAnalysis
from cftc_cot.fields import LegacyFields

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


def test_extremes_flags():
    df = _legacy_df([200, 100, 300], [0, 0, 0])
    analysis = COTAnalysis(df, classification="legacy")
    extreme = analysis.extremes(threshold=0.9, window=52)["noncomm_net_extreme"]
    assert extreme.iloc[1] == "bearish"   # COT index 0
    assert extreme.iloc[2] == "bullish"   # COT index 100


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
