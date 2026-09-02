"""Build quarterly dataset from HCP GDP decomposition + annual features."""
import pandas as pd
import numpy as np
import requests
import os
import warnings
warnings.filterwarnings('ignore')

print("=== Building Quarterly Morocco Dataset ===")

# Parse quarterly GDP from HCP
hcp_dir = r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\hcp_raw"

# Read the GDP decomposition (CVS - chain linked volume)
fpath = os.path.join(hcp_dir, "13_Décomposition_du_PIB_(CVS)_aux_prix_de_l.xlsx")
df_sheet = pd.read_excel(fpath, sheet_name='Data', header=None)

# Extract header row (row 3) with quarter labels
header_row = df_sheet.iloc[3].values
quarters = []
for v in header_row[1:]:
    if pd.notna(v):
        s = str(v).strip()
        if 'T' in s:
            quarters.append(s)

print(f"Quarters found: {len(quarters)}")
print(f"Range: {quarters[0]} to {quarters[-1]}")

# Extract GDP components
gdp_components = {}
for idx in range(4, len(df_sheet)):
    row = df_sheet.iloc[idx]
    label = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
    if len(label) > 3:
        values = []
        for v in row.values[1:]:
            if pd.notna(v):
                try:
                    values.append(float(v))
                except:
                    values.append(np.nan)
            else:
                values.append(np.nan)
        if len(values) >= len(quarters):
            gdp_components[label] = values[:len(quarters)]
            print(f"  {label[:50]}: {sum(1 for v in values[:len(quarters)] if pd.notna(v))} values")

# Build quarterly DataFrame
df_q = pd.DataFrame({"quarter": quarters})

for label, values in gdp_components.items():
    clean_label = label.replace(" ", "_").replace("'", "").replace("é", "e").replace("è", "e")[:40]
    df_q[clean_label] = values

# Calculate quarterly GDP growth rate
pib_col = [c for c in df_q.columns if 'PIB' in c or 'pib' in c or 'Produit' in c]
if pib_col:
    df_q["gdp_growth_qoq"] = df_q[pib_col[0]].pct_change() * 100
    df_q["gdp_growth_yoy"] = df_q[pib_col[0]].pct_change(4) * 100
    print(f"\nGDP growth calculated from: {pib_col[0]}")

# Add annual World Bank indicators (broadcast to quarterly)
print("\n--- Adding World Bank Annual Data ---")
years = list(range(1999, 2027))
wb_data = {"year": years}

INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "wb_gdp_growth",
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
        wb_data[name] = [vals.get(y) for y in years]
    except:
        wb_data[name] = [np.nan] * len(years)

df_wb = pd.DataFrame(wb_data).ffill().bfill()

# Map annual to quarterly
def year_from_quarter(q):
    return int(q[:4])

def quarter_num(q):
    return int(q[-1])

df_q["year"] = df_q["quarter"].apply(year_from_quarter)
df_q["quarter_num"] = df_q["quarter"].apply(quarter_num)

for col in df_wb.columns:
    if col == "year":
        continue
    wb_dict = dict(zip(df_wb["year"], df_wb[col]))
    df_q[col] = df_q["year"].map(wb_dict)

# Add lag features on quarterly data
print("\n--- Feature Engineering ---")
quarterly_numeric = [c for c in df_q.columns if c not in ["quarter", "year", "quarter_num"] and df_q[c].dtype in ['float64', 'int64']]

for col in quarterly_numeric[:10]:  # Top 10 quarterly features
    df_q[f"{col}_lag1"] = df_q[col].shift(1)
    df_q[f"{col}_lag4"] = df_q[col].shift(4)
    df_q[f"{col}_roll4"] = df_q[col].rolling(4).mean()

df_q = df_q.ffill().bfill()

print(f"Final quarterly dataset: {df_q.shape}")
print(f"Columns: {len(df_q.columns)}")

# Save
df_q.to_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\morocco_quarterly_full.csv", index=False)
print(f"\nSaved: morocco_quarterly_full.csv ({df_q.shape[0]} rows, {df_q.shape[1]} columns)")
print(f"Quarters: {df_q['quarter'].iloc[0]} to {df_q['quarter'].iloc[-1]}")
print("DONE")
