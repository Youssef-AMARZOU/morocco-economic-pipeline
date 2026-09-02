"""Enhanced optimization with cross-validation and advanced features."""
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.model_selection import TimeSeriesSplit
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\morocco_real_data.csv")
print(f"Dataset: {df.shape[0]} rows, {df.shape[1]} columns")

target = "gdp_growth"
exclude = ["year", target, "gdp_usd", "gdp_pc", "gdp_rolling3", "gdp_volatility3"]
hcp_gdp = [c for c in df.columns if any(x in c.lower() for x in ['pib', 'gdp', 'produit_interieur', 'importations', 'exportations', 'depenses', 'formation', 'cf_isbl', 'variation_de_stocks'])]
exclude.extend(hcp_gdp)

features = [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'int64']]
print(f"Features: {len(features)}")

X = df[features].values
y = df[target].values
years = df["year"].values

imputer = SimpleImputer(strategy='median')
X = imputer.fit_transform(X)

# Time series cross-validation
tscv = TimeSeriesSplit(n_splits=5)

best_r2 = -999
best_config = None

for k in [10, 15, 20, 25, 30, 40, 50]:
    if k > len(features):
        continue

    selector = SelectKBest(f_regression, k=k)
    X_selected = selector.fit_transform(X, y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_selected)

    models = {
        "Ridge_a10": Ridge(alpha=10),
        "Ridge_a50": Ridge(alpha=50),
        "Ridge_a100": Ridge(alpha=100),
        "Lasso_a01": Lasso(alpha=0.1),
        "Lasso_a1": Lasso(alpha=1),
        "EN_a01": ElasticNet(alpha=0.1, l1_ratio=0.5),
        "SVR_linear": SVR(kernel='linear', C=1),
        "SVR_rbf": SVR(kernel='rbf', C=1),
        "GBM_50": GradientBoostingRegressor(n_estimators=50, max_depth=2, random_state=42),
        "GBM_100": GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42),
        "RF_100": RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42),
    }

    for name, model in models.items():
        try:
            cv_scores = []
            for train_idx, test_idx in tscv.split(X_scaled):
                X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]

                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                r2 = 1 - np.sum((y_test - pred)**2) / np.sum((y_test - y_test.mean())**2)
                cv_scores.append(r2)

            avg_r2 = np.mean(cv_scores)
            std_r2 = np.std(cv_scores)

            if avg_r2 > best_r2:
                best_r2 = avg_r2
                best_config = {
                    "model": name, "k": k,
                    "cv_r2": avg_r2, "cv_std": std_r2,
                    "model_obj": model, "selector": selector, "scaler": scaler
                }
                print(f"  NEW BEST: {name} (k={k}): CV R2={avg_r2:.4f} (+/-{std_r2:.4f})")
        except:
            pass

print(f"\n{'='*80}")
print(f"BEST (CV): {best_config['model']} (k={best_config['k']})")
print(f"  CV R2: {best_config['cv_r2']:.4f} (+/-{best_config['cv_std']:.4f})")
print(f"{'='*80}")

# Final train/test
X_selected = best_config["selector"].transform(X)
X_scaled = best_config["scaler"].transform(X_selected)

train_end = 21
X_train, X_test = X_scaled[:train_end], X_scaled[train_end:]
y_train, y_test = y[:train_end], y[train_end:]
years_test = years[train_end:]

best_config["model_obj"].fit(X_train, y_train)
preds = best_config["model_obj"].predict(X_test)

test_r2 = 1 - np.sum((y_test - preds)**2) / np.sum((y_test - y_test.mean())**2)
rmse = np.sqrt(np.mean((y_test - preds)**2))

print(f"\nFinal Test R2: {test_r2:.4f}")
print(f"Final RMSE: {rmse:.4f}")

print(f"\n{'Year':<6} {'Actual':>8} {'Predicted':>10} {'Error':>8}")
print("-" * 35)
for i, y_true in enumerate(y_test):
    print(f"{int(years_test[i]):<6} {y_true:>8.2f}% {preds[i]:>10.2f}% {preds[i]-y_true:>8.2f}")

# Top features
selected = [features[i] for i in best_config["selector"].get_support(indices=True)]
print(f"\nTop 15 features:")
for f in selected[:15]:
    print(f"  {f}")
