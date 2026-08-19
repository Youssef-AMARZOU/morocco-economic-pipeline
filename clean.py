"""ETAPE 5 - CLEANING & ORGANIZING.
Nettoie le jeu de donnees canonique (indicators_long) et organise les sorties :
  - clean/indicators_clean.csv     : donnees nettoyees + flags qualite (is_missing, dup)
  - clean/indicators_complete.csv : uniquement les valeurs non-nulles (table analytique propre)
  - clean/data_quality_report.csv : completude/annees/doublons par (source,dataset,code)
  - clean/marts/                  : les tables fusionnees deja produites, reorganisees
Operations de nettoyage :
  types (year int, value float), trim des codes, annees valides 1900-2100,
  deduplication (source,dataset,code,entity,year), suppression doublons.
"""
import os, sys, shutil
import pandas as pd
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import config as C

CLEAN = os.path.join(C.PROJECT, "clean")
os.makedirs(CLEAN, exist_ok=True)
os.makedirs(os.path.join(CLEAN, "marts"), exist_ok=True)

# --- Lecture source (staging = deja transforme) ---
df = pd.read_csv(os.path.join(C.STAGING, "indicators_long.csv"), dtype=str)
n0 = len(df)

# Standardisation types
df["code"] = df["code"].astype(str).str.strip()
df["name"] = df["name"].astype(str).str.strip()
df["source"] = df["source"].astype(str).str.strip()
df["dataset"] = df["dataset"].astype(str).str.strip()
df["entity"] = df["entity"].replace({"nan": None, "None": None, "": None})
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

# Annees valides
df["year_valid"] = df["year"].between(1900, 2100)
bad_year = (~df["year_valid"]).sum()
df = df[df["year_valid"]].copy()
df["year"] = df["year"].astype("Int64")

# Doublons (source,dataset,code,entity,year)
dup_mask = df.duplicated(subset=["source","dataset","code","entity","year"], keep="first")
n_dup = int(dup_mask.sum())
df = df[~dup_mask].copy()

# Flags qualite
df["is_missing"] = df["value"].isna()
df["year"] = df["year"].astype(int)

df = df.sort_values(["source","dataset","code","entity","year"])
df.to_csv(os.path.join(CLEAN, "indicators_clean.csv"), index=False, encoding="utf-8")

# Table analytique complete (valeurs non-nulles)
comp = df[~df["is_missing"]].drop(columns=["is_missing","year_valid"]).copy()
comp.to_csv(os.path.join(CLEAN, "indicators_complete.csv"), index=False, encoding="utf-8")

# Rapport qualite par (source,dataset,code)
rep = (df.groupby(["source","dataset","code","name"])
         .agg(n_obs=("value","count"),
              n_missing=("is_missing","sum"),
              year_min=("year","min"),
              year_max=("year","max"))
         .reset_index())
rep["pct_complete"] = ((rep["n_obs"] - rep["n_missing"]) / rep["n_obs"] * 100).round(1)
rep = rep[["source","dataset","code","name","n_obs","n_missing","pct_complete","year_min","year_max"]]
rep = rep.sort_values(["source","dataset","code"])
rep.to_csv(os.path.join(CLEAN, "data_quality_report.csv"), index=False, encoding="utf-8")

# Reorganise les marts deja produits dans clean/marts/
for f in ["mart_macro_wide.csv","mart_banks_macro.csv","benchmark_morocco.csv"]:
    src = os.path.join(C.PROCESSED, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(CLEAN, "marts", f))

print(f"[CLEAN] lignes lues            : {n0}")
print(f"[CLEAN] annees invalides (>2100/<1900) supprimees : {bad_year}")
print(f"[CLEAN] doublons supprimes     : {n_dup}")
print(f"[CLEAN] lignes finales         : {len(df)}")
print(f"[CLEAN] valeurs manquantes     : {int(df['is_missing'].sum())}")
print(f"[CLEAN] -> clean/indicators_clean.csv ({len(df)} lignes)")
print(f"[CLEAN] -> clean/indicators_complete.csv ({len(comp)} lignes)")
print(f"[CLEAN] -> clean/data_quality_report.csv ({len(rep)} codes)")
print(f"[CLEAN] -> clean/marts/ (3 tables fusionnees)")
