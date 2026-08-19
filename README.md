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
- GDP decomposition and trend analysis.
- Sectoral breakdown (agriculture, industry, services).
- Correlation heatmap and Gini coefficient trends.

### 5. Statistical Models
- **OLS**: GDP growth ~ macroeconomic drivers.
- **Logit**: Probability of recession.
- **Pearson correlation**: Growth vs. inflation.
- **TCAM**: Compound annual growth rate of GDP.
- **Volatility analysis**: Bank stock return volatility.

### 6. Growth Scenarios
Monte Carlo simulation of GDP trajectories through 2039 under 3 scenarios (base, optimistic, pessimistic).

### 7. Machine Learning
- **Random Forest**: Non-linear GDP prediction (feature importance).
- **Lasso**: Regularized linear model with variable selection.
- **K-means**: 3 economic regimes identified.
- **PCA**: Dimensionality reduction on macro indicators.

### 8. Deep Learning
Keras feedforward neural network for GDP prediction (when GPU available).

### 9. Benchmark
Morocco vs. regional and global comparators (MENA, Sub-Saharan Africa, World averages).

### 10. Validation
Cross-validated model comparison (RMSE, R-squared) across all methods.

### 11. Export + HTML Report
Generates a self-contained HTML report with:
- YAML metadata header
- Table of contents
- Executive summary
- Full French-language narrative
- All charts embedded as base64

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

## Project Structure

```
morocco-economic-pipeline/
├── README.md                  # This file
├── kaggle_kernel/
│   ├── kernel-metadata.json   # Kaggle kernel config
│   ├── maroc_pipeline.R       # Full R analysis script (494 lines)
│   ├── maroc_pipeline.ipynb   # Notebook version (linked to GitHub)
│   └── rapport_economie_maroc.Rmd  # Standalone Rmd report
├── kaggle_model/
│   └── model-metadata.json    # Model parent metadata
├── fetch_wb.py                # World Bank data fetcher
├── fetch_owid.py              # Our World in Data fetcher
├── fetch_imf2.py              # IMF data fetcher
├── clean.py                   # Data cleaning
├── transform.py               # Data transformation
├── merge.py                   # Data merging
├── load.py                    # Data export
├── spark_etl.py               # Spark ETL (optional)
├── config.py                  # Configuration
├── run_all.py                 # Pipeline orchestrator
├── get_log.py                 # Kaggle log helper
├── publish_outputs.py         # Output publisher
└── .gitignore
```

---

## How to Run

### On Kaggle (recommended)
1. Go to [maroc-pipeline-r](https://www.kaggle.com/code/amarzouyoussef/maroc-pipeline-r)
2. Click **Run All** (or run cells sequentially)
3. Dataset is auto-detected from `/kaggle/input/economie-maroc-rasd/`

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

## Key Results

| Metric | Random Forest | Lasso | ARIMA | Deep Learning |
|--------|---------------|-------|-------|---------------|
| RMSE | ~0.02 | ~0.03 | ~0.04 | ~0.03 |
| R-squared | ~0.95 | ~0.90 | ~0.85 | ~0.92 |
| Use case | Best overall | Interpretability | Univariate forecast | Non-linear patterns |

---

## License

Apache 2.0
