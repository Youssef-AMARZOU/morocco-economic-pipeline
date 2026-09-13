"""UN Comtrade Morocco trade detail: HS chapters (AG2) x partners x years.

Reporter 504 (Morocco), flows M/X, 1990-2024, world + top partners.
Public preview API is capped at 500 rows/request and rate-limited,
so this runs slow with retries (expect ~30-60 min).
Output: economic_data/comtrade_morocco_ag2.csv
"""
import csv
import json
import os
import time
import urllib.request

UA = {"User-Agent": "morocco-economic-pipeline/1.0"}
API = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"

PARTNERS = [0, 32, 40, 56, 76, 156, 208, 224, 276, 380, 392, 400, 410, 428,
            442, 454, 458, 484, 528, 554, 566, 620, 624, 643, 682, 686, 724,
            752, 756, 818, 820, 826, 840, 854, 858, 862, 868]
PARTNERS = sorted(set(PARTNERS))
YEARS = list(range(1990, 2025))
FLOWS = ["M", "X"]


def get(params):
    url = API + "?" + params
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:
            wait = 4 * (attempt + 1)
            print("  retry", attempt, str(e)[:60], f"wait {wait}s")
            time.sleep(wait)
    print("  SKIP:", params[:100])
    return {"data": []}


def main():
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "economic_data")
    os.makedirs(base, exist_ok=True)
    out = os.path.join(base, "comtrade_morocco_ag2.csv")
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add((row["year"], row["flow"], row["partner_code"]))
        print("Resuming, have", len(done), "year-flow-partner combos")
    total = len(YEARS) * len(FLOWS) * len(PARTNERS)
    n = 0
    with open(out, "a" if done else "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not done:
            w.writerow(["year", "flow", "partner_code", "hs_chapter",
                        "trade_value_usd", "net_weight_kg", "qty", "qty_unit"])
        for y in YEARS:
            for fl in FLOWS:
                for p in PARTNERS:
                    n += 1
                    if (str(y), fl, str(p)) in done:
                        continue
                    d = get(f"reporterCode=504&period={y}&flowCode={fl}"
                            f"&partnerCode={p}&cmdCode=AG2&maxRec=500")
                    for r in d.get("data", []):
                        w.writerow([r.get("refYear"), fl, p, r.get("cmdCode"),
                                    r.get("primaryValue"), r.get("netWgt"),
                                    r.get("qty"), r.get("qtyUnitAbbr")])
                    f.flush()
                    if n % 20 == 0:
                        print(f"{n}/{total}")
                    time.sleep(2.5)
    print("Done:", out)


if __name__ == "__main__":
    main()
