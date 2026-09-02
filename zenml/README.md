# Morocco Economic Pipeline - ZenML MLOps

## Setup
```bash
pip install zenml
zenml init
zenml integration install kubernetes mlflow
```

## Pipeline Variants

| Script | Description |
|--------|-------------|
| `run_pipeline.py` | Basic 5-step pipeline (local) |
| `run_mlflow.py` | MLflow experiment tracking |
| `run_real.py` | Real World Bank data (17 indicators) |
| `run_full.py` | Full 29-indicator pipeline |
| `run_optimized.py` | Feature-selected pipeline |
| `run_max_reg.py` | Max-regularization (Ridge α=1000) |
| `run_deploy.py` | Model deployment |
| `run_scheduled.py` | Cron-scheduled pipeline |
| `run_k8s.py` | **Kubernetes pipeline (recommended)** |

## Kubernetes Setup
```bash
# Start Kind cluster
kind create cluster --config kind-config.yaml

# Deploy ZenML server
docker run -d --name zenml-server -p 8080:8080 zenmldocker/zenml-server:0.96.3

# Register components
zenml experiment-tracker register mlflow_tracker --flavor=mlflow --tracking_uri=http://localhost:5000
zenml orchestrator register k8s_orch --flavor=kubernetes
zenml artifact-store register shared_store_linux --flavor=local --path=/mnt/data
zenml container-registry register local_registry --flavor=default --uri=localhost:5001

# Create and activate stack
zenml stack register k8s_stack_linux -o k8s_orch -a shared_store_linux -c local_registry -e mlflow_tracker
zenml stack set k8s_stack_linux
```

## Run Pipeline
```bash
python run_k8s.py
```

## Dashboard
- ZenML: http://localhost:8080
- MLflow: http://localhost:5000
