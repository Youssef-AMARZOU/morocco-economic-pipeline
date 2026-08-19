"""PIPELINE SPARK (PySpark) - version distribuable du pipeline Morocco.
Lit les CSV bruts de raw/, normalise tout en format LONG tidy, puis
genere les tables analytiques (Parquet) + vues SQL Spark.

Sorties :
  spark_out/staging/   indicators_long, dim_indicators, bank_prices
  spark_out/processed/ idem (ETL)
  spark_out/clean/     indicators_clean, indicators_complete, data_quality_report, marts/
  spark_out/warehouse/ tables Parquet queryables (indicators_long, mart_macro_wide,
                          mart_banks_macro, benchmark_morocco, economy_snapshot, bank_prices)
"""
import os, sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

ETL = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ETL, "raw")
OUT = os.path.join(ETL, "spark_out")

def sspark():
    return (SparkSession.builder
            .master("local[2]")
            .appName("Morocco-ETL-Spark")
            .config("spark.sql.warehouse.dir", os.path.join(OUT, "warehouse"))
            .config("spark.driver.memory", "2g")
            .config("spark.sql.parquet.compression.codec", "uncompressed")
            .config("spark.hadoop.hadoop.home.dir", "C:\\hadoop")
            .getOrCreate())

def wide_to_long(df, id_cols, value_cols, src, dataset, name_is_code=True):
    """Empile (melt) les colonnes de valeur en (code, value) en gardant id_cols."""
    n = len(value_cols)
    stack_args = ", ".join([f"`{c}`, '{c}'" for c in value_cols])
    expr = f"stack({n}, {stack_args}) as (value, code)"
    sel = df.select(*id_cols, F.expr(expr))
    sel = sel.withColumn("source", F.lit(src)) \
             .withColumn("dataset", F.lit(dataset)) \
             .withColumn("name", F.when(F.lit(name_is_code), F.col("code")).otherwise(F.col("code")))
    return sel

