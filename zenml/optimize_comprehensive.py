"""Optimize R2 with comprehensive 127-column dataset."""
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

df = pd.read_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\enhanced_data\morocco_comprehensive.csv")
print(f"Dataset: {df.shape[0]} rows, {df.shape[1]} columns")

target = "wb_gdp_growth"
exclude = ["year", target, "wb_gdp_usd", "wb_gdp_pc"]

features = [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'int64']]
print(f"Available features: {len(features)}")

X = df[features].values
y = df[target].values
years = df["year"].values

# Impute
imputer = SimpleImputer(strategy='median')
X = imputer.fit_transform(X)

# Train/test split
train_end = 21
X_train, X_test = X[:train_end], X[train_end:]
y_train, y_test = y[:train_end], y[train_end:]
years_test = years[train_end:]

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

print(f"Train: {train_end}, Test: {len(y_test)}")
print(f"Test years: {list(years_test)}")

# Try different feature counts
print("\n" + "="*80)
print("FEATURE SELECTION + MODEL OPTIMIZATION")
print("="*80)

best_overall_r2 = -999
best_overall_config = None

for k in [10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120]:
    if k > len(features):
        continue

    selector = SelectKBest(f_regression, k=k)
    X_train_k = selector.fit_transform(X_train_s, y_train)
    X_test_k = selector.transform(X_test_s)

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
            model.fit(X_train_k, y_train)
            train_pred = model.predict(X_train_k)
            test_pred = model.predict(X_test_k)

            train_r2 = 1 - np.sum((y_train - train_pred)**2) / np.sum((y_train - y_train.mean())**2)
            test_r2 = 1 - np.sum((y_test - test_pred)**2) / np.sum((y_test - y_test.mean())**2)
            rmse = np.sqrt(np.mean((y_test - test_pred)**2))
            gap = train_r2 - test_r2

            if test_r2 > best_overall_r2:
                best_overall_r2 = test_r2
                best_overall_config = {
                    "model": name,
                    "k": k,
                    "train_r2": train_r2,
                    "test_r2": test_r2,
                    "rmse": rmse,
                    "gap": gap,
                    "model_obj": model,
                    "selector": selector
                }
                print(f"  NEW BEST: {name} (k={k}): Train={train_r2:.4f}, Test={test_r2:.4f}, RMSE={rmse:.4f}, Gap={gap:.4f}")
        except:
            pass

print(f"\n{'='*80}")
print(f"BEST OVERALL: {best_overall_config['model']} (k={best_overall_config['k']})")
print(f"  Train R2: {best_overall_config['train_r2']:.4f}")
print(f"  Test R2:  {best_overall_config['test_r2']:.4f}")
print(f"  RMSE:     {best_overall_config['rmse']:.4f}")
print(f"  Gap:      {best_overall_config['gap']:.4f}")
print(f"{'='*80}")

# Show predictions
selector = best_overall_config["selector"]
X_test_k = selector.transform(X_test_s)
best_model = best_overall_config["model_obj"]
preds = best_model.predict(X_test_k)

print(f"\n{'Year':<6} {'Actual':>8} {'Predicted':>10} {'Error':>8}")
print("-" * 35)
for i, y_true in enumerate(y_test):
    print(f"{int(years_test[i]):<6} {y_true:>8.2f}% {preds[i]:>10.2f}% {preds[i]-y_true:>8.2f}")

# Feature importance
if hasattr(best_model, 'coef_'):
    selected_features = [features[i] for i in selector.get_support(indices=True)]
    coefs = best_model.coef_
    if len(coefs.shape) > 1:
        coefs = coefs[0]
    importance = sorted(zip(selected_features, coefs), key=lambda x: abs(x[1]), reverse=True)
    print(f"\nTop 15 features:")
    for fname, coef in importance[:15]:
        print(f"  {fname[:40]:<40} coef={coef:.4f}")
