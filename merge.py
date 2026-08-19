"""ETAPE 4 - MERGE / JOINTURES.
Produit les tables fusionnees (ETL) dans processed/ :
  1) mart_macro_wide.csv     : panel ANNUEL Maroc, 1 ligne/annee, colonnes = tous les codes (join sur year)
  2) mart_banks_macro.csv    : prix bancaires JOIN macro (curated) sur l'annee du cours
  3) benchmark_morocco.csv   : Maroc JOIN le panel MONDIAL (WB/HDI/IMF) -> valeur, moyenne monde, region, rang
"""
import os, re, sys
import pandas as pd
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import config as C

# ---- 1) PANEL MACRO LARGE (join sur year) ----
ind = pd.read_csv(os.path.join(C.STAGING, "indicators_long.csv"))
# garde uniquement Maroc (entity NaN pour WDI/WEO, 'Morocco' sinon)
ind = ind[ind["entity"].isna() | (ind["entity"] == "Morocco")]
ind["value"] = pd.to_numeric(ind["value"], errors="coerce")
wide = ind.pivot_table(index="year", columns="code", values="value", aggfunc="first")
wide = wide.sort_index()
wide.index.name = "year"
wide.to_csv(os.path.join(C.PROCESSED, "mart_macro_wide.csv"), encoding="utf-8")
print(f"[MERGE] mart_macro_wide : {wide.shape[0]} annees x {wide.shape[1]} indicateurs")

# ---- 2) BANQUES JOIN MACRO (curated) ----
CURATED = [
    "NGDPD","NGDP_RPCH","PCPIPCH","GGXWDG_NGDP","BCA_NGDPD","LUR",          # IMF WEO
    "NY.GDP.MKTP.CD","NY.GDP.MKTP.KD.ZG","FP.CPI.TOTL.ZG","SL.UEM.TOTL.ZS", # WB WDI
    "GC.DOD.TOTL.GD.ZS","NE.EXP.GNFS.CD","NE.IMP.GNFS.CD","SP.POP.TOTL",
    "hdi","gdi_group_2021","eys_2021","le_2021","gni_pc_2021",              # HDI (colonnes annee figees)
]
cura = [c for c in CURATED if c in wide.columns]
banks = pd.read_csv(os.path.join(C.STAGING, "bank_prices.csv"), parse_dates=["trade_date"])
banks["year"] = banks["trade_date"].dt.year
macro_sub = wide[cura].reset_index()
banks_macro = banks.merge(macro_sub, on="year", how="left")
banks_macro.to_csv(os.path.join(C.PROCESSED, "mart_banks_macro.csv"), index=False, encoding="utf-8")
print(f"[MERGE] mart_banks_macro : {banks_macro.shape[0]} lignes x {banks_macro.shape[1]} colonnes (curated={len(cura)})")

# ---- 3) BENCHMARK MAROC vs MONDE ----
def load_world_wb():
    df = pd.read_csv(os.path.join(C.RAW, "kaggle_wdi_country_year_panel.csv"))
    return df
def load_world_hdi():
    df = pd.read_csv(os.path.join(C.RAW, "kaggle_HDI.csv"))
    return df
def load_world_imf():
    df = pd.read_csv(os.path.join(C.RAW, "kaggle_imf_weo_april_2026.csv"))
    return df

def safe_rank(sub_col, ma_val):
    if pd.isna(ma_val):
        return None
    return int((sub_col > ma_val).sum() + 1)

rows = []
# --- WB panel benchmark ---
wb = load_world_wb()
wb_ma = wb[wb["country"] == "Morocco"]
for col in ["gdp_growth_pct","inflation_cpi_pct","gov_debt_pct_gdp","unemployment_pct",
            "gdp_per_capita_usd","fdi_inflows_pct_gdp","trade_pct_gdp","gini_index"]:
    if col not in wb.columns: continue
    ma_series = wb_ma[["year", col]].dropna(subset=[col])
    if ma_series.empty:
        continue
    yr = int(ma_series["year"].max())
    ma_val = float(ma_series.loc[ma_series["year"] == yr, col].iloc[0])
    sub = wb[(wb["year"] == yr) & wb[col].notna()]
    world_avg = sub[col].mean()
    region = wb_ma["region"].iloc[0] if "region" in wb_ma else None
    reg_avg = wb[(wb["year"] == yr) & (wb["region"] == region) & wb[col].notna()][col].mean() if region else np.nan
    rows.append({"source":"WorldBank","indicator":col,"year":yr,"morocco":ma_val,
                 "world_avg":world_avg,"region":region,"region_avg":reg_avg,
                 "rank_out_of":int(sub[col].notna().sum()),"morocco_rank":safe_rank(sub[col], ma_val)})

# --- HDI benchmark ---
hdi = load_world_hdi()
hdi_ma = hdi[hdi["country"] == "Morocco"]
hdi_col = "hdi_2021"
if hdi_col in hdi.columns:
    ma_series = hdi_ma[[hdi_col]].dropna()
    if not ma_series.empty:
        yr = 2021
        ma_val = float(hdi_ma[hdi_col].iloc[0])
        sub = hdi[hdi[hdi_col].notna()]
        world_avg = sub[hdi_col].mean()
        region = hdi_ma["region"].iloc[0]
        reg_avg = hdi[(hdi["region"] == region) & hdi[hdi_col].notna()][hdi_col].mean()
        rank = safe_rank(sub[hdi_col], ma_val)
        rows.append({"source":"UNDP","indicator":hdi_col,"year":yr,"morocco":ma_val,
                     "world_avg":world_avg,"region":region,"region_avg":reg_avg,
                     "rank_out_of":int(sub[hdi_col].notna().sum()),"morocco_rank":rank})

# --- IMF WEO benchmark ---
imf = load_world_imf()
imf_ma = imf[imf["country_name"] == "Morocco"]
for col in ["Real_GDP_Growth_Pct","Inflation_CPI_Pct","Govt_Gross_Debt_Pct_GDP","Unemployment_Rate_Pct","GDP_Per_Capita_USD"]:
    if col not in imf.columns: continue
    ma_series = imf_ma[["year", col]].dropna(subset=[col])
    if ma_series.empty:
        continue
    yr = int(ma_series["year"].max())
    ma_val = float(ma_series.loc[ma_series["year"] == yr, col].iloc[0])
    sub = imf[(imf["year"] == yr) & imf[col].notna()]
    world_avg = sub[col].mean()
    rank = safe_rank(sub[col], ma_val)
    rows.append({"source":"IMF","indicator":col,"year":yr,"morocco":ma_val,
                 "world_avg":world_avg,"region":None,"region_avg":np.nan,
                 "rank_out_of":int(sub[col].notna().sum()),"morocco_rank":rank})

bench = pd.DataFrame(rows)
bench.to_csv(os.path.join(C.PROCESSED, "benchmark_morocco.csv"), index=False, encoding="utf-8")
print(f"[MERGE] benchmark_morocco : {len(bench)} indicateurs (Maroc vs monde/region + rang)")
