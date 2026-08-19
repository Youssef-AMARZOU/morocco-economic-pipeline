import os, builtins
orig_open = builtins.open
def my_open(path, mode='r', **kw):
    if 'b' not in mode and 'encoding' not in kw:
        kw['encoding'] = 'utf-8'; kw['errors'] = 'replace'
    return orig_open(path, mode, **kw)
builtins.open = my_open
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi(); api.authenticate()
slug = "amarzouyoussef/maroc-pipeline-r"
out = r"C:\Users\youss\OneDrive\Desktop\Morocco_ETL\kaggle_kernel2\out_py"
os.makedirs(out, exist_ok=True)
api.kernels_output(slug, path=out)
for f in os.listdir(out):
    print("WROTE", f, os.path.getsize(os.path.join(out, f)))