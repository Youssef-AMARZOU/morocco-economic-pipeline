"""Morocco Pipeline - Kubernetes-ready (self-contained, no local file access)."""

import numpy as np
import pandas as pd
import requests
from typing import Annotated, Tuple
from zenml import pipeline, step
from zenml.integrations.mlflow.flavors.mlflow_experiment_tracker_flavor import MLFlowExperimentTrackerSettings
from zenml.config import DockerSettings


INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "gdp_real_growth_pct",
    "FP.CPI.TOTL.ZG": "cpi_inflation_pct",
    "SL.UEM.TOTL.ZS": "unemployment_pct",
    "NE.EXP.GNFS.ZS": "exports_pct_gdp",
    "NE.IMP.GNFS.ZS": "imports_pct_gdp",
    "BN.CAB.XOKA.GD.ZS": "current_account_pct_gdp",
    "SP.POP.TOTL": "population",
    "SP.DYN.LE00.IN": "life_expectancy_years",
    "EG.USE.ELEC.KH.PC": "electricity_consumption_pc",
    "EG.FEC.RNEW.ZS": "renewable_energy_pct",
    "SH.XPD.CHEX.GD.ZS": "health_expenditure_pct_gdp",
    "FX.OWN.TOTL.ZS": "account_ownership_pct",
}


@step
def fetch_and_prepare() -> Tuple[
    Annotated[np.ndarray, "X"],
    Annotated[np.ndarray, "y"],
    Annotated[list, "feature_names"],
]:
    """Fetch World Bank data directly from API (no local files needed)."""
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
        except Exception:
            data[name] = [np.nan] * len(years)

    df = pd.DataFrame(data).ffill().bfill()

    target = "gdp_real_growth_pct"
    features = [
        "cpi_inflation_pct", "unemployment_pct", "exports_pct_gdp",
        "imports_pct_gdp", "current_account_pct_gdp",
    ]
    features = [c for c in features if c in df.columns]

    for col in features[:3]:
        df[f"{col}_lag1"] = df[col].shift(1)
        features.append(f"{col}_lag1")

    df = df.dropna(subset=[target]).ffill().bfill().dropna()
    X = df[features].values.astype(np.float32)
    y = df[target].values.astype(np.float32)

    print(f"Samples: {len(y)} | Features: {len(features)} | Target std: {y.std():.2f}")
    return X, y, features


@step
def train_and_log(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list,
) -> Annotated[dict, "results"]:
    """Train model with strong regularization."""
    import mlflow
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import r2_score, mean_squared_error

    mlflow.log_param("n_features", int(X.shape[1]))
    mlflow.log_param("n_samples", int(len(y)))

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    split = int(len(X) * 0.7)
    X_train, X_test = X_scaled[:split], X_scaled[split:]
    y_train, y_test = y[:split], y[split:]

    model = Ridge(alpha=1000)
    model.fit(X_train, y_train)
    test_r2 = r2_score(y_test, model.predict(X_test))
    rmse = np.sqrt(mean_squared_error(y_test, model.predict(X_test)))

    mlflow.log_metric("test_r2", float(test_r2))
    mlflow.log_metric("rmse", float(rmse))

    print(f"R2={test_r2:.4f} | RMSE={rmse:.4f}")

    test_pred = model.predict(X_test)
    print("\nActual vs Predicted:")
    for i, (actual, pred) in enumerate(zip(y_test, test_pred)):
        print(f"  Year ~{2019+i}: Actual={actual:.2f}% | Predicted={pred:.2f}%")

    return {"test_r2": float(test_r2), "rmse": float(rmse)}


_b64_patch = "aW1wb3J0IG9zLCBzeXMKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCgpkZWYgX3BhdGNoX2FsbCgpOgogICAgdHJ5OgogICAgICAgIGltcG9ydCB6ZW5tbC5hcnRpZmFjdF9zdG9yZXMuYmFzZV9hcnRpZmFjdF9zdG9yZSBhcyBfYnMKICAgICAgICBkZWYgX2ZpeGVkX3ZhbGlkYXRlKHNlbGYsIHBhdGgpOgogICAgICAgICAgICBycCA9IHN0cihQYXRoKHBhdGgpLmFic29sdXRlKCkucmVzb2x2ZSgpKS5yZXBsYWNlKCdcXCcsICcvJykKICAgICAgICAgICAgY3AgPSBzdHIoUGF0aChzZWxmLmZpeGVkX3Jvb3RfcGF0aCkuYWJzb2x1dGUoKS5yZXNvbHZlKCkpLnJlcGxhY2UoJ1xcJywgJy8nKQogICAgICAgICAgICBpZiBub3QgcnAuc3RhcnRzd2l0aChjcCk6CiAgICAgICAgICAgICAgICByYWlzZSBGaWxlTm90Rm91bmRFcnJvcigKICAgICAgICAgICAgICAgICAgICBmIkZpbGUgYHtycH1gIGlzIG91dHNpZGUgb2YgYXJ0aWZhY3Qgc3RvcmUgYm91bmRzIGB7Y3B9YCIKICAgICAgICAgICAgICAgICkKICAgICAgICBfYnMuQmFzZUFydGlmYWN0U3RvcmUuX3ZhbGlkYXRlX3BhdGggPSBfZml4ZWRfdmFsaWRhdGUKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcGFzcwogICAgdHJ5OgogICAgICAgIGltcG9ydCBzaHV0aWwgYXMgX3NodXRpbAogICAgICAgIF9vcmlnID0gX3NodXRpbC5jb3B5ZmlsZQogICAgICAgIGRlZiBfZml4ZWRfY29weWZpbGUoc3JjLCBkc3QsICoqa3cpOgogICAgICAgICAgICBzcmNfcyA9IHN0cihQYXRoKHNyYykuYWJzb2x1dGUoKS5yZXNvbHZlKCkpLnJlcGxhY2UoJ1xcJywgJy8nKQogICAgICAgICAgICBkc3RfcyA9IHN0cihQYXRoKGRzdCkuYWJzb2x1dGUoKS5yZXNvbHZlKCkpLnJlcGxhY2UoJ1xcJywgJy8nKQogICAgICAgICAgICByZXR1cm4gX29yaWcoc3JjX3MsIGRzdF9zLCAqKmt3KQogICAgICAgIF9zaHV0aWwuY29weWZpbGUgPSBfZml4ZWRfY29weWZpbGUKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcGFzcwoKX3BhdGNoX2FsbCgpCg=="

