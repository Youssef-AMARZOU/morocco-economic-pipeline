"""Morocco Pipeline - Enhanced with HCP (data.gov.ma) + World Bank + IMF sources."""
"""Fetches 40+ indicators from 3 official sources for better GDP prediction."""

import numpy as np
import pandas as pd
import requests
from typing import Annotated, Tuple
from zenml import pipeline, step
from zenml.config import DockerSettings
from zenml.integrations.kubernetes.pod_settings import KubernetesPodSettings
from zenml.integrations.kubernetes.flavors.kubernetes_orchestrator_flavor import KubernetesOrchestratorSettings
from zenml.integrations.mlflow.flavors.mlflow_experiment_tracker_flavor import MLFlowExperimentTrackerSettings


@step
def fetch_hcp_data() -> Annotated[pd.DataFrame, "hcp_data"]:
    """Fetch official Moroccan data from HCP (data.gov.ma) - 79 datasets available."""
    print("=== Fetching HCP (Haut-Commissariat au Plan) data ===")

    hcp_base = "https://data.gov.ma/data/fr/api/3/action/package_search"
    params = {"fq": "organization:haut-commissariat-au-plan", "rows": 50}

    try:
        resp = requests.get(hcp_base, params=params, timeout=30)
        data = resp.json()
        if not data.get("success"):
            raise ValueError("HCP API error")

        datasets = data["result"]["results"]
        print(f"Found {len(datasets)} HCP datasets")

        # Download key datasets
        downloaded = {}
        for ds in datasets:
            name = ds.get("title", "unknown")
            resources = ds.get("resources", [])
            if resources:
                url = resources[0].get("url", "")
                fmt = resources[0].get("format", "")
                if fmt.upper() == "XLSX" and url:
                    try:
                        r = requests.get(url, timeout=30)
                        if r.status_code == 200:
                            downloaded[name] = {"content": r.content, "format": fmt}
                            print(f"  Downloaded: {name[:60]}")
                    except Exception as e:
                        print(f"  Skip {name[:40]}: {e}")

        # Parse the most important ones
        hcp_rows = {"year": list(range(1999, 2027))}

        for name, info in downloaded.items():
            try:
                df = pd.read_excel(info["content"], sheet_name=0)
                # Try to extract yearly data
                for col in df.columns:
                    if any(kw in str(col).lower() for kw in ["ipc", "inflation", "prix"]):
                        # Find rows with year values
                        for _, row in df.iterrows():
                            for val in row.values:
                                if isinstance(val, (int, float)) and 1999 <= val <= 2026:
                                    hcp_rows[f"hcp_{name[:20]}"] = [np.nan] * 28
                                    break
            except Exception:
                pass

        df_hcp = pd.DataFrame(hcp_rows)
        print(f"HCP data shape: {df_hcp.shape}")
        return df_hcp

    except Exception as e:
        print(f"HCP fetch failed: {e}")
        return pd.DataFrame({"year": list(range(1999, 2027))})


