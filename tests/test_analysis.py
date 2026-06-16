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