def main():
    spark = sspark()
    spark.sparkContext.setLogLevel("WARN")
    os.makedirs(OUT, exist_ok=True)

    # ---------- 1) WB WDI (deja long) ----------
    wdi = (spark.read.option("header", True).csv(os.path.join(RAW, "wb_wdi.csv"))
           .withColumnRenamed("indicator_code", "code")
           .withColumnRenamed("indicator_name", "name")
           .withColumn("source", F.lit("WorldBank")).withColumn("dataset", F.lit("WDI"))
           .withColumn("value", F.col("value").cast(DoubleType()))
           .withColumn("year", F.col("year").cast("int"))
           .select("source", "dataset", "code", "name", F.lit(None).alias("entity"), "year", "value"))

    # ---------- 2) IMF WEO (deja long) ----------
    imf = (spark.read.option("header", True).csv(os.path.join(RAW, "imf_weo.csv"))
           .withColumnRenamed("indicator_code", "code")
           .withColumnRenamed("indicator_name", "name")
           .withColumn("source", F.lit("IMF")).withColumn("dataset", F.lit("WEO"))
           .withColumn("value", F.col("value").cast(DoubleType()))
           .withColumn("year", F.col("year").cast("int"))
           .select("source", "dataset", "code", "name", F.lit(None).alias("entity"), "year", "value"))

    # ---------- 3) IMF WEO 2026 (wide) ----------
    imf26 = spark.read.option("header", True).csv(os.path.join(RAW, "imf_weo_2026.csv"))
    id26 = ["country_name", "year"]
    vc26 = [c for c in imf26.columns if c not in
            {"iso_code","country_name","year","is_forecast","data_vintage","scrape_date","is_aggregate_region"}]
    imf26l = (wide_to_long(imf26, id26, vc26, "IMF", "WEO2026")
              .withColumnRenamed("country_name", "entity")
              .withColumn("value", F.col("value").cast(DoubleType()))
              .withColumn("year", F.col("year").cast("int"))
              .select("source","dataset","code","name","entity","year","value"))

    # ---------- 4) WB panel (wide) ----------
    panel = spark.read.option("header", True).csv(os.path.join(RAW, "wb_panel.csv"))
    idp = ["country", "year"]
    vcp = [c for c in panel.columns if c not in
           {"country_id","country","iso2","region","income_level","year"}]
    panell = (wide_to_long(panel, idp, vcp, "WorldBank", "WDI_Panel")
              .withColumnRenamed("country", "entity")
              .withColumn("value", F.col("value").cast(DoubleType()))
              .withColumn("year", F.col("year").cast("int"))
              .select("source","dataset","code","name","entity","year","value"))

    # ---------- 5) HDI (wide, colonnes suffixees _AAAA) ----------
    hdi = spark.read.option("header", True).csv(os.path.join(RAW, "hdi.csv"))
    idh = ["country"]
    vch = [c for c in hdi.columns if c not in {"iso3","country","hdicode","region"}]
    hdil = (wide_to_long(hdi, idh, vch, "UNDP", "HDI")
            .withColumnRenamed("country", "entity")
            .withColumn("year", F.regexp_extract("code", r"_(\d{4})$", 1).cast("int"))
            .withColumn("code", F.regexp_replace("code", r"_\d{4}$", ""))
            .withColumn("name", F.col("code"))
            .withColumn("value", F.col("value").cast(DoubleType()))
            .select("source","dataset","code","name","entity","year","value"))

    # ---------- 6) OWID (deja long) ----------
    owid = (spark.read.option("header", True).csv(os.path.join(RAW, "owid.csv"))
            .withColumn("entity", F.lit("Morocco"))
            .withColumn("value", F.col("value").cast(DoubleType()))
            .withColumn("year", F.col("year").cast("int"))
            .select("source","dataset","code","name","entity","year","value"))

    # ---------- Union indicateurs ----------
    ind = wdi.unionByName(imf).unionByName(imf26l).unionByName(panell) \
             .unionByName(hdil).unionByName(owid)
    ind = ind.filter(F.col("year").isNotNull())

    n_rows = ind.count()
    n_codes = ind.select("code").distinct().count()
    print(f"[SPARK] indicators_long : {n_rows:,} lignes, {n_codes} codes")

    # ---------- Dimension indicateurs ----------
    dim = (ind.groupBy("source","dataset","code","name")
              .agg(F.min("year").alias("years_min"), F.max("year").alias("years_max"),
                   F.count(F.when(F.col("value").isNotNull(), 1)).alias("n_obs"))
              .orderBy("source","dataset","code"))
    print(f"[SPARK] dim_indicators : {dim.count()} codes")

    # ---------- Banques ----------
    bp = spark.read.option("header", True).csv(os.path.join(RAW, "banks_prices.csv"))
    for c in ["Price","Open","High","Low","Volume","Change_pct"]:
        if c in bp.columns:
            bp = bp.withColumn(c, F.col(c).cast(DoubleType()))
    bp = (bp.withColumnRenamed("bank","entity").withColumnRenamed("date","trade_date")
             .withColumn("year", F.substring("trade_date",1,4).cast("int")))

    # ---------- Ecriture staging / processed ----------
    ind.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"staging","indicators_long"))
    dim.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"staging","dim_indicators"))
    bp.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"staging","bank_prices"))
    ind.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"processed","indicators_long"))
    dim.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"processed","dim_indicators"))
    bp.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"processed","bank_prices"))

    # ---------- CLEAN ----------
    ind_clean = ind.filter((F.col("year") >= 1900) & (F.col("year") <= 2100))
    n_invalid = n_rows - ind_clean.count()
    ind_complete = ind_clean.filter(F.col("value").isNotNull())
    missing = (ind_clean.groupBy("code","name")
               .agg(F.count(F.when(F.col("value").isNotNull(),1)).alias("n_nonnull"),
                    F.count("*").alias("n_total"))
               .withColumn("n_missing", F.col("n_total")-F.col("n_nonnull"))
               .orderBy(F.desc("n_missing")))
    dq = missing.withColumn("pct_missing", (F.col("n_missing")/F.col("n_total")*100).cast("double"))
    n_missing = ind_clean.count() - ind_complete.count()
    print(f"[SPARK] clean: {ind_clean.count():,} lignes (supprimees invalides: {n_invalid}) | manquantes: {n_missing}")
    ind_clean.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"clean","indicators_clean"))
    ind_complete.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"clean","indicators_complete"))
    dq.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"clean","data_quality_report"))

    # ---------- MERGE : mart_macro_wide (pivot code -> colonnes) ----------
    wide = (ind_clean.withColumn("code_l", F.lower(F.col("code")))
            .groupBy("year").pivot("code_l").agg(F.first("value"))
            .orderBy("year"))
    print(f"[SPARK] mart_macro_wide : {wide.count()} annees x {len(wide.columns)-1} indicateurs")
    wide.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"clean","marts","mart_macro_wide"))

    # ---------- MERGE : mart_banks_macro (banques x macro par annee) ----------
    macro_year = (ind_clean.filter(F.col("entity").isNull())
                  .withColumn("code_l", F.lower(F.col("code")))
                  .groupBy("year").pivot("code_l").agg(F.first("value")))
    banks_macro = bp.join(macro_year, on="year", how="left")
    print(f"[SPARK] mart_banks_macro : {banks_macro.count():,} lignes x {len(banks_macro.columns)} colonnes")
    banks_macro.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"clean","marts","mart_banks_macro"))

    # ---------- benchmark_morocco (14 curated) + economy_snapshot (SQL) ----------
    CURATED = ["ngdpd","ngdp_rpch","pcpipch","ggxwdg_ngdp","bca_ngdpd","lur",
               "sp.pop.totl","sp.dyn.le00.in","sl.uem.totl.zs","ne.exp.gnfs.cd",
               "ne.imp.gnfs.cd","fp.cpi.totl.zg","ny.gdp.mktp.kd.zg","se.adt.litr.zs"]
    bench = (ind_clean.filter(F.lower(F.col("code")).isin(CURATED))
             .withColumn("code_l", F.lower(F.col("code")))
             .groupBy("year").pivot("code_l").agg(F.first("value")).orderBy("year"))
    bench.coalesce(1).write.mode("overwrite").option("header",True).csv(os.path.join(OUT,"clean","marts","benchmark_morocco"))

    # ---------- WAREHOUSE : vues SQL Spark ----------
    ind.createOrReplaceTempView("indicators_long")
    bp.createOrReplaceTempView("bank_prices")
    snap = spark.sql("""
        SELECT year,
            MAX(CASE WHEN code='NGDPD' THEN value END) AS pib_usd_m,
            MAX(CASE WHEN code='NGDP_RPCH' THEN value END) AS croissance_pib,
            MAX(CASE WHEN code='PCPIPCH' THEN value END) AS inflation,
            MAX(CASE WHEN code='GGXWDG_NGDP' THEN value END) AS dette_publique_pib,
            MAX(CASE WHEN code='BCA_NGDPD' THEN value END) AS balance_courante_pib,
            MAX(CASE WHEN code='LUR' THEN value END) AS chomage
        FROM indicators_long
        WHERE dataset IN ('WEO','WEO2026') AND source='IMF'
        GROUP BY year ORDER BY year
    """)
    print("[SPARK] v_economy_snapshot (apercu):")
    snap.show(5, truncate=False)

    # ecriture warehouse (Parquet queryable)
    wh = os.path.join(OUT, "warehouse")
    ind.coalesce(1).write.mode("overwrite").parquet(os.path.join(wh,"indicators_long"))
    wide.coalesce(1).write.mode("overwrite").parquet(os.path.join(wh,"mart_macro_wide"))
    banks_macro.coalesce(1).write.mode("overwrite").parquet(os.path.join(wh,"mart_banks_macro"))
    bench.coalesce(1).write.mode("overwrite").parquet(os.path.join(wh,"benchmark_morocco"))
    snap.coalesce(1).write.mode("overwrite").parquet(os.path.join(wh,"economy_snapshot"))
    bp.coalesce(1).write.mode("overwrite").parquet(os.path.join(wh,"bank_prices"))
    print(f"[SPARK] warehouse Parquet ecrit dans {wh}")

    spark.stop()
    print("[SPARK] PIPELINE SPARK TERMINE")

if __name__ == "__main__":
    main()