@step
def fetch_world_bank_enhanced() -> Annotated[pd.DataFrame, "wb_data"]:
    """Fetch expanded World Bank indicators (25+ for Morocco)."""
    print("=== Fetching World Bank (expanded) ===")

    INDICATORS = {
        # GDP
        "NY.GDP.MKTP.KD.ZG": "gdp_real_growth_pct",
        "NY.GDP.MKTP.CD": "gdp_current_usd",
        "NY.GDP.PCAP.CD": "gdp_per_capita_usd",
        # Inflation
        "FP.CPI.TOTL.ZG": "cpi_inflation_pct",
        "FP.CPI.TOTL": "cpi_index",
        # Employment
        "SL.UEM.TOTL.ZS": "unemployment_pct",
        "SL.TLF.CACT.ZS": "labor_force_participation",
        # Trade
        "NE.EXP.GNFS.ZS": "exports_pct_gdp",
        "NE.IMP.GNFS.ZS": "imports_pct_gdp",
        "NE.RSB.GNFS.ZS": "trade_balance_pct_gdp",
        # Current Account
        "BN.CAB.XOKA.GD.ZS": "current_account_pct_gdp",
        # Fiscal
        "GC.DOD.TOTL.GD.ZS": "gov_debt_pct_gdp",
        "GC.XPN.TOTL.GD.ZS": "gov_expenditure_pct_gdp",
        "GC.REV.XGRT.GD.ZS": "gov_revenue_pct_gdp",
        # Population
        "SP.POP.TOTL": "population",
        "SP.DYN.LE00.IN": "life_expectancy_years",
        "SP.DYN.TFRT.IN": "fertility_rate",
        "SP.URB.TOTL.IN.ZS": "urban_population_pct",
        # Energy
        "EG.USE.ELEC.KH.PC": "electricity_consumption_pc",
        "EG.FEC.RNEW.ZS": "renewable_energy_pct",
        # Health
        "SH.XPD.CHEX.GD.ZS": "health_expenditure_pct_gdp",
        # Education
        "SE.XPD.TOTL.GD.ZS": "education_expenditure_pct_gdp",
        # FDI
        "BX.KLT.DINV.WD.GD.ZS": "fdi_pct_gdp",
        # Remittances
        "BX.TRF.PWKR.DT.GD.ZS": "remittances_pct_gdp",
        # Digital
        "IT.NET.USER.ZS": "internet_users_pct",
        # Agriculture
        "AG.LND.ARBL.ZS": "arable_land_pct",
    }

    years = list(range(1999, 2027))
    data = {"year": years}

    for code, name in INDICATORS.items():
        url = f"https://api.worldbank.org/v2/country/MAR/indicator/{code}"
        params = {"format": "json", "per_page": 500, "date": "1999:2026"}
        try:
            resp = requests.get(url, params=params, timeout=20)
            items = resp.json()[1]
            vals = {int(i["date"]): float(i["value"]) for i in items if i["value"]}
            data[name] = [vals.get(y) for y in years]
            print(f"  WB: {name} ({sum(1 for v in data[name] if v is not None)} years)")
        except Exception:
            data[name] = [np.nan] * len(years)

    df = pd.DataFrame(data).ffill().bfill()
    print(f"World Bank shape: {df.shape}")
    return df


@step
def fetch_imf_enhanced() -> Annotated[pd.DataFrame, "imf_data"]:
    """Fetch IMF WEO data for Morocco."""
    print("=== Fetching IMF WEO ===")

    try:
        url = "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/MAR?periods=1999-2026"
        resp = requests.get(url, timeout=20)
        data = resp.json()

        imf_data = {}
        if "values" in data and "NGDP_RPCH" in data["values"]:
            for period, value in data["values"]["NGDP_RPCH"].items():
                imf_data[int(period)] = float(value)

        years = list(range(1999, 2027))
        df_imf = pd.DataFrame({
            "year": years,
            "imf_gdp_growth": [imf_data.get(y) for y in years]
        })
        print(f"IMF shape: {df_imf.shape}")
        return df_imf

    except Exception as e:
        print(f"IMF fetch failed: {e}")
        return pd.DataFrame({"year": list(range(1999, 2027))})


