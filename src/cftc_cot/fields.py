from typing import List, Final

class BaseFields:
    # Common to all datasets
    REPORT_DATE: Final = "report_date_as_yyyy_mm_dd"
    YYYY_WEEK: Final = "yyyy_report_week_ww"
    MARKET_NAME: Final = "market_and_exchange_names"
    CONTRACT_NAME: Final = "contract_market_name"
    COMMODITY: Final = "commodity"
    COMMODITY_NAME: Final = "commodity_name"
    COMMODITY_GROUP: Final = "commodity_group_name"
    COMMODITY_SUBGROUP: Final = "commodity_subgroup_name"
    CFTC_COMM_CODE: Final = "cftc_commodity_code"
    CFTC_MARKET_CODE: Final = "cftc_market_code"
    CFTC_REGION_CODE: Final = "cftc_region_code"
    
    OI: Final = "open_interest_all"
    OI_OLD: Final = "open_interest_old"
    OI_OTHER: Final = "open_interest_other"
    
    CONTRACT_UNITS: Final = "contract_units"
    FUTONLY_OR_COMBINED: Final = "futonly_or_combined"
    ID: Final = "id"
    
    TOT_REPT_LONG: Final = "tot_rept_positions_long_all"
    TOT_REPT_SHORT: Final = "tot_rept_positions_short"  # No _all
    
    NONREPT_LONG: Final = "nonrept_positions_long_all"
    NONREPT_SHORT: Final = "nonrept_positions_short_all"
    
    CHANGE_OI: Final = "change_in_open_interest_all"
    CHANGE_TOT_REPT_LONG: Final = "change_in_tot_rept_long_all"
    CHANGE_TOT_REPT_SHORT: Final = "change_in_tot_rept_short"
    CHANGE_NONREPT_LONG: Final = "change_in_nonrept_long_all"
    CHANGE_NONREPT_SHORT: Final = "change_in_nonrept_short_all"

class LegacyFields(BaseFields):
    NONCOMM_LONG: Final = "noncomm_positions_long_all"
    NONCOMM_SHORT: Final = "noncomm_positions_short_all"
    NONCOMM_SPREAD: Final = "noncomm_postions_spread_all"  # API TYPO
    
    COMM_LONG: Final = "comm_positions_long_all"
    COMM_SHORT: Final = "comm_positions_short_all"
    
    CHANGE_NONCOMM_LONG: Final = "change_in_noncomm_long_all"
    CHANGE_NONCOMM_SHORT: Final = "change_in_noncomm_short_all"
    CHANGE_NONCOMM_SPREAD: Final = "change_in_noncomm_spead_all"  # API TYPO
    
    CHANGE_COMM_LONG: Final = "change_in_comm_long_all"
    CHANGE_COMM_SHORT: Final = "change_in_comm_short_all"
    
    PCT_NONCOMM_LONG: Final = "pct_of_oi_noncomm_long_all"
    PCT_NONCOMM_SHORT: Final = "pct_of_oi_noncomm_short_all"
    PCT_NONCOMM_SPREAD: Final = "pct_of_oi_noncomm_spread"  # No _all
    
    PCT_COMM_LONG: Final = "pct_of_oi_comm_long_all"
    PCT_COMM_SHORT: Final = "pct_of_oi_comm_short_all"
    
    TRADERS_NONCOMM_LONG: Final = "traders_noncomm_long_all"
    TRADERS_NONCOMM_SHORT: Final = "traders_noncomm_short_all"
    TRADERS_NONCOMM_SPREAD: Final = "traders_noncomm_spread_all"
    
    TRADERS_COMM_LONG: Final = "traders_comm_long_all"
    TRADERS_COMM_SHORT: Final = "traders_comm_short_all"
    
    TRADERS_NONCOMM_SPREAD_OLD: Final = "traders_noncomm_spead_old"  # API TYPO

class DisaggregatedFields(BaseFields):
    PROD_MERC_LONG: Final = "prod_merc_positions_long"  # No _all
    PROD_MERC_SHORT: Final = "prod_merc_positions_short" # No _all
    
    SWAP_LONG: Final = "swap_positions_long_all"
    SWAP_SHORT: Final = "swap__positions_short_all"  # Double underscore
    SWAP_SPREAD: Final = "swap__positions_spread_all" # Double underscore
    
    M_MONEY_LONG: Final = "m_money_positions_long_all"
    M_MONEY_SHORT: Final = "m_money_positions_short_all"
    M_MONEY_SPREAD: Final = "m_money_positions_spread" # No _all
    
    OTHER_REPT_LONG: Final = "other_rept_positions_long" # No _all
    OTHER_REPT_SHORT: Final = "other_rept_positions_short" # No _all
    OTHER_REPT_SPREAD: Final = "other_rept_positions_spread" # No _all
    
    CFTC_SUBGROUP_CODE: Final = "cftc_subgroup_code"

class TFFFields(BaseFields):
    DEALER_LONG: Final = "dealer_positions_long_all"
    DEALER_SHORT: Final = "dealer_positions_short_all"
    DEALER_SPREAD: Final = "dealer_positions_spread_all"
    
    ASSET_MGR_LONG: Final = "asset_mgr_positions_long" # No _all
    ASSET_MGR_SHORT: Final = "asset_mgr_positions_short" # No _all
    ASSET_MGR_SPREAD: Final = "asset_mgr_positions_spread" # No _all
    
    LEV_MONEY_LONG: Final = "lev_money_positions_long" # No _all
    LEV_MONEY_SHORT: Final = "lev_money_positions_short" # No _all
    LEV_MONEY_SPREAD: Final = "lev_money_positions_spread" # No _all
    
    OTHER_REPT_LONG: Final = "other_rept_positions_long"
    OTHER_REPT_SHORT: Final = "other_rept_positions_short"
    OTHER_REPT_SPREAD: Final = "other_rept_positions_spread"
    
    CFTC_SUBGROUP_CODE: Final = "cftc_subgroup_code"
