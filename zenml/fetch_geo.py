"""Bulk geography downloads for Morocco (large files, gitignored).

- OSM PBF + shapefile (Geofabrik): roads, buildings, landuse, POIs
- Copernicus DEM 30m tiles (AWS eu-central-1): Casablanca, Marrakech, Tangier, Agadir
- GADM v4.1 admin boundaries (SHP + GeoPackage)
Output: economic_data/osm/, economic_data/geo/
"""
import os
import urllib.request

UA = {"User-Agent": "morocco-economic-pipeline/1.0"}

FILES = {
    "osm/morocco-latest.osm.pbf":
        "https://download.geofabrik.de/africa/morocco-latest.osm.pbf",
    "osm/morocco-latest-free.shp.zip":
        "https://download.geofabrik.de/africa/morocco-latest-free.shp.zip",
    "geo/gadm41_MAR_shp.zip":
        "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_MAR_shp.zip",
    "geo/gadm41_MAR.gpkg":
        "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_MAR.gpkg",
}
DEM_TILES = ["N33_00_W008_00", "N31_00_W008_00", "N35_00_W006_00", "N30_00_W010_00"]
for t in DEM_TILES:
    FILES[f"geo/dem/Copernicus_DSM_COG_10_{t}_DEM.tif"] = (
        f"https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/"
        f"Copernicus_DSM_COG_10_{t}_DEM/Copernicus_DSM_COG_10_{t}_DEM.tif")


def dl(url, path):
    if os.path.exists(path):
        print("exists, skip:", path)
        return
    print("downloading:", url.split("/")[-1])
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    print("  done", f"{os.path.getsize(path) / 1e6:.1f} MB")


def main():
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "economic_data")
    for rel, url in FILES.items():
        p = os.path.join(base, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        dl(url, p)


if __name__ == "__main__":
    main()