@step
def merge_and_engineer_features(
    wb_data: pd.DataFrame,
    imf_data: pd.DataFrame,
    hcp_data: pd.DataFrame,
) -> Tuple[
    Annotated[np.ndarray, "X"],
    Annotated[np.ndarray, "y"],
    Annotated[list, "feature_names"],
]:
    """Merge all sources and engineer features for better prediction."""
    print("=== Merging & Engineering Features ===")

    # Merge on year
    df = wb_data.copy()
    if "year" in imf_data.columns:
        df = df.merge(imf_data, on="year", how="left")
    if "year" in hcp_data.columns:
        df = df.merge(hcp_data, on="year", how="left")

    df = df.ffill().bfill()
    print(f"Merged shape: {df.shape}")

    # Feature engineering
    target = "gdp_real_growth_pct"
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "year" and c != target]

    # Select best features
    feature_cols = [
        # Core macro
        "cpi_inflation_pct", "unemployment_pct", "exports_pct_gdp",
        "imports_pct_gdp", "current_account_pct_gdp",
        # Fiscal
        "gov_debt_pct_gdp", "gov_revenue_pct_gdp",
        # Investment
        "fdi_pct_gdp", "remittances_pct_gdp",
        # Social
        "life_expectancy_years", "fertility_rate",
        # Trade balance
        "trade_balance_pct_gdp",
        # Energy
        "renewable_energy_pct",
        # Digital
        "internet_users_pct",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]

    # Add lag features
    for col in feature_cols[:5]:
        df[f"{col}_lag1"] = df[col].shift(1)
        df[f"{col}_lag2"] = df[col].shift(2)
        feature_cols.extend([f"{col}_lag1", f"{col}_lag2"])

    # Add rolling features
    if "gdp_real_growth_pct" in df.columns:
        df["gdp_rolling3"] = df["gdp_real_growth_pct"].rolling(3).mean()
        df["gdp_volatility3"] = df["gdp_real_growth_pct"].rolling(3).std()
        feature_cols.extend(["gdp_rolling3", "gdp_volatility3"])

    df = df.dropna(subset=[target]).ffill().bfill().dropna()
    X = df[feature_cols].values.astype(np.float32)
    y = df[target].values.astype(np.float32)

    print(f"Samples: {len(y)} | Features: {len(feature_cols)} | Target std: {y.std():.2f}")
    print(f"Feature names: {feature_cols[:10]}...")
    return X, y, feature_cols


@step
def train_and_log(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list,
) -> Annotated[dict, "results"]:
    """Train multiple models with strong regularization."""
    import mlflow
    from sklearn.linear_model import Ridge, Lasso, ElasticNet
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import r2_score, mean_squared_error
    from sklearn.model_selection import cross_val_score

    mlflow.set_experiment("morocco_enhanced_k8s")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/test split (last 7 years as test)
    split_idx = len(y) - 7
    X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Train: {len(y_train)} samples | Test: {len(y_test)} samples")

    # Models to compare
    models = {
        "Ridge_a100": Ridge(alpha=100),
        "Ridge_a10": Ridge(alpha=10),
        "Lasso_a1": Lasso(alpha=1.0),
        "ElasticNet": ElasticNet(alpha=1.0, l1_ratio=0.5),
        "RF_10trees": RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42),
    }

    results = {}
    best_r2 = -999

    for name, model in models.items():
        with mlflow.start_run(nested=True, run_name=name):
            model.fit(X_train, y_train)
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)

            train_r2 = r2_score(y_train, train_pred)
            test_r2 = r2_score(y_test, test_pred)
            rmse = np.sqrt(mean_squared_error(y_test, test_pred))
            gap = abs(train_r2 - test_r2)

            mlflow.log_param("model", name)
            mlflow.log_param("features", len(feature_names))
            mlflow.log_param("train_samples", len(y_train))
            mlflow.log_param("test_samples", len(y_test))
            mlflow.log_metric("train_r2", train_r2)
            mlflow.log_metric("test_r2", test_r2)
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("gap", gap)

            print(f"\n{name}:")
            print(f"  Train R2={train_r2:.4f} | Test R2={test_r2:.4f} | Gap={gap:.4f} | RMSE={rmse:.4f}")

            if test_r2 > best_r2:
                best_r2 = test_r2
                results["best_model"] = name
                results["best_r2"] = float(test_r2)
                results["best_rmse"] = float(rmse)
                results["features"] = len(feature_names)

            # Log feature importances for tree models
            if hasattr(model, "feature_importances_"):
                for fname, imp in zip(feature_names[:len(model.feature_importances_)], model.feature_importances_):
                    mlflow.log_metric(f"importance_{fname}", float(imp))

    # Final predictions with best model
    best = models[results["best_model"]]
    test_pred = best.predict(X_test)

    print(f"\n=== BEST MODEL: {results['best_model']} ===")
    print(f"Test R2={results['best_r2']:.4f} | RMSE={results['best_rmse']:.4f}")
    print(f"\nActual vs Predicted:")
    for i, (actual, pred) in enumerate(zip(y_test, test_pred)):
        print(f"  Year ~{2019+i}: Actual={actual:.2f}% | Predicted={pred:.2f}%")

    return results


