"""Bulk WDI Morocco slice via the official WDI_CSV.zip (reliable, one download).

Downloads https://databankfiles.worldbank.org/public/ddpext_download/WDI_CSV.zip,
extracts WDIData.csv, keeps Country Code == MAR rows only.
Output: economic_data/wdi_morocco_full.csv (wide format, one row per indicator).
"""
import csv
import os
import urllib.request
import zipfile

UA = {"User-Agent": "morocco-economic-pipeline/1.0"}
URL = "https://databankfiles.worldbank.org/public/ddpext_download/WDI_CSV.zip"


def main():
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "economic_data")
    os.makedirs(base, exist_ok=True)
    zpath = os.path.join(base, "_WDI_CSV.zip")
    if not os.path.exists(zpath):
        print("Downloading WDI_CSV.zip (~280MB)...")
        req = urllib.request.Request(URL, headers=UA)
        with urllib.request.urlopen(req, timeout=120) as r, open(zpath, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        print("Download done.")
    with zipfile.ZipFile(zpath) as z:
        names = [n for n in z.namelist() if n.lower() in ("wdidata.csv", "wdicsv.csv")]
        print("Archive members:", [n for n in z.namelist()][:8])
        src = names[0]
        print("Reading:", src)
        with z.open(src) as fh:
            import io
            text = io.TextIOWrapper(fh, encoding="utf-8-sig")
            reader = csv.DictReader(text)
            mar_rows = [row for row in reader if row.get("Country Code") == "MAR"]
    print("Morocco rows:", len(mar_rows))
    out = os.path.join(base, "wdi_morocco_full.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=reader.fieldnames)
        w.writeheader()
        w.writerows(mar_rows)
    print("Wrote:", out, f"{os.path.getsize(out) / 1e6:.1f} MB")
    os.remove(zpath)
    print("Removed bulk zip (kept Morocco slice only).")


if __name__ == "__main__":
    main()
