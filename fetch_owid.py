"""FETCH OWID : Notre source complementaire (Our World in Data).
Recupere les indicateurs disponibles pour le Maroc (Code=MAR) et les
ecrit dans raw/owid.csv au format long canonique.
"""
import requests, csv, os, sys
sys.stdout.reconfigure(encoding="utf-8")
import config as C

# Slugs verifies disponibles pour MAR (d'apres sondage)
SLUGS = {
    "literacy-rate": "Taux d'alphabetisation (adultes)",
    "share-of-population-in-extreme-poverty": "Population en pauvrete extreme (%)",
    "child-mortality-rate": "Mortalite infantile (pour 1000)",
    "gross-enrollment-ratio-in-secondary-education": "Scolarisation secondaire brute (%)",
    "life-expectancy-at-birth": "Esperance de vie naissance (ans)",
    "unemployment-rate": "Taux de chomage (%)",
    "population": "Population totale",
    "co2-emissions-per-capita": "Emissions CO2 par habitant (t)",
    "renewable-share-energy": "Part energies renouvelables (%)",
    # --- Slugs additionnels (extension du corpus) ---
    "healthy-life-expectancy": "Esperance de vie en bonne sante (ans)",
    "human-development-index": "Indice de developpement humain (HDI)",
    "share-of-population-with-access-to-electricity": "Acces a l'electricite (%)",
    "road-network-per-capita": "Reseau routier par habitant",
}

out = os.path.join(C.RAW, "owid.csv")
n_total = 0
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["source", "dataset", "code", "name", "entity", "year", "value"])
    for slug, name in SLUGS.items():
        url = f"https://ourworldindata.org/grapher/{slug}.csv"
        try:
            r = requests.get(url, timeout=40, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                print(f"  {slug}: {r.status_code}"); continue
            lines = r.text.strip().split("\n")
            header = lines[0].split(",")
            # colonnes: Entity, Code, Year, <value>
            val_col = header[-1]
            n = 0
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) < 4:
                    continue
                entity, code, year = parts[0], parts[1], parts[2]
                val = parts[3]
                if code != "MAR":
                    continue
                # filtre années aberrants (sentinelles OWID type -10000, futures >2100)
                if not year.lstrip("-").isdigit() or int(year) < 1900 or int(year) > 2100:
                    continue
                try:
                    v = float(val) if val not in ("", "NA", "NaN") else ""
                except ValueError:
                    v = ""
                w.writerow(["OWID", slug, slug, name, "Morocco", year, v])
                n += 1
            print(f"  {slug:48s}: {n} lignes MAR (colonne '{val_col}')")
            n_total += n
        except Exception as e:
            print(f"  {slug}: ERR {e}")
print(f"OWID ecrit: {out} ({n_total} lignes MAR)")