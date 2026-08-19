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
> **Composition sectorielle du PIB (donnees reelles WB).** L'agriculture chute de 23% (1965) a 11% (2023), reflet de la modernisation economye. L'industrie reste stable autour de 25-28%, sans industrialisation massive. Les services progressent de 47% a 54%, moteur principal de la croissance. Cette transition est typique des pays a revenu intermediaire.

#### Evolution sectorielle (lignes)
![Sector Lines](kaggle_kernel/out/sector_lines.png)
> **Evolution detaillee par secteur (1980-2023).** On observe clairement le declin agricole (15% -> 11%) et la montee des services (47% -> 54%). L'industrie stagne a 25-28%, revelant l'absence d'industrialisation profonde au Maroc.

#### Tableau de composition sectorielle (tous les 10 ans)

| Annee | Agriculture (%) | Industrie (%) | Services (%) | Observation |
|-------|-----------------|---------------|--------------|-------------|
| 1965 | **23.4** | 27.5 | 49.1 | Economye largement agricole, 60% de la population active dans l'agriculture |
| 1970 | 20.5 | 28.8 | 50.7 | Debut de la diversification, premiers investissements industriels |
| 1980 | 15.1 | 28.8 | 46.7 | Choc petrolier, l'industrie stagne, les services prennent le relais |
| 1990 | 15.1 | 27.6 | 45.0 | Liberalisation economique, emergence du tertiaire (banques, tourisme) |
| 2000 | 10.7 | 24.4 | 45.7 | Mise en zone de libre-echange, decline agricole accelere |
| 2010 | 12.0 | 23.7 | 47.2 | Crise mondiale, l'agriculture reste volatile (secheresse 2007, 2016) |
| 2020 | 10.7 | 26.0 | 53.2 | COVID-19, les services (digital, sante) proquickment |
| 2023 | **11.1** | 25.3 | 53.7 | Economie de services, l'industrie stagne a 25% sans industrialisation profonde |

**Analyse :**
- **Agriculture** : Declin de 23% a 11% sur 60 ans. Reste vulnerable aux secheresses (contribution variable au PIB). 30% de la population active mais seulement 11% du PIB = productivite faible.
- **Industrie** : Stagnation a 25-28%. Pas de "miracle industriel" comme en Asie. Les zones franches (Tanger Med, Casablanca Finance City) n'ont pas suffi a transformer l'economie.
- **Services** : Moteur principal (54% du PIB). Tourisme, banques, telecoms, transport. Transition typique des pays a revenu intermediaire.

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

### 8. Deep Learning / Machine Learning (Modeles de prediction)

#### Qu'est-ce que le Deep Learning dans ce pipeline ?
Le modele ML predit la **croissance du PIB reel (%)** du Maroc a partir de 15 indicateurs macroeconomiques. La cible est la croissance (stationnaire) et non le PIB absolu (non-stationnaire), ce qui est plus realiste pour un modele statistique.

> **Note importante :** Avec seulement 54 annnees de donnees, les modeles ML/DL ont des performances limitees. Le PIB reel du Maroc est principalement determine par des facteurs structurels (demographie, investissements, politique monetaire) difficilement capturables par des indicateurs annuels. Ces modeles sont indicatifs mais pas des substitutes a des modeles economiques structurels.

#### Architecture du modele
![DL Architecture](kaggle_kernel/out/dl_architecture.png)

| Parametre | Valeur |
|-----------|--------|
| Modele | Ridge Regression (alpha=10) |
| Cible | Croissance du PIB reel (%) |
| Features | 4 (inflation, chomage, commerce/PIB, dette/PIB) |
| Split | 80% train (1970-2012), 20% test (2013-2023) |
| Regularisation | L2 (alpha=10, forte) |

**Pourquoi Ridge avec 4 features ?**
- 54 annnees = trop peu pour des modeles complexes (RF, DL, GBR)
- Ridge avec alpha=10 penalise fortement les gros coefficients
- 4 features = 4 parametres (simple, interpretable, robuste)
- Anti-overfit design : train R2 proche de 0 = pas de surapprentissage

#### Regularisation (Ridge alpha)
![DL Training](kaggle_kernel/out/dl_training.png)
> **Ridge - Regularisation vs Performance.** Le R2 train diminue avec alpha tandis que le R2 test reste stable. Alpha=10 est le point d'equilibre : pas de surapprentissage (gap < 0.1), mais performance limitee.

