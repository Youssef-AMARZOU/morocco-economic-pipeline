"""Configuration et registre des sources CSV.
Chaque source pointe vers un fichier CSV deja present sur le disque
(dossier Morocco_Official_Data). L'etape EXTRACT copie ces fichiers
dans raw/ pour figer la zone source (immutable).
"""
import os

SRC_ROOT = r"C:\Users\youss\OneDrive\Desktop\Morocco_Official_Data"

# (nom_logique, chemin_source, type)
SOURCES = [
    ("wb_wdi",          os.path.join(SRC_ROOT, "morocco_worldbank_wdi.csv"),                 "indicators_long"),
    ("imf_weo",         os.path.join(SRC_ROOT, "morocco_imf_weo.csv"),                       "indicators_long"),
    ("imf_weo_2026",    os.path.join(SRC_ROOT, "morocco_imf_weo_april2026.csv"),             "wide_year"),
    ("wb_panel",        os.path.join(SRC_ROOT, "morocco_wb_panel.csv"),                      "wide_year"),
    ("hdi",             os.path.join(SRC_ROOT, "morocco_hdi.csv"),                           "wide_year_hdi"),
    ("banks_prices",    os.path.join(SRC_ROOT, "morocco_banks_stock_prices_long.csv"),       "bank_prices"),
]

# Fichiers bruts d'origine Kaggle (copie tel quel dans raw/ pour traçabilité)
RAW_KAGGLE = [
    r"C:\Users\youss\OneDrive\Desktop\Morocco_Official_Data\kaggle_datasets\imf-world-economic-outlook-april-2026\imf_weo_april_2026.csv",
    r"C:\Users\youss\OneDrive\Desktop\Morocco_Official_Data\kaggle_datasets\moroccan-banks-historical-stock-price",
    r"C:\Users\youss\OneDrive\Desktop\Morocco_Official_Data\kaggle_datasets\world-bank-development-indicators-panel\wdi_country_year_panel.csv",
    r"C:\Users\youss\OneDrive\Desktop\Morocco_Official_Data\kaggle_datasets\world-economic-trends-and-indicators\HDI.csv",
]

PROJECT = r"C:\Users\youss\OneDrive\Desktop\Morocco_ETL"
RAW = os.path.join(PROJECT, "raw")
STAGING = os.path.join(PROJECT, "staging")
PROCESSED = os.path.join(PROJECT, "processed")
WAREHOUSE = os.path.join(PROJECT, "warehouse.db")
