import os, builtins
orig_open = builtins.open
def my_open(path, mode='r', **kw):
    if 'b' not in mode and 'encoding' not in kw:
        kw['encoding'] = 'utf-8'; kw['errors'] = 'replace'
    return orig_open(path, mode, **kw)
builtins.open = my_open
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi(); api.authenticate()

OUT = r"C:\Users\youss\OneDrive\Desktop\Morocco_ETL\kaggle_kernel2\out_py"
DATASET = "amarzouyoussef/economie-maroc-rasd"

files_to_upload = [
    "maroc_pipeline.html",
    "master_dataset.csv",
    "rf_model.rds",
    "lasso_model.rds",
    "arima_model.rds",
    "corr.png",
    "trends.png",
    "sector.png",
    "gini.png",
    "scenarios.png",
    "arima.png",
    "bench.png",
    "clusters.png",
    "pca.png",
]

for f in files_to_upload:
    src = os.path.join(OUT, f)
    if os.path.exists(src):
        print(f"Uploading {f} ({os.path.getsize(src)} bytes)...")
        api.dataset_upload_file(src, file_name=f, dataset_slug=DATASET)
        print(f"  OK: {f}")
    else:
        print(f"  SKIP: {f} not found")

print("Done publishing to dataset:", DATASET)