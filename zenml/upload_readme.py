from huggingface_hub import upload_file

readme = b"""---
language:
  - en
license: cc0-1.0
tags:
  - morocco
  - economics
  - world-bank
  - hcp
  - imf
  - time-series
  - indicators
size_categories:
  - 10K<n<100K
---

# Morocco Economic V2 (HCP + WB + IMF)

Enhanced Morocco socio-economic dataset with 38 indicators from 3 official sources.

## Sources
- World Bank (WDI): 25 indicators (GDP, inflation, trade, FDI, remittances...)
- IMF WEO: GDP growth forecasts
- HCP (data.gov.ma): 49 official Moroccan datasets downloaded

## Indicators (38 columns)
- GDP: real growth, current USD, per capita
- Inflation: CPI index, CPI inflation
- Employment: unemployment, labor force participation
- Trade: exports, imports, trade balance
- Fiscal: government debt, expenditure, revenue
- Social: population, life expectancy, fertility, urbanization
- Energy: electricity consumption, renewable energy
- Finance: FDI, remittances, current account
- Digital: internet users
- Features: lag features, rolling averages, volatility

## Years: 1999-2026 (28 rows)

## Usage
```python
import pandas as pd
df = pd.read_csv("morocco_indicators_enhanced.csv")
```

## License: CC0-1.0
"""

upload_file(
    path_or_fileobj=readme,
    path_in_repo="README.md",
    repo_id="YsfMO98/morocco-economic-v2",
    repo_type="dataset",
)
print("Updated README.md with YAML metadata")
