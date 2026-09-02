"""Fetch ALL HCP XLSX datasets, parse quarterly data, create comprehensive features."""
import numpy as np
import pandas as pd
import requests
import os
import json
import warnings
warnings.filterwarnings('ignore')

print("=== Fetching ALL HCP Datasets (49 XLSX files) ===")

hcp_base = "https://data.gov.ma/data/fr/api/3/action/package_search"
params = {"fq": "organization:haut-commissariat-au-plan", "rows": 100}

resp = requests.get(hcp_base, params=params, timeout=30)
datasets = resp.json()["result"]["results"]
print(f"Found {len(datasets)} HCP datasets")

output_dir = "C:\\Users\\youss\\OneDrive\\Desktop\\morocco-economic-pipeline\\economic_data\\hcp_raw"
os.makedirs(output_dir, exist_ok=True)

# Download ALL XLSX files
downloaded = {}
for i, ds in enumerate(datasets):
    name = ds.get("title", f"dataset_{i}")
    resources = ds.get("resources", [])
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
                    downloaded[fname] = name
                    print(f"  [{len(downloaded)}] {name[:60]}")
                    break
            except Exception as e:
                pass

print(f"\nDownloaded {len(downloaded)} HCP XLSX files")

# Parse XLSX files to extract data
print("\n=== Parsing XLSX files ===")
all_series = {}

for fname, name in downloaded.items():
    try:
        fpath = os.path.join(output_dir, fname)
        # Try reading with different sheets
        xls = pd.ExcelFile(fpath)
        for sheet in xls.sheet_names:
            try:
                df_sheet = pd.read_excel(fpath, sheet_name=sheet, header=None)
                # Look for year columns (1999-2026)
                year_row = None
                for idx, row in df_sheet.iterrows():
                    vals = [str(v) for v in row.values if pd.notna(v)]
                    year_count = sum(1 for v in vals if v.strip().isdigit() and 1990 <= int(v.strip()) <= 2030)
                    if year_count >= 10:
                        year_row = idx
                        break

                if year_row is not None:
                    # Extract years and values
                    years_raw = df_sheet.iloc[year_row].values
                    years = []
                    for v in years_raw:
                        if pd.notna(v):
                            s = str(v).strip()
                            if s.isdigit() and 1990 <= int(s) <= 2030:
                                years.append(int(s))

                    if len(years) >= 10:
                        # Get label column (first column with text)
                        label_col = 0
                        for idx2, row in df_sheet.iterrows():
                            if idx2 != year_row and pd.notna(row.iloc[0]):
                                label = str(row.iloc[0]).strip()
                                if len(label) > 2 and not label.isdigit():
                                    # This row has data
                                    data_vals = []
                                    for v in row.values[1:]:
                                        if pd.notna(v):
                                            try:
                                                data_vals.append(float(v))
                                            except:
                                                data_vals.append(np.nan)
                                        else:
                                            data_vals.append(np.nan)

                                    if len(data_vals) >= len(years):
                                        key = f"{name[:30]}_{label[:30]}"
                                        # Create year-value pairs
                                        series = {}
                                        for yi, y in enumerate(years):
                                            if yi < len(data_vals):
                                                series[y] = data_vals[yi]
                                        if len(series) >= 10:
                                            all_series[key] = series
                                            print(f"  {key[:50]}: {len(series)} years")
                                            break
            except Exception as e:
                pass
    except Exception as e:
        pass

print(f"\nExtracted {len(all_series)} time series from HCP")

# Build comprehensive dataset
print("\n=== Building Comprehensive Dataset ===")
years = list(range(1999, 2027))
df = pd.DataFrame({"year": years})

for key, series in all_series.items():
    clean_key = key.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")[:50]
    df[clean_key] = [series.get(y, np.nan) for y in years]

