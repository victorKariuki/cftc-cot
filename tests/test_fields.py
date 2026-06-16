from cftc_cot.fields import LegacyFields, DisaggregatedFields, TFFFields

def test_legacy_fields():
    assert LegacyFields.NONCOMM_LONG == "noncomm_positions_long_all"
    assert LegacyFields.NONCOMM_SPREAD == "noncomm_postions_spread_all"

def test_disagg_fields():
    assert DisaggregatedFields.SWAP_SHORT == "swap__positions_short_all"
    assert DisaggregatedFields.PROD_MERC_LONG == "prod_merc_positions_long"

def test_tff_fields():
    assert TFFFields.DEALER_LONG == "dealer_positions_long_all"
    assert TFFFields.ASSET_MGR_LONG == "asset_mgr_positions_long"
