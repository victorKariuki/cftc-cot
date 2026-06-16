from cftc_cot import COTClient, COTAnalysis

client = COTClient()

# Get 52 weeks of Crude Oil data
df = client.legacy().market("Crude Oil").last_n_weeks(52).execute()

# Compute net positions
analysis = COTAnalysis(df, classification="legacy")
df = analysis.net_positions()

print("Latest Crude Oil Net Positions:")
print(df[['report_date_as_yyyy_mm_dd', 'noncomm_net']].head())