# Add World Bank data
print("\n--- World Bank ---")
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "wb_gdp_growth",
    "NY.GDP.MKTP.CD": "wb_gdp_usd",
    "NY.GDP.PCAP.CD": "wb_gdp_pc",
    "FP.CPI.TOTL.ZG": "wb_cpi_inflation",
    "SL.UEM.TOTL.ZS": "wb_unemployment",
    "NE.EXP.GNFS.ZS": "wb_exports_pct",
    "NE.IMP.GNFS.ZS": "wb_imports_pct",
    "NE.RSB.GNFS.ZS": "wb_trade_balance",
    "BN.CAB.XOKA.GD.ZS": "wb_current_account",
    "GC.DOD.TOTL.GD.ZS": "wb_gov_debt",
    "GC.XPN.TOTL.GD.ZS": "wb_gov_spending",
    "GC.REV.XGRT.GD.ZS": "wb_gov_revenue",
    "SP.POP.TOTL": "wb_population",
    "SP.DYN.LE00.IN": "wb_life_expectancy",
    "SP.DYN.TFRT.IN": "wb_fertility",
    "SP.URB.TOTL.IN.ZS": "wb_urban_pct",
    "EG.USE.ELEC.KH.PC": "wb_electricity_pc",
    "EG.FEC.RNEW.ZS": "wb_renewable_pct",
    "SH.XPD.CHEX.GD.ZS": "wb_health_spend",
    "SE.XPD.TOTL.GD.ZS": "wb_education_spend",
    "BX.KLT.DINV.WD.GD.ZS": "wb_fdi_pct",
    "BX.TRF.PWKR.DT.GD.ZS": "wb_remittances_pct",
    "IT.NET.USER.ZS": "wb_internet_pct",
}

for code, name in INDICATORS.items():
    try:
        url = f"https://api.worldbank.org/v2/country/MAR/indicator/{code}"
        resp = requests.get(url, params={"format": "json", "per_page": 500, "date": "1999:2026"}, timeout=15)
        items = resp.json()[1]
        vals = {int(i["date"]): float(i["value"]) for i in items if i["value"]}
        df[name] = [vals.get(y) for y in years]
        n = sum(1 for v in df[name] if v is not None)
        print(f"  {name}: {n}")
    except:
        df[name] = np.nan

# Add IMF
print("\n--- IMF ---")
try:
    url = "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/MAR?periods=1999-2026"
    resp = requests.get(url, timeout=20)
    imf = resp.json()
    if "values" in imf and "NGDP_RPCH" in imf["values"]:
        vals = {int(k): float(v) for k, v in imf["values"]["NGDP_RPCH"].items()}
        df["imf_gdp_growth"] = [vals.get(y) for y in years]
        print(f"  imf_gdp_growth: {sum(1 for v in df['imf_gdp_growth'] if v is not None)}")
except:
    df["imf_gdp_growth"] = np.nan

# Feature engineering
print("\n=== Feature Engineering ===")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols.remove("year")

for col in numeric_cols:
    if df[col].notna().sum() > 10:
        df[f"{col}_lag1"] = df[col].shift(1)
        df[f"{col}_lag2"] = df[col].shift(2)
        df[f"{col}_roll3"] = df[col].rolling(3).mean()
        df[f"{col}_roll5"] = df[col].rolling(5).mean()
        df[f"{col}_vol3"] = df[col].rolling(3).std()

# Drop columns with too many NaN
nan_pct = df.isnull().mean()
df = df[nan_pct[nan_pct < 0.5].index]
df = df.ffill().bfill()

# Drop rows with all NaN in numeric
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
df = df.dropna(subset=numeric_cols, how='all')

print(f"Final shape: {df.shape}")
print(f"Columns: {len(df.columns)}")

# Save
df.to_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\morocco_comprehensive.csv", index=False)
print(f"\nSaved: morocco_comprehensive.csv ({df.shape[0]} rows, {df.shape[1]} columns)")
print("DONE")
