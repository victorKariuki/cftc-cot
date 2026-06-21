import pandas as pd
from cftc_cot.client import COTClient
from cftc_cot.fields import LegacyFields


def test_classifications_for(monkeypatch):
    client = COTClient()
    pools = {
        "legacy": ["GOLD - X", "VIX - Y"],
        "disaggregated": ["GOLD - X"],
        "tff": ["VIX - Y"],
    }
    monkeypatch.setattr(client, "list_markets", lambda cls, weeks=None: pools[cls])

    assert client.classifications_for("GOLD - X") == ["legacy", "disaggregated"]
    assert client.classifications_for("VIX - Y") == ["legacy", "tff"]
    assert client.classifications_for("UNKNOWN - Z") == []


def test_compare_long_form(monkeypatch):
    client = COTClient()
    df = pd.DataFrame(
        {
            LegacyFields.NONCOMM_LONG: [100, 200, 300],
            LegacyFields.NONCOMM_SHORT: [0, 0, 0],
            LegacyFields.REPORT_DATE: pd.to_datetime(
                ["2024-01-01", "2024-01-08", "2024-01-15"]
            ),
        }
    )
    monkeypatch.setattr(client, "classifications_for", lambda m, weeks=None: ["legacy"])
    monkeypatch.setattr(
        client, "history", lambda cls, full, weeks=None, exact=True: df.copy()
    )

    out = client.compare("GOLD - COMMODITY EXCHANGE INC.", weeks=10, windows=(2,))

    expected = {
        "market", "exchange", "classification", "category", "date",
        "net", "cot_index", "zscore", "cot_index_w2",
    }
    assert expected.issubset(out.columns)
    # Only noncomm_net is derivable from the provided fields.
    assert set(out["category"]) == {"noncomm_net"}
    assert (out["market"] == "GOLD").all()
    assert (out["exchange"] == "COMMODITY EXCHANGE INC.").all()
    assert out["cot_index_w2"].notna().any()


def test_compare_empty_when_no_data(monkeypatch):
    client = COTClient()
    monkeypatch.setattr(client, "classifications_for", lambda m, weeks=None: ["legacy"])
    monkeypatch.setattr(
        client, "history", lambda cls, full, weeks=None, exact=True: pd.DataFrame()
    )
    assert client.compare("NOPE - X").empty
