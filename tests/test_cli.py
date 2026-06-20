import pandas as pd
import pytest
from cftc_cot import cli


def test_build_parser_latest():
    args = cli.build_parser().parse_args(
        ["latest", "--dataset", "legacy", "--market", "Crude Oil"]
    )
    assert args.command == "latest"
    assert args.market == "Crude Oil"


def test_build_parser_index_defaults():
    args = cli.build_parser().parse_args(["index", "--market", "Gold"])
    assert args.window == 156
    assert args.dataset == "legacy"


def test_build_parser_requires_command():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])


def test_classification_for():
    assert cli.classification_for("legacy") == "legacy"
    assert cli.classification_for("disaggregated_futures") == "disaggregated"
    assert cli.classification_for("tff_combined") == "tff"


def test_main_latest_monkeypatched(monkeypatch, capsys):
    sample = pd.DataFrame({"market_and_exchange_names": ["CRUDE OIL"], "open_interest_all": [123]})

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def latest(self, dataset, market):
            return sample

    monkeypatch.setattr(cli, "COTClient", FakeClient)
    rc = cli.main(["--format", "csv", "latest", "--market", "Crude Oil"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "CRUDE OIL" in out


def test_main_markets_monkeypatched(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def list_markets(self, dataset):
            return ["GOLD", "SILVER"]

    monkeypatch.setattr(cli, "COTClient", FakeClient)
    rc = cli.main(["markets", "--dataset", "legacy"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "GOLD" in out and "SILVER" in out