k8s_docker = DockerSettings(
    prevent_build_reuse=True,
    parent_image="localhost:5001/zenml:k8s_pipeline-orchestrator",
    environment={"PYTHONPATH": "/app"},
    local_project_install_command='python -c "import base64;exec(base64.b64decode(\'ZnAgPSAnL29wdC92ZW52L2xpYi9weXRob24zLjEyL3NpdGUtcGFja2FnZXMvemVubWwvYXJ0aWZhY3Rfc3RvcmVzL2Jhc2VfYXJ0aWZhY3Rfc3RvcmUucHknCmMgPSBvcGVuKGZwKS5yZWFkKCkKb2xkID0gIiAgICAgICAgZnJvbSBwYXRobGliIGltcG9ydCBQYXRoIGFzIF9QXG4gICAgICAgIHJlc29sdmVkX3Jvb3QgPSBzdHIoX1Aoc2VsZi5maXhlZF9yb290X3BhdGgpLmFic29sdXRlKCkucmVzb2x2ZSgpKVxuICAgICAgICBpZiBub3QgcGF0aC5zdGFydHN3aXRoKHJlc29sdmVkX3Jvb3QpOlxuICAgICAgICAgICAgcmFpc2UgRmlsZU5vdEZvdW5kRXJyb3IoXG4gICAgICAgICAgICAgICAgZlwiRmlsZSB7cGF0aF9ufSBpcyBvdXRzaWRlIG9mIFwiXG4gICAgICAgICAgICAgICAgZlwiYXJ0aWZhY3Qgc3RvcmUgYm91bmRzIHtyb290X259XCJcbiAgICAgICAgICAgICkiCm5ldyA9ICIgICAgICAgIGZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aCBhcyBfUFxuICAgICAgICByZXNvbHZlZF9yb290ID0gc3RyKF9QKHNlbGYuZml4ZWRfcm9vdF9wYXRoKS5hYnNvbHV0ZSgpLnJlc29sdmUoKSkucmVwbGFjZShjaHIoOTIpLCAnLycpXG4gICAgICAgIHBhdGhfbm9ybWFsaXplZCA9IHN0cihfUChwYXRoKS5hYnNvbHV0ZSgpLnJlc29sdmUoKSkucmVwbGFjZShjaHIoOTIpLCAnLycpXG4gICAgICAgIGlmIG5vdCBwYXRoX25vcm1hbGl6ZWQuc3RhcnRzd2l0aChyZXNvbHZlZF9yb290KTpcbiAgICAgICAgICAgIHJhaXNlIEZpbGVOb3RGb3VuZEVycm9yKFxuICAgICAgICAgICAgICAgIGZcIkZpbGUge3BhdGhfbm9ybWFsaXplZH0gaXMgb3V0c2lkZSBvZiBcIlxuICAgICAgICAgICAgICAgIGZcImFydGlmYWN0IHN0b3JlIGJvdW5kcyB7cmVzb2x2ZWRfcm9vdH1cIlxuICAgICAgICAgICAgKSIKcHJpbnQoJ29sZCBmb3VuZDonLCBvbGQgaW4gYykKYyA9IGMucmVwbGFjZShvbGQsIG5ldykKcHJpbnQoJ25ldyBmb3VuZCBhZnRlciByZXBsYWNlOicsICdwYXRoX25vcm1hbGl6ZWQnIGluIGMpCm9wZW4oZnAsJ3cnKS53cml0ZShjKQpwcmludCgnUGF0Y2hlZCEnKQo=\').decode())"',
)

from zenml.integrations.kubernetes.pod_settings import KubernetesPodSettings

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


from zenml.integrations.kubernetes.flavors.kubernetes_orchestrator_flavor import KubernetesOrchestratorSettings

k8s_orch_settings = KubernetesOrchestratorSettings(
    pod_settings=k8s_pod_settings,
)


@pipeline(
    enable_cache=False,
    settings={
        "experiment_tracker": MLFlowExperimentTrackerSettings(experiment_name="morocco_k8s"),
        "docker": k8s_docker,
        "orchestrator.kubernetes": k8s_orch_settings,
    },
)
def k8s_pipeline():
    """Pipeline that runs entirely on Kubernetes (no local file access)."""
    X, y, features = fetch_and_prepare()
    train_and_log(X, y, features)


if __name__ == "__main__":
    print("Morocco Kubernetes Pipeline")
    k8s_pipeline()
