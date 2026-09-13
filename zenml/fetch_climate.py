"""Daily climate history for major Moroccan cities via Open-Meteo (free, no key).

Cities: Casablanca, Rabat, Marrakech, Fes, Tangier, Agadir, Meknes, Oujda,
Kenitra, Tetouan, Laayoune, Dakhla, Errachidia, Ouarzazate, Nador.
Variables: T° max/min/mean, precipitation, wind, 1940-01-01 to yesterday.
Output: economic_data/climate_morocco_cities.csv
"""
import csv
import datetime
import json
import os
import time
import urllib.parse
import urllib.request

CITIES = {
    "Casablanca": (33.5731, -7.5898), "Rabat": (34.0209, -6.8416),
    "Marrakech": (31.6295, -7.9811), "Fes": (34.0181, -5.0078),
    "Tangier": (35.7794, -5.8100), "Agadir": (30.4278, -9.5981),
    "Meknes": (33.8935, -5.5473), "Oujda": (34.6814, -1.9086),
    "Kenitra": (34.2610, -6.5802), "Tetouan": (35.5889, -5.3626),
    "Laayoune": (27.1253, -13.1625), "Dakhla": (23.6848, -15.9579),
    "Errachidia": (31.9311, -4.4247), "Ouarzazate": (30.9335, -6.9370),
    "Nador": (35.1688, -2.9335),
}
VARS = ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
        "precipitation_sum", "wind_speed_10m_max"]
END = datetime.date.today().strftime("%Y-%m-%d")


def fetch(url):
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "morocco-economic-pipeline/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            wait = 10 * (attempt + 1)
            print("  retry", attempt, str(e)[:60], f"wait {wait}s")
            time.sleep(wait)
    raise RuntimeError("failed: " + url[:80])


def main():
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "economic_data")
    os.makedirs(base, exist_ok=True)
    out = os.path.join(base, "climate_morocco_cities.csv")
    decades = [(y, min(y + 9, 2026)) for y in range(1940, 2027, 10)]
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add((row["city"], row["date"][:4]))
        print("Resuming, have", len(done), "city-years")
    with open(out, "a" if done else "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not done:
            w.writerow(["city", "date"] + VARS)
        for city, (lat, lon) in CITIES.items():
            total = 0
            for y0, y1 in decades:
                if all((city, str(y)) in done for y in range(y0, y1 + 1)):
                    continue
                q = urllib.parse.urlencode({
                    "latitude": lat, "longitude": lon,
                    "start_date": f"{y0}-01-01", "end_date": f"{y1}-12-31",
                    "daily": ",".join(VARS), "timezone": "Africa/Casablanca",
                })
                d = fetch("https://archive-api.open-meteo.com/v1/archive?" + q)
                daily, dates = d["daily"], d["daily"]["time"]
                for i, dt in enumerate(dates):
                    w.writerow([city, dt] + [daily[v][i] for v in VARS])
                f.flush()
                total += len(dates)
                time.sleep(3)
            print(city, total, "days")
    print("Wrote:", out)


if __name__ == "__main__":
    main()
