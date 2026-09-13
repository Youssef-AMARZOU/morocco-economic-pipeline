"""Fetch Morocco (Q1028) time-series data from the Wikidata API.

Properties extracted (only statements with point-in-time qualifiers):
  P1082  population
  P1081  Human Development Index
  P2250  life expectancy (years)
  P2131  nominal GDP (USD)
  P1198  unemployment rate (%)
  P1538  number of households
  P1539  female population
  P1540  male population

Output: economic_data/wikidata_morocco.csv + economic_data/wikidata_metadata.json
No interpolation - missing years stay empty.
"""
import csv
import datetime
import json
import os
import urllib.parse
import urllib.request

UA = {"User-Agent": "morocco-economic-pipeline/1.0 (github.com/Youssef-AMARZOU/morocco-economic-pipeline)"}
API = "https://www.wikidata.org/w/api.php"


PROPS = ["P1082", "P1081", "P2250", "P2131", "P1198", "P1538", "P1539", "P1540"]


def main():
    params = {
        "action": "wbgetentities",
        "ids": "Q1028",
        "format": "json",
        "props": "claims",
        "formatversion": "2",
    }
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    claims = data["entities"]["Q1028"]["claims"]

    # Resolve human-readable labels for properties and units used.
    label_ids = set(PROPS)
    for pid in PROPS:
        for s in claims.get(pid, []):
            mv = (s.get("mainsnak") or {}).get("datavalue", {}).get("value", {})
            if isinstance(mv, dict) and str(mv.get("unit", "1")) != "1":
                label_ids.add(mv["unit"].split("/")[-1])
    lab_req = urllib.request.Request(
        API + "?" + urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(sorted(label_ids)),
            "format": "json", "props": "labels", "languages": "en", "formatversion": "2",
        }), headers=UA)
    with urllib.request.urlopen(lab_req, timeout=60) as r:
        lab_data = json.load(r)
    labels = {
        eid: ent.get("labels", {}).get("en", {}).get("value", eid)
        for eid, ent in lab_data.get("entities", {}).items()
    }
    print("Property labels:", {p: labels.get(p, p) for p in PROPS})

    # Short stable column names.
    colmap = {
        "P1082": "population",
        "P1081": "hdi",
        "P2250": "life_expectancy_years",
        "P2131": "gdp_nominal_usd",
        "P1198": "unemployment_rate_pct",
        "P1538": "households",
        "P1539": "female_population",
        "P1540": "male_population",
    }

    rows = {}  # year -> {col: value}
    meta_units = {}
    for pid in PROPS:
        col = colmap[pid]
        for s in claims.get(pid, []):
            mv = (s.get("mainsnak") or {}).get("datavalue", {}).get("value", {})
            if not isinstance(mv, dict) or "amount" not in mv:
                continue
            quals = s.get("qualifiers") or {}
            times = quals.get("P585", [])
            if not times:
                continue
            t = ((times[0].get("datavalue") or {}).get("value") or {}).get("time", "")
            if len(t) < 5 or not t[1:5].isdigit():
                continue
            year = int(t[1:5])
            try:
                val = float(mv["amount"])
            except (TypeError, ValueError):
                continue
            unit = str(mv.get("unit", "1"))
            unit_qid = unit.split("/")[-1] if unit != "1" else "1"
            meta_units[col] = labels.get(unit_qid, unit_qid) if unit_qid != "1" else "count"
            # Prefer 'preferred' rank on clashes, else keep first seen.
            cell = rows.setdefault(year, {})
            if col not in cell or s.get("rank") == "preferred":
                cell[col] = val

    years = sorted(rows)
    cols = ["year"] + [colmap[p] for p in PROPS]
    print(f"Years covered: {years[0]}-{years[-1]} ({len(years)} rows)")

    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "economic_data")
    os.makedirs(base, exist_ok=True)
    csv_path = os.path.join(base, "wikidata_morocco.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for y in years:
            w.writerow({"year": y, **{c: rows[y].get(c, "") for c in cols[1:]}})

    meta = {
        "entity": "Q1028",
        "entity_url": "https://www.wikidata.org/wiki/Q1028",
        "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "columns": {
            colmap[p]: {"wikidata_property": p, "label": labels.get(p, p),
                        "unit": meta_units.get(colmap[p], "")}
            for p in PROPS
        },
        "note": "Real Wikidata statements only; missing years are empty (no interpolation).",
    }
    with open(os.path.join(base, "wikidata_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print("Wrote:", csv_path)


if __name__ == "__main__":
    main()