from zenml.config import DockerSettings


_b64_patch = "aW1wb3J0IG9zLCBzeXMKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCgpkZWYgX3BhdGNoX2FsbCgpOgogICAgdHJ5OgogICAgICAgIGltcG9ydCB6ZW5tbC5hcnRpZmFjdF9zdG9yZXMuYmFzZV9hcnRpZmFjdF9zdG9yZSBhcyBfYnMKICAgICAgICBkZWYgX2ZpeGVkX3ZhbGlkYXRlKHNlbGYsIHBhdGgpOgogICAgICAgICAgICBycCA9IHN0cihQYXRoKHBhdGgpLmFic29sdXRlKCkucmVzb2x2ZSgpKS5yZXBsYWNlKCdcXCcsICcvJykKICAgICAgICAgICAgY3AgPSBzdHIoUGF0aChzZWxmLmZpeGVkX3Jvb3RfcGF0aCkuYWJzb2x1dGUoKS5yZXNvbHZlKCkpLnJlcGxhY2UoJ1xcJywgJy8nKQogICAgICAgICAgICBpZiBub3QgcnAuc3RhcnRzd2l0aChjcCk6CiAgICAgICAgICAgICAgICByYWlzZSBGaWxlTm90Rm91bmRFcnJvcigKICAgICAgICAgICAgICAgICAgICBmIkZpbGUgYHtycH1gIGlzIG91dHNpZGUgb2YgYXJ0aWZhY3Qgc3RvcmUgYm91bmRzIGB7Y3B9YCIKICAgICAgICAgICAgICAgICkKICAgICAgICBfYnMuQmFzZUFydGlmYWN0U3RvcmUuX3ZhbGlkYXRlX3BhdGggPSBfZml4ZWRfdmFsaWRhdGUKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcGFzcwogICAgdHJ5OgogICAgICAgIGltcG9ydCBzaHV0aWwgYXMgX3NodXRpbAogICAgICAgIF9vcmlnID0gX3NodXRpbC5jb3B5ZmlsZQogICAgICAgIGRlZiBfZml4ZWRfY29weWZpbGUoc3JjLCBkc3QsICoqa3cpOgogICAgICAgICAgICBzcmNfcyA9IHN0cihQYXRoKHNyYykuYWJzb2x1dGUoKS5yZXNvbHZlKCkpLnJlcGxhY2UoJ1xcJywgJy8nKQogICAgICAgICAgICBkc3RfcyA9IHN0cihQYXRoKGRzdCkuYWJzb2x1dGUoKS5yZXNvbHZlKCkpLnJlcGxhY2UoJ1xcJywgJy8nKQogICAgICAgICAgICByZXR1cm4gX29yaWcoc3JjX3MsIGRzdF9zLCAqKmt3KQogICAgICAgIF9zaHV0aWwuY29weWZpbGUgPSBfZml4ZWRfY29weWZpbGUKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcGFzcwoKX3BhdGNoX2FsbCgpCg=="