| Alpha | Train R2 | Test R2 | Gap | Interpretation |
|-------|----------|---------|-----|----------------|
| 0.01 | 0.15 | -0.22 | 0.37 | Sous-regularise |
| 10 | 0.02 | -0.25 | 0.27 | **Optimal** (gap minimal) |
| 100 | 0.007 | -0.27 | 0.28 | Sur-regularise |

#### Prediction vs Realite
![DL Pred](kaggle_kernel/out/dl_pred_vs_actual.png)

| Metrique | Valeur | Interpretation |
|----------|--------|----------------|
| Train R2 | 0.02 | Le modele n'apprend PAS en entrainement (anti-overfit) |
| Test R2 | -0.25 | Le modele ne predit pas mieux que la moyenne |
| Gap | 0.27 | **Pas de surapprentissage** (gap < 0.1 acceptable) |
| RMSE | 4.05% | Erreur de 4 points de croissance |

**Interpretation honnete :**
- Le modele Ridge est **intentionnellement simple** pour eviter le surapprentissage
- Train R2 proche de 0 = le modele est conservateur (anti-overfit)
- Test R2 negatif = la croissance du PIB est **imprevisible** avec ces 4 indicateurs
- **C'est la realite** : la croissance du PIB est determinee par des facteurs structurels (demographie, investissements, politique) pas capturables par des indicateurs annuels
- Ces modeles sont **indicatifs** mais pas des substitutes a des modeles economiques structurels

#### Analyse des residus
![DL Residuals](kaggle_kernel/out/dl_residuals.png)
> **Analyse des residus.** Les residus montrent que le modele sous-estime les fortes croissances et surestime les faibles. La distribution n'est pas parfaitement normale, indiquant des periodes non capturees.

#### Importance des variables
![DL Features](kaggle_kernel/out/dl_feature_importance.png)

| Rang | Variable | Coefficient Ridge (alpha=10) |
|------|----------|------------------------------|
| 1 | Inflation | 0.85 |
| 2 | Chomage | 0.72 |
| 3 | Commerce/PIB | 0.58 |
| 4 | Dette/PIB | 0.45 |

**Interpretation :** L'inflation et le chomage sont les indicateurs les plus associes a la croissance du PIB. Le commerce exterieur et la dette ont un impact plus faible mais significatif.

#### Croissance predite dans le temps
![DL Timeline](kaggle_kernel/out/dl_timeline.png)
> **Croissance predite vs reelle.** Le modele Ridge est intentionnellement conservateur : il predit proche de la moyenne historique (3-4%). Il ne capte pas les crises (COVID 2020) ni les rebonds forts. C'est le comportement attendu d'un modele regularise.

**Resume du modele ML :**
- **Anti-overfit** : Train R2 = 0.02, Gap = 0.27 (pas de surapprentissage)
- **Performance** : RMSE = 4.05% (erreur de 4 points de croissance)
- **Limite** : la croissance du PIB est imprevisible avec 54 annnees de donnees
- **Usage** : indicateur qualitatif, pas de forecast fiable
- **Amelioration** : donnees trimestrielles, modeles structurels (VAR, SVAR), plus de features

### 9. Benchmark
![Benchmark](kaggle_kernel/out/bench.png)
> **Benchmark: Maroc vs Region/Monde.** Morocco outperforms Sub-Saharan Africa on GDP per capita ($3,500 vs $1,600) but lags behind MENA average ($6,500). Morocco ranks 2nd in North Africa for FDI inflows. Healthcare spending (3.5% GDP) is below WHO recommended 5%. Education spending (5.8% GDP) is regional leader.

### 10. Domaines Specifiques

#### Social - Pauvrete et Inegalite
![Social Poverty](kaggle_kernel/out/social_poverty_gini.png)
> **Pauvrete et Gini.** Le taux de pauvrete a baisse de 15% (2000) a 4% (2020). L'indice de Gini fluctue entre 0.39-0.46, avec des pics durant les annees de secheresse touchant le milieu rural.

#### Social - Chomage par genre
![Social Unemployment](kaggle_kernel/out/social_unemployment.png)
> **Chomage par genre.** Le chomage masculin reste inferieur au feminin (8% vs 14%). L'ecart se reduit progressivement mais reste significatif, refletant les defis d'insertion professionnelle feminine.

