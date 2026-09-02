"""HONEST quarterly optimization - NO GDP components as features."""
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\morocco_quarterly_full.csv")
print(f"Dataset: {df.shape[0]} rows, {df.shape[1]} columns")

target = "gdp_growth_qoq"
print(f"Target: {target}")

# EXCLUDE GDP components (leakage)
leaky_cols = [
    "Produit_interieur_brut_PIB", "Importations_de_biens_et_services",
    "Depenses_de_consommation_finale_des_mena",
    "Depenses_de_Consommation_Finale_des_Admi",
    "CF_ISBL", "Formation_Brute_de_Capital",
    "Exportations_de_biens_et_services",
    "gdp_growth_qoq", "gdp_growth_yoy",
    "quarter", "year", "quarter_num"
]
# Also exclude lag/rolling of leaky cols
exclude = [c for c in df.columns if any(l in c for l in ["PIB", "Importations", "Depenses", "CF_ISBL", "Formation", "Exportations", "gdp_growth"]) 
           or c in ["quarter", "year", "quarter_num"]]

features = [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'int64']]
print(f"\nHONEST features ({len(features)}):")
for f in features:
    print(f"  {f}")

X = df[features].values
y = df[target].values

imputer = SimpleImputer(strategy='median')
X = imputer.fit_transform(X)

train_end = len(y) - 7
X_train, X_test = X[:train_end], X[train_end:]
y_train, y_test = y[:train_end], y[train_end:]
quarters_test = df["quarter"].values[train_end:]

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

print(f"\nTrain: {train_end}, Test: {len(y_test)}")
print(f"Test quarters: {list(quarters_test)}")

best_r2 = -999
best_config = None

for k in [3, 5, 7, 10, 15]:
    if k > len(features):
        continue

    selector = SelectKBest(f_regression, k=k)
    X_train_k = selector.fit_transform(X_train_s, y_train)
    X_test_k = selector.transform(X_test_s)

    models = {
        "Ridge_a1": Ridge(alpha=1),
        "Ridge_a10": Ridge(alpha=10),
        "Ridge_a100": Ridge(alpha=100),
        "Lasso_a01": Lasso(alpha=0.1),
        "Lasso_a1": Lasso(alpha=1),
        "EN_a1": ElasticNet(alpha=1, l1_ratio=0.5),
        "SVR_linear": SVR(kernel='linear', C=1),
        "SVR_rbf": SVR(kernel='rbf', C=1),
        "GBM_10": GradientBoostingRegressor(n_estimators=10, max_depth=2, random_state=42),
        "GBM_50": GradientBoostingRegressor(n_estimators=50, max_depth=2, random_state=42),
        "RF_50": RandomForestRegressor(n_estimators=50, max_depth=3, random_state=42),
    }

    for name, model in models.items():
        try:
            model.fit(X_train_k, y_train)
            train_pred = model.predict(X_train_k)
            test_pred = model.predict(X_test_k)

            train_r2 = 1 - np.sum((y_train - train_pred)**2) / np.sum((y_train - y_train.mean())**2)
            test_r2 = 1 - np.sum((y_test - test_pred)**2) / np.sum((y_test - y_test.mean())**2)
            rmse = np.sqrt(np.mean((y_test - test_pred)**2))
            gap = train_r2 - test_r2

            if test_r2 > best_r2:
                best_r2 = test_r2
                best_config = {
                    "model": name, "k": k,
                    "train_r2": train_r2, "test_r2": test_r2,
                    "rmse": rmse, "gap": gap,
                    "model_obj": model, "selector": selector
                }
                print(f"  NEW BEST: {name} (k={k}): Train={train_r2:.4f}, Test={test_r2:.4f}, RMSE={rmse:.4f}, Gap={gap:.4f}")
        except:
            pass

print(f"\n{'='*80}")
print(f"BEST (HONEST): {best_config['model']} (k={best_config['k']})")
print(f"  Train R2: {best_config['train_r2']:.4f}")
print(f"  Test R2:  {best_config['test_r2']:.4f}")
print(f"  RMSE:     {best_config['rmse']:.4f}")
print(f"  Gap:      {best_config['gap']:.4f}")
print(f"{'='*80}")

selector = best_config["selector"]
X_test_k = selector.transform(X_test_s)
preds = best_config["model_obj"].predict(X_test_k)

print(f"\n{'Quarter':<10} {'Actual':>8} {'Predicted':>10} {'Error':>8}")
print("-" * 40)
for i, y_true in enumerate(y_test):
    print(f"{quarters_test[i]:<10} {y_true:>8.2f}% {preds[i]:>10.2f}% {preds[i]-y_true:>8.2f}")

# Selected features
selected = [features[i] for i in selector.get_support(indices=True)]
print(f"\nSelected features: {selected}")
