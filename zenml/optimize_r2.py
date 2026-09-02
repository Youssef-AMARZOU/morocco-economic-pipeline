"""Find optimal R2 by testing all model/feature combinations."""
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\enhanced_data\morocco_indicators_enhanced.csv")

target = "gdp_real_growth_pct"
exclude = ["year", target, "gdp_current_usd", "gdp_per_capita_usd",
           "hcp_datasets_count", "cpi_index"]

features = [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'int64']]
print(f"Features: {len(features)}")

X = df[features].values
y = df[target].values
years = df["year"].values

# Impute NaN with median
imputer = SimpleImputer(strategy='median')
X = imputer.fit_transform(X)

# Time series split
train_end = 21
X_train, X_test = X[:train_end], X[train_end:]
y_train, y_test = y[:train_end], y[train_end:]
years_test = years[train_end:]

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

print(f"Train: {train_end}, Test: {len(y_test)}")
print(f"Test years: {list(years_test)}")

models = {
    "Ridge_a1": Ridge(alpha=1),
    "Ridge_a5": Ridge(alpha=5),
    "Ridge_a10": Ridge(alpha=10),
    "Ridge_a50": Ridge(alpha=50),
    "Ridge_a100": Ridge(alpha=100),
    "Lasso_a001": Lasso(alpha=0.01),
    "Lasso_a01": Lasso(alpha=0.1),
    "Lasso_a1": Lasso(alpha=1),
    "Lasso_a5": Lasso(alpha=5),
    "EN_a01_l1": ElasticNet(alpha=0.1, l1_ratio=0.1),
    "EN_a01_l5": ElasticNet(alpha=0.1, l1_ratio=0.5),
    "EN_a1_l1": ElasticNet(alpha=1, l1_ratio=0.1),
    "RF_10": RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42),
    "RF_50": RandomForestRegressor(n_estimators=50, max_depth=3, random_state=42),
    "RF_100": RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42),
    "GBM_10": GradientBoostingRegressor(n_estimators=10, max_depth=2, random_state=42),
    "GBM_50": GradientBoostingRegressor(n_estimators=50, max_depth=2, random_state=42),
    "GBM_100": GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42),
    "SVR_rbf": SVR(kernel='rbf', C=1),
    "SVR_linear": SVR(kernel='linear', C=1),
}

results = []
for name, model in models.items():
    try:
        if name.startswith("SVR"):
            model.fit(X_train_s, y_train)
            train_pred = model.predict(X_train_s)
            test_pred = model.predict(X_test_s)
        else:
            model.fit(X_train, y_train)
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)

        train_r2 = 1 - np.sum((y_train - train_pred)**2) / np.sum((y_train - y_train.mean())**2)
        test_r2 = 1 - np.sum((y_test - test_pred)**2) / np.sum((y_test - y_test.mean())**2)
        rmse = np.sqrt(np.mean((y_test - test_pred)**2))
        gap = train_r2 - test_r2

        if hasattr(model, 'coef_'):
            n_features = np.sum(np.abs(model.coef_) > 1e-6)
        else:
            n_features = len(features)

        results.append({
            "model": name,
            "train_r2": round(train_r2, 4),
            "test_r2": round(test_r2, 4),
            "rmse": round(rmse, 4),
            "gap": round(gap, 4),
            "n_features": int(n_features)
        })
    except Exception as e:
        pass

results_df = pd.DataFrame(results).sort_values("test_r2", ascending=False)
print("\n" + "="*80)
print("ALL RESULTS (sorted by Test R2)")
print("="*80)
print(results_df.to_string(index=False))

best = results_df.iloc[0]
print(f"\n{'='*80}")
print(f"BEST MODEL: {best['model']}")
print(f"  Train R2: {best['train_r2']}")
print(f"  Test R2:  {best['test_r2']}")
print(f"  RMSE:     {best['rmse']}")
print(f"  Gap:      {best['gap']}")
print(f"  Features: {best['n_features']}")
print(f"{'='*80}")

# Predictions for best model
best_model = models[best['model']]
if best['model'].startswith("SVR"):
    best_model.fit(X_train_s, y_train)
    preds = best_model.predict(X_test_s)
else:
    best_model.fit(X_train, y_train)
    preds = best_model.predict(X_test)

print(f"\n{'Year':<6} {'Actual':>8} {'Predicted':>10} {'Error':>8}")
print("-" * 35)
for i, y_true in enumerate(y_test):
    print(f"{int(years_test[i]):<6} {y_true:>8.2f}% {preds[i]:>10.2f}% {preds[i]-y_true:>8.2f}")
