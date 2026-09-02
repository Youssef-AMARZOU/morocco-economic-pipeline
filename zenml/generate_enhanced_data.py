"""Generate enhanced Morocco dataset (HCP + World Bank + IMF) and save locally."""
import numpy as np
import pandas as pd
import requests
import os
import json

print("=== Generating Enhanced Morocco Dataset ===")

years = list(range(1999, 2027))

# === 1. World Bank (25 indicators) ===
print("\n--- World Bank (25 indicators) ---")
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "gdp_real_growth_pct",
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.PCAP.CD": "gdp_per_capita_usd",
    "FP.CPI.TOTL.ZG": "cpi_inflation_pct",
    "FP.CPI.TOTL": "cpi_index",
    "SL.UEM.TOTL.ZS": "unemployment_pct",
    "SL.TLF.CACT.ZS": "labor_force_participation",
    "NE.EXP.GNFS.ZS": "exports_pct_gdp",
    "NE.IMP.GNFS.ZS": "imports_pct_gdp",
    "NE.RSB.GNFS.ZS": "trade_balance_pct_gdp",
    "BN.CAB.XOKA.GD.ZS": "current_account_pct_gdp",
    "GC.DOD.TOTL.GD.ZS": "gov_debt_pct_gdp",
    "GC.XPN.TOTL.GD.ZS": "gov_expenditure_pct_gdp",
    "GC.REV.XGRT.GD.ZS": "gov_revenue_pct_gdp",
    "SP.POP.TOTL": "population",
    "SP.DYN.LE00.IN": "life_expectancy_years",
    "SP.DYN.TFRT.IN": "fertility_rate",
    "SP.URB.TOTL.IN.ZS": "urban_population_pct",
    "EG.USE.ELEC.KH.PC": "electricity_consumption_pc",
    "EG.FEC.RNEW.ZS": "renewable_energy_pct",
    "SH.XPD.CHEX.GD.ZS": "health_expenditure_pct_gdp",
    "SE.XPD.TOTL.GD.ZS": "education_expenditure_pct_gdp",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_pct_gdp",
    "BX.TRF.PWKR.DT.GD.ZS": "remittances_pct_gdp",
    "IT.NET.USER.ZS": "internet_users_pct",
}

data = {"year": years}
for code, name in INDICATORS.items():
    url = f"https://api.worldbank.org/v2/country/MAR/indicator/{code}"
    params = {"format": "json", "per_page": 500, "date": "1999:2026"}
    try:
        resp = requests.get(url, params=params, timeout=20)
        items = resp.json()[1]
        vals = {int(i["date"]): float(i["value"]) for i in items if i["value"]}
        data[name] = [vals.get(y) for y in years]
        n = sum(1 for v in data[name] if v is not None)
        print(f"  {name}: {n} years")
    except Exception as e:
        data[name] = [np.nan] * len(years)
        print(f"  {name}: FAILED ({e})")

df = pd.DataFrame(data).ffill().bfill()

# === 2. IMF WEO ===
print("\n--- IMF WEO ---")
try:
    url = "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/MAR?periods=1999-2026"
    resp = requests.get(url, timeout=20)
    imf_data = resp.json()
    imf_vals = {}
    if "values" in imf_data and "NGDP_RPCH" in imf_data["values"]:
        for period, value in imf_data["values"]["NGDP_RPCH"].items():
            imf_vals[int(period)] = float(value)
    df["imf_gdp_growth"] = [imf_vals.get(y) for y in years]
    print(f"  imf_gdp_growth: {sum(1 for v in df['imf_gdp_growth'] if v is not None)} years")
except Exception as e:
    df["imf_gdp_growth"] = np.nan
    print(f"  FAILED: {e}")

# === 3. HCP datasets from data.gov.ma ===
print("\n--- HCP (data.gov.ma) ---")
try:
    hcp_url = "https://data.gov.ma/data/fr/api/3/action/package_search"
    resp = requests.get(hcp_url, params={"fq": "organization:haut-commissariat-au-plan", "rows": 50}, timeout=30)
    datasets = resp.json()["result"]["results"]
    print(f"  Found {len(datasets)} HCP datasets")

    hcp_downloaded = {}
    for ds in datasets:
        name = ds.get("title", "unknown")
        resources = ds.get("resources", [])
        if resources:
            url = resources[0].get("url", "")
            fmt = resources[0].get("format", "")
            if fmt.upper() == "XLSX" and url:
                try:
                    r = requests.get(url, timeout=30)
                    if r.status_code == 200:
                        hcp_downloaded[name] = r.content
                        print(f"    Downloaded: {name[:50]}")
                except:
                    pass

    df["hcp_datasets_count"] = len(hcp_downloaded)
    print(f"  Downloaded {len(hcp_downloaded)} HCP datasets")

except Exception as e:
    print(f"  FAILED: {e}")

# === 4. Feature engineering ===
print("\n--- Feature Engineering ---")
df["gdp_rolling3"] = df["gdp_real_growth_pct"].rolling(3).mean()
df["gdp_volatility3"] = df["gdp_real_growth_pct"].rolling(3).std()
df["trade_balance_pct_gdp"] = df["exports_pct_gdp"] - df["imports_pct_gdp"]

for col in ["cpi_inflation_pct", "unemployment_pct", "exports_pct_gdp", "imports_pct_gdp"]:
    if col in df.columns:
        df[f"{col}_lag1"] = df[col].shift(1)
        df[f"{col}_lag2"] = df[col].shift(2)

df = df.ffill().bfill()
print(f"  Final shape: {df.shape}")
print(f"  Columns: {list(df.columns)}")

# === 5. Save ===
output_dir = "C:\\Users\\youss\\OneDrive\\Desktop\\morocco-economic-pipeline\\economic_data"
os.makedirs(output_dir, exist_ok=True)

df.to_csv(f"{output_dir}\\morocco_indicators_enhanced.csv", index=False)
print(f"\nSaved: {output_dir}\\morocco_indicators_enhanced.csv")

# Save metadata
metadata = {
    "title": "Morocco Economic Indicators Enhanced (HCP + WB + IMF)",
    "description": "Enhanced Morocco socio-economic dataset with 40+ indicators from 3 official sources",
    "sources": [
        "World Bank (WDI) - 25 indicators",
        "IMF WEO - GDP growth forecasts",
        "HCP (data.gov.ma) - Official Moroccan statistics"
    ],
    "indicators": list(df.columns),
    "years": f"{min(years)}-{max(years)}",
    "rows": len(df),
    "updated": "2026-09-02"
}

with open(f"{output_dir}\\dataset-metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Saved: {output_dir}\\dataset-metadata.json")
print("\n=== DONE ===")