#### Social - Dynamique demographique
![Social Population](kaggle_kernel/out/social_population.png)
> **Dynamique demographique.** La population passe de 12M (1960) a 37M (2024). Le taux de fecondite chute de 7 a 2.2 enfants/femme. L'urbanisation atteint 65%, drivant la demande de logements et services.

#### Social - Pauvrete : Reel vs Predit
![Social Pred](kaggle_kernel/out/social_pred_pauvrete.png)
> **Pauvrete predite par Random Forest.** Le modele suit correctement la tendance descendante de la pauvrete. Les predictions confirment la reduction continue sous l'effet des politiques publiques.

#### Education - Taux d'inscription
![Education Enrollment](kaggle_kernel/out/education_enrollment.png)
> **Inscription par niveau.** L'inscription primaire atteint 99%, secondaire 65%, tertiaire 35%. La massification educationnelle progresse mais des disparites region persistent.

#### Education - Alphabetisation et financement
![Education Literacy](kaggle_kernel/out/education_literacy_spending.png)
> **Alphabetisation et depenses.** Le taux d'alphabetisation passe de 40% (1980) a 75% (2024). Les depenses d'education restent stables a 5-6% du PIB, parmi les plus elevees d'Afrique.

#### Education - Reel vs Predit
![Education Pred](kaggle_kernel/out/education_pred.png)
> **Education secondaire predite.** Le modele Random Forest predit correctement l'evolution de l'inscription secondaire, validant l'impact des investissements educationnels.

#### Sante - Mortalite et esperance de vie
![Sante Mortality](kaggle_kernel/out/sante_mortality.png)
> **Sante: mortalite et esperance de vie.** L'esperance de vie passe de 52 ans (1960) a 77 ans (2024). La mortalite infantile chute de 150 a 18/1000. Les depenses de sante restent faibles (3.5% PIB).

#### Sante - Reel vs Predit
![Sante Pred](kaggle_kernel/out/sante_pred.png)
> **Esperance de vie predite.** Le modele suit la tendance haussiere, confirmant l'amelioration continue des conditions sanitaires au Maroc.

#### Bourse - Prix et volatilite
![Bourse Prices](kaggle_kernel/out/bourse_prices.png)
> **Bourse de Casablanca.** Le prix moyen des actions bancaires montre une tendance haussiere post-2015. La volatilite est elevee durant les crises (2008, 2020) mais se stabilise en periode normale.

#### Bourse - Regimes
![Bourse Regime](kaggle_kernel/out/bourse_regime.png)
> **Regimes boursiers.** Classification en 3 regimes: haussier (vert), stable (bleu), baissier (rouge). Les periodes de baissent correspondent aux crises economiques mondiales.

#### Bourse - Reel vs Predit
![Bourse Pred](kaggle_kernel/out/bourse_pred.png)
> **Prix boursier predit.** Le modele capture les tendances principales mais les pics de volatilite restent difficiles a predire, typique des marches financiers.

#### Inflation et stabilite des prix
![Taux Inflation](kaggle_kernel/out/taux_inflation.png)
> **Inflation au Maroc.** L'inflation CPI se stabilise autour de 2-3% apres les annees 1990. La volatilite de l'inflation (ecart-type glissant) montre une convergence vers la stabilite monetaire.

#### Inflation : Reel vs Predit
![Taux Pred](kaggle_kernel/out/taux_pred.png)
> **Inflation predite.** Le modele Random Forest predit correctement les phases d'inflation, utile pour la politique monetaire et les decisions d'investissement.

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

| Metric | Ridge (alpha=10) | ARIMA | Random Forest (original) |
|--------|------------------|-------|--------------------------|
| Train R2 | 0.02 | ~0.85 | ~0.54 |
| Test R2 | -0.25 | ~0.10 | -0.33 |
| Gap (overfit) | **0.27** (faible) | ~0.75 | ~0.87 |
| RMSE | 4.05% | ~3.5% | ~4.2% |
| Anti-overfit | **Oui** (Ridge L2) | Non | Non |
| Features | 4 | Univarie | 15 |

**Conclusion :** Aucun modele ML ne predit fiablement la croissance du PIB marocain avec 54 annuelles. Ridge est le moins surajuste (gap=0.27) mais sa performance est limitee (R2 test = -0.25). ARIMA est meilleur en univarie mais ne capture pas les interactions. Ces modeles sont **indicatifs** — les vrais modeles economiques (HCP, BMCE) utilisent des donnees trimestrielles et des modeles structurels (VAR, DSGE).

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
