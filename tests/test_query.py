import pytest
from requests.exceptions import ConnectionError as ReqConnectionError
from cftc_cot.query import COTQuery, _q, _num
from cftc_cot.exceptions import COTClassificationError, COTConnectionError, COTQueryError

def test_query_initialization():
    query = COTQuery("legacy")
    assert query.dataset_name == "legacy"
    assert query.classification == "legacy"

def test_classification_guard():
    query = COTQuery("tff")
    with pytest.raises(COTClassificationError):
        query.noncomm_long_gt(100)

def test_to_soda2_query():
    query = COTQuery("legacy").where("condition").limit(10)
    assert "WHERE condition" in query.to_soda2()
    assert "LIMIT 10" in query.to_soda2()


def test_quote_escaping_helper():
    assert _q("O'Brien") == "O''Brien"


def test_market_escapes_apostrophe():
    query = COTQuery("legacy").market("O'Brien")
    # Escaped literal must appear; no lone apostrophe that would break the query.
    assert "O''BRIEN" in query.to_soda2()


def test_num_coerces_valid():
    assert _num(5000) == 5000
    assert _num("5000") == 5000
    assert _num(5000.9) == 5000


def test_num_rejects_injection():
    with pytest.raises(COTQueryError):
        _num("0 OR 1=1")


def test_numeric_filter_rejects_injection():
    # The amount is interpolated into the query, so non-numeric input must be rejected.
    with pytest.raises(COTQueryError):
        COTQuery("legacy").noncomm_long_gt("0 OR 1=1")


def test_numeric_filter_accepts_int():
    q = COTQuery("legacy").noncomm_long_gt(5000)
    assert "noncomm_positions_long_all > 5000" in q.to_soda2()


def test_exchange_partial_match():
    q = COTQuery("legacy").exchange("Chicago Mercantile Exchange")
    soda = q.to_soda2()
    assert "like '%CHICAGO MERCANTILE EXCHANGE%'" in soda


def test_exchange_exact_matches_trailing_segment():
    q = COTQuery("legacy").exchange("Chicago Mercantile Exchange", exact=True)
    # Exact = the segment after the final " - ".
    assert "like '% - CHICAGO MERCANTILE EXCHANGE'" in q.to_soda2()


def test_exchange_escapes_apostrophe():
    q = COTQuery("legacy").exchange("O'Brien Exchange")
    assert "O''BRIEN EXCHANGE" in q.to_soda2()


def test_distinct_values_builds_query_with_filters():
    query = COTQuery("legacy").last_n_weeks(4)
    captured = {}

    def fake_get(dataset_id, **kwargs):
        captured["query"] = kwargs["query"]
        return [
            {"market_and_exchange_names": "GOLD - COMMODITY EXCHANGE INC."},
            {"market_and_exchange_names": "SILVER - COMMODITY EXCHANGE INC."},
        ]

    query.client.get = fake_get
    values = query.distinct_values("market_and_exchange_names")

    assert values == [
        "GOLD - COMMODITY EXCHANGE INC.",
        "SILVER - COMMODITY EXCHANGE INC.",
    ]
    assert captured["query"].startswith("SELECT DISTINCT market_and_exchange_names")
    assert "WHERE report_date_as_yyyy_mm_dd >=" in captured["query"]
    assert "LIMIT" in captured["query"]


def test_retry_succeeds_after_transient_failure():
    query = COTQuery("legacy", max_retries=3, backoff_base=0)
    calls = {"n": 0}

    def flaky_get(dataset_id, **kwargs):
        calls["n"] += 1
        if calls["n"] < 2:
            raise ReqConnectionError("boom")
        return [{"cnt": "5"}]

    query.client.get = flaky_get
    assert query._request_with_retry(query="SELECT count(*)") == [{"cnt": "5"}]
    assert calls["n"] == 2


def test_retry_exhaustion_raises():
    query = COTQuery("legacy", max_retries=2, backoff_base=0)

    def always_fail(dataset_id, **kwargs):
        raise ReqConnectionError("down")

    query.client.get = always_fail
    with pytest.raises(COTConnectionError):
        query._request_with_retry(query="SELECT count(*)")
