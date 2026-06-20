import asyncio
import json

import pandas as pd
import pytest

pytest.importorskip("mcp")

from cftc_cot import mcp_server
from cftc_cot.fields import LegacyFields
from mcp.server.fastmcp.exceptions import ToolError


def _legacy_df():
    return pd.DataFrame({
        LegacyFields.REPORT_DATE: pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
        LegacyFields.NONCOMM_LONG: [200, 100, 300],
        LegacyFields.NONCOMM_SHORT: [0, 0, 0],
        LegacyFields.COMM_LONG: [50, 50, 50],
        LegacyFields.COMM_SHORT: [10, 20, 30],
    })


class FakeClient:
    def __init__(self, df=None):
        self._df = _legacy_df() if df is None else df
        self.calls = []

    def history(self, dataset, market, weeks=52, exact=False):
        self.calls.append({"fn": "history", "dataset": dataset, "market": market,
                           "weeks": weeks, "exact": exact})
        return self._df.copy()

    def latest(self, dataset, market, exact=False):
        self.calls.append({"fn": "latest", "dataset": dataset, "market": market, "exact": exact})
        return self._df.tail(1).copy()

    def list_markets(self, dataset):
        self.calls.append({"fn": "list_markets", "dataset": dataset})
        return ["CRUDE OIL", "GOLD"]


@pytest.fixture
def fake(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(mcp_server, "_client", client)
    return client


def run(coro):
    return asyncio.run(coro)


# --- registration -----------------------------------------------------------
def test_tools_registered():
    names = {t.name for t in run(mcp_server.mcp.list_tools())}
    expected = {
        "list_markets", "latest_report", "history", "net_positions", "cot_index",
        "z_scores", "long_short_ratios", "wow_change", "percentile_rank", "extremes",
    }
    assert expected <= names


def test_prompts_registered():
    names = {p.name for p in run(mcp_server.mcp.list_prompts())}
    assert {"analyze_market", "positioning_summary"} <= names


# --- tool behavior ----------------------------------------------------------
def test_list_markets(fake):
    assert run(mcp_server.list_markets("legacy")) == ["CRUDE OIL", "GOLD"]


def test_latest_report_success(fake):
    rows = run(mcp_server.latest_report("Crude Oil", exact=True))
    assert len(rows) == 1
    assert rows[0][LegacyFields.NONCOMM_LONG] == 300


def test_history_success(fake):
    rows = run(mcp_server.history("Crude Oil"))
    assert len(rows) == 3


def test_cot_index_success(fake):
    rows = run(mcp_server.cot_index("Crude Oil", window=52, tail=3))
    assert "noncomm_net_cot_index" in rows[-1]


def test_net_positions_success(fake):
    rows = run(mcp_server.net_positions("Crude Oil"))
    assert rows[-1]["noncomm_net"] == 300


def test_percentile_rank_returns_float(fake):
    val = run(mcp_server.percentile_rank("Crude Oil", "noncomm_net"))
    assert isinstance(val, float)
    assert val == 1.0  # last net (300) is the largest in history


def test_percentile_rank_bad_column(fake):
    with pytest.raises(ToolError):
        run(mcp_server.percentile_rank("Crude Oil", "not_a_column"))


# --- error handling ---------------------------------------------------------
def test_unknown_dataset_raises(fake):
    with pytest.raises(ToolError):
        run(mcp_server.latest_report("Crude Oil", dataset="bogus"))


def test_empty_fetch_raises(monkeypatch):
    empty = FakeClient(df=pd.DataFrame())
    monkeypatch.setattr(mcp_server, "_client", empty)
    with pytest.raises(ToolError):
        run(mcp_server.history("Nonexistent Market"))


def test_exact_forwarded(fake):
    run(mcp_server.history("Crude Oil", exact=True))
    assert fake.calls[-1]["exact"] is True


# --- resources & prompts ----------------------------------------------------
def test_datasets_resource():
    data = json.loads(mcp_server.datasets_resource())
    assert "legacy" in data["datasets"]
    assert "legacy" in data["classifications"]


def test_fields_resource():
    data = json.loads(mcp_server.fields_resource("legacy"))
    assert data["fields"]["NONCOMM_LONG"] == LegacyFields.NONCOMM_LONG


def test_fields_resource_bad_classification():
    with pytest.raises(ValueError):
        mcp_server.fields_resource("nope")


def test_prompt_nonempty():
    text = mcp_server.analyze_market("Crude Oil")
    assert "Crude Oil" in text and "cot_index" in text
