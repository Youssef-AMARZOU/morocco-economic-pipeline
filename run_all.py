"""PIPELINE PRINCIPAL - orchestre toutes les etapes (fetch + ETL + ELT + merge + clean + solve + warehouse).
Usage:
  python run_all.py                 -> pipeline complet : re-fetch toutes les sources live + ETL/ELT
  python run_all.py --no-fetch      -> utilise les donnees deja presentes dans raw/ (pas de re-telechargement)
  python run_all.py --fetch-only    -> ne fait que re-telecharger les sources live
"""
import os, sys, subprocess, argparse, shutil, datetime

ETL = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\youss\OneDrive\Desktop\Morocco_Official_Data"
KAGGLE = os.path.join(SRC, "kaggle_datasets")
PY = sys.executable

STAGES = ["extract", "transform", "load", "merge", "clean", "fetch_solve", "update_warehouse"]
KAGGLE_DATASETS = [
    "mustaphaoutgougua/moroccan-banks-historical-stock-price",
    "kanchana1990/imf-world-economic-outlook-april-2026",
    "madhur321/world-bank-development-indicators-panel",
    "udayraman/world-economic-trends-and-indicators",
]


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run(script, timeout=1800000):
    log(f">>> {script}.py")
    r = subprocess.run([PY, os.path.join(ETL, script + ".py")], cwd=ETL, timeout=timeout)
    if r.returncode != 0:
        log(f"ECHEC {script} (code {r.returncode})")
        raise SystemExit(1)
    log(f"<<< {script} OK")


def fetch_all():
    log("### FETCH World Bank WDI ###")
    wdi = os.path.join(SRC, "morocco_worldbank_wdi.csv")
    if os.path.exists(wdi):
        os.remove(wdi)
    run("fetch_wb")
    run("fetch_wb2")

    log("### FETCH IMF WEO ###")
    imf = os.path.join(SRC, "morocco_imf_weo.csv")
    if os.path.exists(imf):
        os.remove(imf)
    run("fetch_imf2")
    run("fetch_imf4")
    run("fetch_imf5")

    log("### FETCH Kaggle ###")
    for d in KAGGLE_DATASETS:
        name = d.split("/")[-1]
        out = os.path.join(KAGGLE, name)
        if os.path.exists(out):
            shutil.rmtree(out)
        os.makedirs(out, exist_ok=True)
        subprocess.run(["kaggle", "datasets", "download", "-d", d, "-p", out, "--unzip"],
                       cwd=ETL, timeout=600000, check=False)
        log(f"  {d} -> maj")

    log("### FETCH OWID ###")
    owid = os.path.join(ETL, "raw", "owid.csv")
    if os.path.exists(owid):
        os.remove(owid)
    run("fetch_owid")


def pipeline():
    for s in STAGES:
        run(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true", help="utilise raw/ deja present (pas de re-fetch)")
    ap.add_argument("--fetch-only", action="store_true", help="ne fait que re-telecharger les sources")
    args = ap.parse_args()

    if args.fetch_only:
        fetch_all()
        log("FETCH TERMINE")
        return

    if not args.no_fetch:
        fetch_all()

    pipeline()
    log("=== PIPELINE COMPLET TERMINE ===")


if __name__ == "__main__":
    main()