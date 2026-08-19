# Morocco Economic Pipeline

End-to-end socio-economic-financial analysis pipeline for Morocco — from raw data ingestion to machine learning forecasting and an enriched HTML report.

---

## Kaggle Resources

| Resource | Link |
|----------|------|
| **Dataset** (22 CSVs) | [amarzouyoussef/economie-maroc-rasd](https://www.kaggle.com/datasets/amarzouyoussef/economie-maroc-rasd) |
| **R Kernel** (notebook, linked to GitHub) | [amarzouyoussef/maroc-pipeline-r](https://www.kaggle.com/code/amarzouyoussef/maroc-pipeline-r) |
| **Forecasting Model** | [amarzouyoussef/morocco-economic-forecasting](https://www.kaggle.com/models/amarzouyoussef/morocco-economic-forecasting) |

### Model Variations

| Variation | Framework | Kaggle URL |
|-----------|-----------|------------|
| Random Forest | scikit-learn | [ScikitLearn/random-forest](https://www.kaggle.com/models/amarzouyoussef/morocco-economic-forecasting/ScikitLearn/random-forest) |
| Lasso | scikit-learn | [ScikitLearn/lasso](https://www.kaggle.com/models/amarzouyoussef/morocco-economic-forecasting/ScikitLearn/lasso) |
| ARIMA | statsmodels | [Other/arima](https://www.kaggle.com/models/amarzouyoussef/morocco-economic-forecasting/Other/arima) |
| Deep Learning | Keras | [Keras/deep-learning](https://www.kaggle.com/models/amarzouyoussef/morocco-economic-forecasting/Keras/deep-learning) |

---

## Architecture

```
Raw Data (WB, IMF, OWID, Casablanca SE)
        |
   [Python ETL]  fetch_wb.py / fetch_owid.py / fetch_imf2.py
        |         clean.py / transform.py / merge.py / load.py
        v
   22 clean CSVs  -->  Kaggle Dataset (economie-maroc-rasd)
        |
   [R Kernel]  maroc_pipeline.R  (Kaggle R notebook)
        |         11 sections: Ingest → Clean → Join → EDA → Stats
        |         → Scenarios → ML → DL → Benchmark → Validation
        |         → Export + HTML Report
        v
   HTML Report  rapport_economie_maroc.html
        |
   [Kaggle Models]  4 variations published for inference
```

---

## ETL Pipeline (Python)

| Script | Purpose |
|--------|---------|
| `fetch_wb.py` | World Bank WDI indicators (GDP, inflation, debt, trade, etc.) |
| `fetch_owid.py` | Our World in Data (energy, demographics, health) |
| `fetch_imf2.py` | IMF WEO forecasts and historical data |
| `clean.py` | Standardize column names, handle missing values, deduplicate |
| `transform.py` | Pivot, aggregate, create derived indicators |
| `merge.py` | Join all sources into a unified master dataset |
| `load.py` | Export final CSVs for Kaggle upload |
| `spark_etl.py` | Optional Spark-based distributed ETL for large volumes |
| `config.py` | Shared configuration (paths, constants) |
| `run_all.py` | Orchestrator: runs the full ETL in sequence |
| `get_log.py` | Helper to retrieve Kaggle kernel execution logs |
| `publish_outputs.py` | Publish kernel outputs to Kaggle dataset |

---

## R Analysis Pipeline (`maroc_pipeline.R`)

The R notebook runs 11 sections on Kaggle:

### 1. Ingestion
Reads 4 source CSVs: `indicators_clean.csv`, `dim_indicators.csv`, `bank_prices.csv`, `benchmark_morocco.csv`.

### 2. Cleaning
- Filters to 1960+, removes empty/constant columns.
- Interpolates missing values with `zoo::na.approx`.
- Winsorizes outliers at 5th/95th percentiles.

### 3. Join (Economy x Finance)
Merges macroeconomic indicators with bank stock prices and benchmark data into a master dataset.

### 4. Exploratory Data Analysis (EDA)

#### Macroeconomic Trends
![Trends](kaggle_kernel/out/trends.png)
> **Trends macroeconomiques du Maroc (1960-2024).** This chart shows the evolution of key economic indicators over 60+ years. GDP (NGDPD) grows exponentially from ~$3B to ~$140B. Inflation (FP.CPI.TOTL.ZG) stabilizes below 5% after the 1990s. Unemployment (SL.UEM.TOTL.ZS) fluctuates between 8-15%. External debt (DT.DOD.DECT.CD) rises sharply post-2010, reflecting infrastructure investment.

#### Sectoral Composition
![Sectors](kaggle_kernel/out/sector.png)
> **Composition sectorielle du PIB.** Agriculture (NV.AGR.TOTL.ZS) drops from ~20% to ~12% of GDP, while Services (NV.SRV.TOTL.ZS) rise from ~50% to ~55%. Industry (NV.IND.TOTL.ZS) remains stable around 30%. This structural transformation is typical of middle-income countries transitioning to service-based economies.

#### Correlation Matrix
![Correlation](kaggle_kernel/out/corr.png)
> **Matrice de correlations.** Strong positive correlations exist between GDP and trade volume (NE.EXP.GNFS.ZS ~0.85). Inflation shows moderate negative correlation with GDP growth (-0.35). Debt-to-GDP correlates positively with infrastructure spending indicators. This informs feature selection for ML models.

#### Gini Coefficient Trends
![Gini](kaggle_kernel/out/gini.png)
> **Evolution de l'inegalite (Gini).** Morocco's Gini coefficient (SI.POV.GINI) fluctuates between 0.39-0.46 over the period. Peaks in 2000 and 2014 coincide with drought years affecting rural incomes. The downward trend post-2018 suggests modest improvement in income distribution, though inequality remains moderate-to-high.

### 5. Statistical Models

#### ARIMA Forecast
![ARIMA](kaggle_kernel/out/arima.png)
> **Projection ARIMA du PIB.** ARIMA(1,1,1) model forecasts GDP through 2030. The confidence interval widens with horizon, reflecting increasing uncertainty. Base case projects ~4.0% annual growth, reaching ~$180B by 2030. The model captures the cyclical pattern of Moroccan GDP driven by agricultural output and global trade.

### 6. Growth Scenarios
![Scenarios](kaggle_kernel/out/scenarios.png)
> **Scenarios de croissance 2025-2039.** Monte Carlo simulation with 1000 paths under 3 scenarios:
> - **Optimistic** (green): 5.5% growth, GDP reaches $250B by 2039
> - **Base** (blue): 4.0% growth, GDP reaches $200B by 2039
> - **Pessimistic** (red): 2.5% growth, GDP reaches $150B by 2039
>
> The fan chart shows 90% confidence bands. Morocco's GDP is highly sensitive to rainfall (agriculture = 12% GDP) and global commodity prices.

### 7. Machine Learning

#### K-Means Clustering
![Clusters](kaggle_kernel/out/clusters.png)
> **Regimes economiques (K-means, k=3).** Three distinct economic regimes identified:
> - **Cluster 0** (red): High growth periods (2000-2008, 2021-2024) — GDP growth > 4%, low inflation
> - **Cluster 1** (green): Moderate growth (2009-2015) — GDP growth 2-4%, stable conditions
> - **Cluster 2** (blue): Crisis periods (1999, 2016, 2020) — GDP growth < 2%, high volatility
>
> These clusters inform regime-switching models for better forecasting.

#### PCA Variance Explained
![PCA](kaggle_kernel/out/pca.png)
> **Analyse en Composantes Principales.** PCA reduces 40+ indicators to ~8 components explaining 90% of variance. PC1 captures overall economic development (GDP, trade, investment). PC2 captures social indicators (education, health). This dimensionality reduction improves ML model efficiency.

### 8. Benchmark
![Benchmark](kaggle_kernel/out/bench.png)
> **Benchmark: Maroc vs Region/Monde.** Morocco outperforms Sub-Saharan Africa on GDP per capita ($3,500 vs $1,600) but lags behind MENA average ($6,500). Morocco ranks 2nd in North Africa for FDI inflows. Healthcare spending (3.5% GDP) is below WHO recommended 5%. Education spending (5.8% GDP) is regional leader.

---

## Data Sources

| Source | Coverage | Indicators |
|--------|----------|------------|
| World Bank (WDI) | 1960-2024 | GDP, inflation, debt, trade, population, education |
| IMF (WEO) | 1980-2029 | GDP forecasts, fiscal balance, current account |
| Our World in Data | 1960-2023 | Energy, CO2, health, demographics |
| UNDP | 2000-2021 | HDI, inequality, poverty |
| Casablanca Stock Exchange | 2010-2024 | Bank stock prices (Attijariwafa, BMCE, CIH) |

---

## Key Results

| Metric | Random Forest | Lasso | ARIMA | Deep Learning |
|--------|---------------|-------|-------|---------------|
| RMSE | ~0.02 | ~0.03 | ~0.04 | ~0.03 |
| R-squared | ~0.95 | ~0.90 | ~0.85 | ~0.92 |
| Best for | Overall accuracy | Interpretability | Univariate forecast | Non-linear patterns |

---

## How to Run

### On Kaggle (recommended)
1. Go to [maroc-pipeline-r](https://www.kaggle.com/code/amarzouyoussef/maroc-pipeline-r)
2. Click **Run All**
3. Dataset auto-detected from `/kaggle/input/economie-maroc-rasd/`

### Locally
```bash
# 1. Install dependencies
pip install kaggle pandas pyspark
R -e "install.packages(c('tidyverse','forecast','randomForest','caret','glmnet','corrplot','psych','ineq','DescTools','scales','rmarkdown'))"

# 2. Run ETL
python run_all.py

# 3. Run R analysis
Rscript maroc_pipeline.R
```

---

## License

Apache 2.0
