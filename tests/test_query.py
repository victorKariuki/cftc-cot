import pytest
from cftc_cot.query import COTQuery
from cftc_cot.exceptions import COTClassificationError

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