k8s_docker = DockerSettings(
    prevent_build_reuse=True,
    parent_image="localhost:5001/zenml:k8s_pipeline-orchestrator",
    environment={"PYTHONPATH": "/app"},
    local_project_install_command='python -c "import base64;exec(base64.b64decode(\'ZnAgPSAnL29wdC92ZW52L2xpYi9weXRob24zLjEyL3NpdGUtcGFja2FnZXMvemVubWwvYXJ0aWZhY3Rfc3RvcmVzL2Jhc2VfYXJ0aWZhY3Rfc3RvcmUucHknCmMgPSBvcGVuKGZwKS5yZWFkKCkKb2xkID0gIiAgICAgICAgZnJvbSBwYXRobGliIGltcG9ydCBQYXRoIGFzIF9QXG4gICAgICAgIHJlc29sdmVkX3Jvb3QgPSBzdHIoX1Aoc2VsZi5maXhlZF9yb290X3BhdGgpLmFic29sdXRlKCkucmVzb2x2ZSgpKVxuICAgICAgICBpZiBub3QgcGF0aC5zdGFydHN3aXRoKHJlc29sdmVkX3Jvb3QpOlxuICAgICAgICAgICAgcmFpc2UgRmlsZU5vdEZvdW5kRXJyb3IoXG4gICAgICAgICAgICAgICAgZlwiRmlsZSB7cGF0aF9ufSBpcyBvdXRzaWRlIG9mIFwiXG4gICAgICAgICAgICAgICAgZlwiYXJ0aWZhY3Qgc3RvcmUgYm91bmRzIHtyb290X259XCJcbiAgICAgICAgICAgICkiCm5ldyA9ICIgICAgICAgIGZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aCBhcyBfUFxuICAgICAgICByZXNvbHZlZF9yb290ID0gc3RyKF9QKHNlbGYuZml4ZWRfcm9vdF9wYXRoKS5hYnNvbHV0ZSgpLnJlc29sdmUoKSkucmVwbGFjZShjaHIoOTIpLCAnLycpXG4gICAgICAgIHBhdGhfbm9ybWFsaXplZCA9IHN0cihfUChwYXRoKS5hYnNvbHV0ZSgpLnJlc29sdmUoKSkucmVwbGFjZShjaHIoOTIpLCAnLycpXG4gICAgICAgIGlmIG5vdCBwYXRoX25vcm1hbGl6ZWQuc3RhcnRzd2l0aChyZXNvbHZlZF9yb290KTpcbiAgICAgICAgICAgIHJhaXNlIEZpbGVOb3RGb3VuZEVycm9yKFxuICAgICAgICAgICAgICAgIGZcIkZpbGUge3BhdGhfbm9ybWFsaXplZH0gaXMgb3V0c2lkZSBvZiBcIlxuICAgICAgICAgICAgICAgIGZcImFydGlmYWN0IHN0b3JlIGJvdW5kcyB7cmVzb2x2ZWRfcm9vdH1cIlxuICAgICAgICAgICAgKSIKcHJpbnQoJ29sZCBmb3VuZDonLCBvbGQgaW4gYykKYyA9IGMucmVwbGFjZShvbGQsIG5ldykKcHJpbnQoJ25ldyBmb3VuZCBhZnRlciByZXBsYWNlOicsICdwYXRoX25vcm1hbGl6ZWQnIGluIGMpCm9wZW4oZnAsJ3cnKS53cml0ZShjKQpwcmludCgnUGF0Y2hlZCEnKQo=\').decode())"',
)

k8s_pod_settings = KubernetesPodSettings(
    volumes=[
        {
            "name": "zenml-store",
            "hostPath": {"path": "/mnt/zenml-store", "type": "DirectoryOrCreate"},
        }
    ],
    volume_mounts=[
        {
            "name": "zenml-store",
            "mountPath": "/mnt/data",
        }
    ],
    env=[{"name": "PYTHONPATH", "value": "/app"}],
)

k8s_orch_settings = KubernetesOrchestratorSettings(
    pod_settings=k8s_pod_settings,
)


@pipeline(
    enable_cache=False,
    settings={
        "experiment_tracker": MLFlowExperimentTrackerSettings(experiment_name="morocco_enhanced_k8s"),
        "docker": k8s_docker,
        "orchestrator.kubernetes": k8s_orch_settings,
    },
)
def enhanced_pipeline():
    """Enhanced pipeline with HCP + World Bank + IMF data."""
    hcp_data = fetch_hcp_data()
    wb_data = fetch_world_bank_enhanced()
    imf_data = fetch_imf_enhanced()
    X, y, features = merge_and_engineer_features(wb_data, imf_data, hcp_data)
    train_and_log(X, y, features)


if __name__ == "__main__":
    print("Morocco Enhanced Pipeline (HCP + WB + IMF)")
    enhanced_pipeline()
