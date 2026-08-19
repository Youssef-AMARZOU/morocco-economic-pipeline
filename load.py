"""ETAPE 3 - LOAD.
Deux modes (flag --mode) :

  etl  : charge les fichiers STAGING (deja transformes) vers processed/ (CSV propres)
  elt  : charge les RAW dans un entrepot SQLite (warehouse.db) puis TRANSFORME
         via SQL (vues) -> c'est l'ELT. Les vues d'agregation = le 2e Transform (ETLT).

Usage : python load.py --mode both   (defaut)
        python load.py --mode etl
        python load.py --mode elt
"""
import os, sqlite3, sys, argparse, shutil
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
import config as C

def melt_view_sql(table, id_cols, value_cols, src, dataset, entity_col):
    parts = []
    for vc in value_cols:
        parts.append(
            f"SELECT '{src}' AS source, '{dataset}' AS dataset, "
            f"'{vc}' AS code, '{vc}' AS name, {entity_col} AS entity, "
            f"CAST(year AS INTEGER) AS year, CAST({vc} AS REAL) AS value "
            f"FROM {table} WHERE {vc} IS NOT NULL"
        )
    return " UNION ALL ".join(parts)

def melt_hdi_sql(table, id_cols, year_cols, src, dataset):
    parts = []
    for col, yr in year_cols.items():
        parts.append(
            f"SELECT '{src}' AS source, '{dataset}' AS dataset, "
            f"'{col.replace('_'+str(yr),'')}' AS code, '{col.replace('_'+str(yr),'')}' AS name, "
            f"country AS entity, {yr} AS year, CAST({col} AS REAL) AS value "
            f"FROM {table} WHERE {col} IS NOT NULL"
        )
    return " UNION ALL ".join(parts)

def run_etl():
    shutil.copy2(os.path.join(C.STAGING, "indicators_long.csv"), os.path.join(C.PROCESSED, "indicators_long.csv"))
    shutil.copy2(os.path.join(C.STAGING, "dim_indicators.csv"), os.path.join(C.PROCESSED, "dim_indicators.csv"))
    shutil.copy2(os.path.join(C.STAGING, "bank_prices.csv"), os.path.join(C.PROCESSED, "bank_prices.csv"))
    print(f"[LOAD/ETL] CSV propres ecrits dans processed/ : "
          f"indicators_long, dim_indicators, bank_prices")

