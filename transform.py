"""ETAPE 2 - TRANSFORM.
Normalise toutes les sources en un schema TIDY (long) canonique :
    source, dataset, code, name, year, value, unit
plus une table de faits separee pour les prix de bourse.
Sorties dans staging/ (zone d'integration, données nettoyées/typées).
"""
import os, re, sys, json
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
import config as C

rows = []          # indicateurs long
banks = []         # prix bancaires

# --- 1) WB WDI (deja long) ---
df = pd.read_csv(os.path.join(C.RAW, "wb_wdi.csv"))
df = df.rename(columns={"indicator_code": "code", "indicator_name": "name", "year": "year", "value": "value"})
df["source"], df["dataset"] = "WorldBank", "WDI"
rows.append(df[["source", "dataset", "code", "name", "year", "value"]])

# --- 2) IMF WEO (deja long) ---
df = pd.read_csv(os.path.join(C.RAW, "imf_weo.csv"))
df = df.rename(columns={"indicator_code": "code", "indicator_name": "name", "year": "year", "value": "value"})
df["source"], df["dataset"] = "IMF", "WEO"
rows.append(df[["source", "dataset", "code", "name", "year", "value"]])

# --- 3) IMF WEO 2026 (wide -> long) ---
df = pd.read_csv(os.path.join(C.RAW, "imf_weo_2026.csv"))
idvars = ["iso_code", "country_name", "year", "is_forecast"]
metrics = [c for c in df.columns if c not in idvars and c not in ("data_vintage", "scrape_date", "is_aggregate_region")]
m = df.melt(id_vars=["country_name", "year", "is_forecast"], value_vars=metrics,
            var_name="code", value_name="value")
m["source"], m["dataset"] = "IMF", "WEO2026"
m = m.rename(columns={"country_name": "entity"})
m["name"] = m["code"]
rows.append(m[["source", "dataset", "code", "name", "year", "value"]].assign(entity=m["entity"]))

# --- 4) WB panel (wide -> long) ---
df = pd.read_csv(os.path.join(C.RAW, "wb_panel.csv"))
idvars = ["country_id", "country", "iso2", "region", "income_level", "year"]
metrics = [c for c in df.columns if c not in idvars]
m = df.melt(id_vars=["country", "year"], value_vars=metrics, var_name="code", value_name="value")
m["source"], m["dataset"] = "WorldBank", "WDI_Panel"
m = m.rename(columns={"country": "entity"})
m["name"] = m["code"]
rows.append(m[["source", "dataset", "code", "name", "year", "value"]].assign(entity=m["entity"]))

# --- 5) HDI (wide -> long, colonnes suffixees _AAAA) ---
df = pd.read_csv(os.path.join(C.RAW, "hdi.csv"))
idvars = ["iso3", "country", "hdicode", "region"]
year_cols = {c: int(c.split("_")[-1]) for c in df.columns if re.search(r"_(\d{4})$", c)}
m = df.melt(id_vars=["country"], value_vars=list(year_cols.keys()), var_name="col", value_name="value")
m["year"] = m["col"].map(year_cols)
m["code"] = m["col"].str.replace(r"_\d{4}$", "", regex=True)
m["source"], m["dataset"] = "UNDP", "HDI"
m = m.rename(columns={"country": "entity"})
m["name"] = m["code"]
rows.append(m[["source", "dataset", "code", "name", "year", "value"]].assign(entity=m["entity"]))

# --- 7) OWID (deja long, source complementaire) ---
if os.path.exists(os.path.join(C.RAW, "owid.csv")):
    ow = pd.read_csv(os.path.join(C.RAW, "owid.csv"))
    ow["year"] = pd.to_numeric(ow["year"], errors="coerce")
    ow["value"] = pd.to_numeric(ow["value"], errors="coerce")
    rows.append(ow[["source", "dataset", "code", "name", "entity", "year", "value"]].dropna(subset=["year"]))

# --- Assemblage indicateurs long ---
ind = pd.concat(rows, ignore_index=True)
ind["year"] = pd.to_numeric(ind["year"], errors="coerce").astype("Int64")
ind["value"] = pd.to_numeric(ind["value"], errors="coerce")
ind = ind.dropna(subset=["year"]).sort_values(["source", "dataset", "code", "year"])
ind.to_csv(os.path.join(C.STAGING, "indicators_long.csv"), index=False, encoding="utf-8")

# Dimension indicateurs
dim = (ind.groupby(["source", "dataset", "code", "name"])
         .agg(years_min=("year", "min"), years_max=("year", "max"), n_obs=("value", "count"))
         .reset_index())
dim.to_csv(os.path.join(C.STAGING, "dim_indicators.csv"), index=False, encoding="utf-8")

# --- 6) Prix bancaires (deja tidy) ---
bp = pd.read_csv(os.path.join(C.RAW, "banks_prices.csv"))
for c in ["Price", "Open", "High", "Low", "Volume", "Change_pct"]:
    if c in bp.columns:
        bp[c] = pd.to_numeric(bp[c], errors="coerce")
bp = bp.rename(columns={"bank": "entity", "date": "trade_date"})
bp.to_csv(os.path.join(C.STAGING, "bank_prices.csv"), index=False, encoding="utf-8")

print(f"[TRANSFORM] indicators_long : {len(ind):,} lignes, {ind['code'].nunique()} codes")
print(f"            par source       : {ind.groupby(['source','dataset']).size().to_dict()}")
print(f"[TRANSFORM] dim_indicators  : {len(dim)} codes")
print(f"[TRANSFORM] bank_prices     : {len(bp):,} lignes ({bp['entity'].nunique()} banques)")
