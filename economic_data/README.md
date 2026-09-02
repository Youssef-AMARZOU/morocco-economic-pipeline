# Morocco Economic Analysis V2

![Linked with](https://img.shields.io/badge/linked_with-rasd-blue?logo=kaggle)

Real data for Morocco economic analysis (1999-2026).

## Linked Datasets

- **[economie-maroc-rasd](https://www.kaggle.com/datasets/amarzouyoussef/economie-maroc-rasd)** — Main dataset (22 CSVs)
- **[morocco-charts-v2](https://www.kaggle.com/datasets/amarzouyoussef/morocco-charts-v2)** — Charts & insights

## Contents

| File | Description |
|------|-------------|
| morocco_real_data.csv | 130 features, 28 years (HCP + World Bank) |
| morocco_indicators_enhanced.csv | 38 features (original enhanced dataset) |
| hcp_real/ | 63 HCP XLSX files (IPC, IPP, employment) |
| charts/ | 10 visualization charts (PNG) |

## Data Sources

- World Bank (WDI): 25 indicators
- IMF WEO: GDP forecasts
- HCP (data.gov.ma): 63 official files

## Key Results

- Best model: SVR_linear with R2=0.40
- RMSE: 3.44
- Features: 31 (honest, no data leakage)

## License

CC0-1.0
