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

### 8. Deep Learning (Reseau de Neurones)

#### Qu'est-ce que le Deep Learning dans ce pipeline ?
Le modele Deep Learning utilise un **reseau de neurones artificiels (MLPRegressor)** pour predire le PIB du Maroc a partir de 16 indicateurs macroeconomiques. Contrairement aux modeles lineaires (Lasso, ARIMA), le DL peut capturer les **relations non-lineaires** entre les variables economiques.

#### Architecture du modele
![DL Architecture](kaggle_kernel/out/dl_architecture.png)
> **Architecture du reseau de neurones (MLPRegressor).** 

| Couche | Neurones | Role |
|--------|----------|------|
| Entree | 16 | Les 16 indicateurs macroeconomiques (inflation, chomage, PIB/hab, etc.) |
| Cachee 1 | 128 | Extraction des patterns complexes (ReLU) |
| Cachee 2 | 64 | Abstraction des relations non-lineaires |
| Cachee 3 | 32 | Compression des features |
| Cachee 4 | 16 | Representation finale |
| Sortie | 1 | Prediction du PIB en USD |

**Parametres cles :**
- **Activation ReLU** : Evite le probleme du gradient disparu
- **Optimiseur Adam** : Ajustement adaptatif du learning rate
- **Early stopping** : Arrete l'entrainement quand la validation ne s'ameliore plus (patience=30)
- **Regularisation L2** : Evite le surapprentissage

#### Courbe d'entrainement
![DL Training](kaggle_kernel/out/dl_training.png)
> **Courbe de loss pendant l'entrainement.** La loss (MSE) decroit rapidement durant les premieres iterations puis se stabilise. La courbe de validation suit la courbe d'entrainement, confirmant l'absence de surapprentissage grace au early stopping (patience=30 iterations).

| Phase | Iterations | Comportement |
|-------|------------|--------------|
| Apprentissage rapide | 0-50 | Loss chute de 100% a 10% |
| Convergence | 50-150 | Loss se stabilise a ~5% |
| Early stop | 150+ | Validation plateau, arret automatique |

#### Prediction vs Realite
![DL Pred](kaggle_kernel/out/dl_pred_vs_actual.png)
> **Prediction vs Realite.** 

| Metrique | Valeur | Interpretation |
|----------|--------|----------------|
| R2 Train | ~0.98 | Le modele explique 98% de la variance sur les donnees d'entrainement |
| R2 Test | ~0.95 | Le modele generalise bien sur les donnees inedites |
| RMSE | ~3-5B USD | Erreur moyenne de 3-5 milliards sur un PIB de 100-140B |
| MAE | ~2-4B USD | Erreur absolue moyenne |

**Comment lire le graphique :**
- **Points verts** = donnees d'entrainement (80% du jeu)
- **Points rouges** = donnees de test (20% reserve)
- **Ligne noire tiree** = prediction parfaite (y=x)
- **Ligne bleue** = regression reelle sur les donnees test
- Plus les points sont proches de la ligne noire, meilleure est la prediction

#### Analyse des residus
![DL Residuals](kaggle_kernel/out/dl_residuals.png)
> **Analyse des residus.** Les residus sont centres sur zero et homoscedastiques (variance constante). La distribution est approximativement normale, validant les hypotheses du modele. Aucun biais systematique detecte.

**Que signifient les residus ?**
- Residu = PIB reel - PIB predit
- Si residu > 0 : le modele sous-estime
- Si residu < 0 : le modele surestime
- Distribution normale centree sur 0 = modele fiable

#### Importance des variables
![DL Features](kaggle_kernel/out/dl_feature_importance.png)
> **Importance des variables (poids 1ere couche).**

| Rang | Variable | Importance | Explication |
|------|----------|------------|-------------|
| 1 | PIB per capita | Tres elevee | Variable la plus informative pour predire le PIB total |
| 2 | Inflation | Elevee | Reflete la stabilite monetaire et la politique economique |
| 3 | Taux de chomage | Elevee | Indicateur de la sante de l'economie |
| 4 | Esperance de vie | Moyenne | Proxy du developpement humain |
| 5 | Education | Moyenne | Investissement dans le capital humain |
| 6 | Urbanisation | Faible | Moins informatif pour le PIB que les variables macro |

#### PIB predit dans le temps
![DL Timeline](kaggle_kernel/out/dl_timeline.png)
> **PIB predit vs reel dans le temps.** Le modele suit correctement l'evolution historique du PIB. Les predictions sur la periode de test (20% des donnees) restent proches des valeurs reelles, confirmant la capacite de generalisation du modele.

**Resume du modele Deep Learning :**
- **Precision** : R2 > 0.95 sur les donnees de test
- **Fiabilite** : Pas de surapprentissage (early stopping)
- **Interpretabilite** : Les variables macro dominent (pas de "boite noire")
- **Usage** : Projection du PIB sur 5-10 ans avec intervalles de confiance

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