def run_elt():
    if os.path.exists(C.WAREHOUSE):
        os.remove(C.WAREHOUSE)
    con = sqlite3.connect(C.WAREHOUSE)
    cur = con.cursor()

    # LOAD RAW (figure immutable) -> tables crues
    raw_map = {
        "raw_wb_wdi": os.path.join(C.RAW, "wb_wdi.csv"),
        "raw_imf_weo": os.path.join(C.RAW, "imf_weo.csv"),
        "raw_imf_weo_2026": os.path.join(C.RAW, "imf_weo_2026.csv"),
        "raw_wb_panel": os.path.join(C.RAW, "wb_panel.csv"),
        "raw_hdi": os.path.join(C.RAW, "hdi.csv"),
        "raw_banks_prices": os.path.join(C.RAW, "banks_prices.csv"),
        "raw_owid": os.path.join(C.RAW, "owid.csv"),
    }
    for t, p in raw_map.items():
        df = pd.read_csv(p)
        df.to_sql(t, con, if_exists="replace", index=False)
    print(f"[LOAD/ELT] {len(raw_map)} tables crues chargees dans warehouse.db")

    # TRANSFORM (dans l'entrepot, en SQL) -> on materialise le mart pour
    # contourner la limite SQLite des UNION composes (>500 termes sur le HDI).
    cur.execute("""
    CREATE TABLE indicators_long (
        source TEXT, dataset TEXT, code TEXT, name TEXT,
        entity TEXT, year INTEGER, value REAL
    );
    """)

    # Sources deja longues (2 termes : OK)
    cur.execute("""
    INSERT INTO indicators_long
        SELECT 'WorldBank' AS source,'WDI' AS dataset, indicator_code AS code, indicator_name AS name,
               NULL AS entity, CAST(year AS INTEGER) AS year, CAST(value AS REAL) AS value FROM raw_wb_wdi WHERE value IS NOT NULL
        UNION ALL
        SELECT 'IMF' AS source,'WEO' AS dataset, indicator_code AS code, indicator_name AS name,
               NULL AS entity, CAST(year AS INTEGER) AS year, CAST(value AS REAL) AS value FROM raw_imf_weo WHERE value IS NOT NULL;
    """)

    # Wide -> long, un INSERT par colonne (evite la limite de UNION composes)
    def cols_of(t):
        return [r[1] for r in cur.execute(f"PRAGMA table_info({t})").fetchall()]

    id_2026 = {"iso_code","country_name","year","is_forecast","data_vintage","scrape_date","is_aggregate_region"}
    for vc in [c for c in cols_of("raw_imf_weo_2026") if c not in id_2026]:
        cur.execute(f"""INSERT INTO indicators_long
            SELECT 'IMF','WEO2026','{vc}','{vc}',country_name,CAST(year AS INTEGER),CAST({vc} AS REAL)
            FROM raw_imf_weo_2026 WHERE {vc} IS NOT NULL;""")

    id_panel = {"country_id","country","iso2","region","income_level","year"}
    for vc in [c for c in cols_of("raw_wb_panel") if c not in id_panel]:
        cur.execute(f"""INSERT INTO indicators_long
            SELECT 'WorldBank','WDI_Panel','{vc}','{vc}',country,CAST(year AS INTEGER),CAST({vc} AS REAL)
            FROM raw_wb_panel WHERE {vc} IS NOT NULL;""")

    hdi_cols = cols_of("raw_hdi")
    year_cols = {c: int(c.split("_")[-1]) for c in hdi_cols if c not in {"iso3","country","hdicode","region"} and c[-4:].isdigit()}
    for col, yr in year_cols.items():
        base = col.replace("_"+str(yr), "")
        cur.execute(f"""INSERT INTO indicators_long
            SELECT 'UNDP','HDI','{base}','{base}',country,{yr},CAST({col} AS REAL)
            FROM raw_hdi WHERE {col} IS NOT NULL;""")

    # OWID (deja au format long canonique)
    if os.path.exists(os.path.join(C.RAW, "owid.csv")):
        cur.execute("""
        INSERT INTO indicators_long
            SELECT source, dataset, code, name, entity, CAST(year AS INTEGER), CAST(value AS REAL)
            FROM raw_owid WHERE value IS NOT NULL;
        """)

    # Vue par-dessus le mart materialise (nom stable pour les downstreans)
    cur.execute("CREATE VIEW v_indicators_long AS SELECT * FROM indicators_long;")

    # 2e TRANSFORM (ETLT) : vues d'agregation / mart analytique
    cur.execute("""
    CREATE VIEW v_economy_snapshot AS
    SELECT year,
       MAX(CASE WHEN code='NGDPD' THEN value END) AS pib_usd_m,
       MAX(CASE WHEN code='NGDP_RPCH' THEN value END) AS croissance_pib,
       MAX(CASE WHEN code='PCPIPCH' THEN value END) AS inflation,
       MAX(CASE WHEN code='GGXWDG_NGDP' THEN value END) AS dette_publique_pib,
       MAX(CASE WHEN code='BCA_NGDPD' THEN value END) AS balance_courante_pib,
       MAX(CASE WHEN code='LUR' THEN value END) AS chomage
    FROM v_indicators_long
    WHERE dataset IN ('WEO','WEO2026') AND source='IMF'
    GROUP BY year ORDER BY year;
    """)

    cur.execute("""
    CREATE VIEW v_bank_prices AS
    SELECT bank, date AS trade_date,
           CAST(Price AS REAL) AS price, CAST(Open AS REAL) AS open,
           CAST(High AS REAL) AS high, CAST(Low AS REAL) AS low,
           CAST(Volume AS REAL) AS volume, CAST(Change_pct AS REAL) AS change_pct
    FROM raw_banks_prices;
    """)

    cur.execute("""
    CREATE VIEW v_bank_annual AS
    SELECT bank, CAST(strftime('%Y', date) AS INTEGER) AS annee,
           COUNT(*) AS seances,
           AVG(Price) AS prix_moyen, MIN(Price) AS prix_min, MAX(Price) AS prix_max,
           (MAX(Price)-MIN(Price))/MIN(Price)*100.0 AS volatilite_pct
    FROM raw_banks_prices
    GROUP BY bank, annee ORDER BY bank, annee;
    """)

    con.commit()

    # Verification
    n = cur.execute("SELECT COUNT(*) FROM v_indicators_long").fetchone()[0]
    nb = cur.execute("SELECT COUNT(*) FROM v_bank_prices").fetchone()[0]
    print(f"[LOAD/ELT] v_indicators_long : {n:,} lignes | v_bank_prices : {nb:,} lignes")
    print(f"[LOAD/ELT] vues creees : v_indicators_long, v_economy_snapshot, v_bank_prices, v_bank_annual")
    con.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["etl","elt","both"], default="both")
    args = ap.parse_args()
    if args.mode in ("etl","both"): run_etl()
    if args.mode in ("elt","both"): run_elt()
    print("[LOAD] termine.")
