"""Fetch REAL HCP data - only external predictors, NOT GDP components."""
import pandas as pd
import numpy as np
import requests
import os
import warnings
warnings.filterwarnings('ignore')

print("=== Fetching REAL HCP Data (Non-GDP Components) ===")

hcp_base = "https://data.gov.ma/data/fr/api/3/action/package_search"
params = {"fq": "organization:haut-commissariat-au-plan", "rows": 100}

resp = requests.get(hcp_base, params=params, timeout=30)
datasets = resp.json()["result"]["results"]
print(f"Found {len(datasets)} HCP datasets")

output_dir = r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\hcp_real"
os.makedirs(output_dir, exist_ok=True)

# Download key XLSX files
real_data = {}
for i, ds in enumerate(datasets):
    name = ds.get("title", f"dataset_{i}")
    resources = ds.get("resources", [])

    # Only download non-GDP-component files
    skip_keywords = ['PIB', 'GDP', 'Produit interieur', 'Importations', 'Exportations',
                     'Depenses', 'Formation', 'CF ISBL', 'Variation de stocks']
    should_skip = any(kw.lower() in name.lower() for kw in skip_keywords)

    if not should_skip:
        for res in resources:
            url = res.get("url", "")
            fmt = res.get("format", "")
            if fmt.upper() == "XLSX" and url:
                try:
                    r = requests.get(url, timeout=30)
                    if r.status_code == 200 and len(r.content) > 1000:
                        fname = f"{i}_{name[:40].replace(' ', '_').replace('/', '_')}.xlsx"
                        with open(os.path.join(output_dir, fname), "wb") as f:
                            f.write(r.content)
                        real_data[fname] = name
                        print(f"  [{len(real_data)}] {name[:60]}")
                        break
                except Exception as e:
                    pass

print(f"\nDownloaded {len(real_data)} REAL HCP files (non-GDP)")

# Parse each file
print("\n=== Parsing Files ===")
parsed_data = {}

for fname, name in real_data.items():
    try:
        fpath = os.path.join(output_dir, fname)
        xls = pd.ExcelFile(fpath)

        for sheet in xls.sheet_names:
            if 'data' not in sheet.lower() and 'metadata' not in sheet.lower():
                continue
            try:
                df_sheet = pd.read_excel(fpath, sheet_name=sheet, header=None)

                # Find year row
                for idx, row in df_sheet.iterrows():
                    vals = [str(v) for v in row.values if pd.notna(v)]
                    year_count = sum(1 for v in vals if v.strip().isdigit() and 1990 <= int(v.strip()) <= 2030)
                    if year_count >= 10:
                        # Found year header
                        years_raw = df_sheet.iloc[idx].values
                        years = []
                        for v in years_raw:
                            if pd.notna(v):
                                s = str(v).strip()
                                if s.isdigit() and 1990 <= int(s) <= 2030:
                                    years.append(int(s))

                        # Get data rows
                        for data_idx in range(idx+1, min(idx+20, len(df_sheet))):
                            data_row = df_sheet.iloc[data_idx]
                            label = str(data_row.iloc[0]) if pd.notna(data_row.iloc[0]) else ""
                            if len(label) > 3 and not label.isdigit():
                                # Parse values
                                series = {}
                                for yi, y in enumerate(years):
                                    if yi < len(data_row) - 1:
                                        try:
                                            val = float(data_row.iloc[yi+1])
                                            series[y] = val
                                        except:
                                            pass
                                if len(series) >= 10:
                                    key = f"{name[:30]}_{label[:30]}"
                                    clean_key = key.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")[:50]
                                    parsed_data[clean_key] = series
                                    print(f"  {clean_key[:50]}: {len(series)} years")
                                    break
                        break
            except Exception as e:
                pass
    except Exception as e:
        pass

print(f"\nParsed {len(parsed_data)} time series from HCP")

# Build final dataset
print("\n=== Building Real Dataset ===")
years = list(range(1999, 2027))
df = pd.DataFrame({"year": years})

for key, series in parsed_data.items():
    df[key] = [series.get(y, np.nan) for y in years]

# Add World Bank
print("\n--- World Bank ---")
WB = {
    "NY.GDP.MKTP.KD.ZG": "gdp_growth",
    "NY.GDP.MKTP.CD": "gdp_usd",
    "NY.GDP.PCAP.CD": "gdp_pc",
    "FP.CPI.TOTL.ZG": "cpi_inflation",
    "FP.CPI.TOTL": "cpi_index",
    "SL.UEM.TOTL.ZS": "unemployment",
    "SL.TLF.CACT.ZS": "labor_force",
    "NE.EXP.GNFS.ZS": "exports_pct",
    "NE.IMP.GNFS.ZS": "imports_pct",
    "NE.RSB.GNFS.ZS": "trade_balance",
    "BN.CAB.XOKA.GD.ZS": "current_account",
    "GC.DOD.TOTL.GD.ZS": "gov_debt",
    "GC.XPN.TOTL.GD.ZS": "gov_spending",
    "GC.REV.XGRT.GD.ZS": "gov_revenue",
    "SP.POP.TOTL": "population",
    "SP.DYN.LE00.IN": "life_expectancy",
    "SP.DYN.TFRT.IN": "fertility",
    "SP.URB.TOTL.IN.ZS": "urban_pct",
    "EG.USE.ELEC.KH.PC": "electricity_pc",
    "EG.FEC.RNEW.ZS": "renewable_pct",
    "SH.XPD.CHEX.GD.ZS": "health_spend",
    "SE.XPD.TOTL.GD.ZS": "education_spend",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_pct",
    "BX.TRF.PWKR.DT.GD.ZS": "remittances_pct",
    "IT.NET.USER.ZS": "internet_pct",
}

for code, name in WB.items():
    try:
        url = f"https://api.worldbank.org/v2/country/MAR/indicator/{code}"
        resp = requests.get(url, params={"format": "json", "per_page": 500, "date": "1999:2026"}, timeout=15)
        items = resp.json()[1]
        vals = {int(i["date"]): float(i["value"]) for i in items if i["value"]}
        df[name] = [vals.get(y) for y in years]
    except:
        df[name] = np.nan

# Feature engineering
print("\n--- Feature Engineering ---")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols.remove("year")

for col in numeric_cols:
    if df[col].notna().sum() > 10:
        df[f"{col}_lag1"] = df[col].shift(1)
        df[f"{col}_lag2"] = df[col].shift(2)
        df[f"{col}_roll3"] = df[col].rolling(3).mean()

# Clean
df = df.ffill().bfill()
nan_pct = df.isnull().mean()
df = df[nan_pct[nan_pct < 0.5].index]

print(f"Final shape: {df.shape}")

# Save
df.to_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\morocco_real_data.csv", index=False)
print(f"\nSaved: morocco_real_data.csv ({df.shape[0]} rows, {df.shape[1]} columns)")
print("DONE")
