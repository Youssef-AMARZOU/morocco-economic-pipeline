"""ETAPE 1 - EXTRACT.
Copie tous les CSV source et fichiers bruts Kaggle dans la zone raw/
(figure immutable du pipeline). Genere un manifeste.
"""
import os, shutil, sys, json, hashlib, datetime
sys.stdout.reconfigure(encoding="utf-8")
import config as C

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8192), b""):
            h.update(b)
    return h.hexdigest()

def copy_one(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst

manifest = {"extracted_at": datetime.datetime.now().isoformat(timespec="seconds"), "files": []}

# Sources nommees
for name, src, typ in C.SOURCES:
    if os.path.exists(src):
        dst = os.path.join(C.RAW, name + ".csv")
        copy_one(src, dst)
        manifest["files"].append({"logical": name, "type": typ, "source": src,
                                  "raw": dst, "sha256": sha256(dst), "size": os.path.getsize(dst)})
        print(f"[EXTRACT] {name:14s} -> raw/{name}.csv  ({os.path.getsize(dst)} o)")
    else:
        print(f"[EXTRACT] MANQUANT: {src}")

# Bruts Kaggle (tel quel)
for item in C.RAW_KAGGLE:
    if os.path.isdir(item):
        dst_dir = os.path.join(C.RAW, "kaggle", os.path.basename(item))
        for fp in [f for f in os.listdir(item) if f.lower().endswith(".csv")]:
            d = copy_one(os.path.join(item, fp), os.path.join(dst_dir, fp))
            manifest["files"].append({"logical": "kaggle_" + fp.replace(".csv",""),
                                      "type": "raw_kaggle", "source": os.path.join(item, fp),
                                      "raw": d, "sha256": sha256(d), "size": os.path.getsize(d)})
            print(f"[EXTRACT] kaggle   -> raw/kaggle/{fp}  ({os.path.getsize(d)} o)")
    elif os.path.exists(item):
        name = "kaggle_" + os.path.basename(item).replace(".csv","")
        dst = os.path.join(C.RAW, name + ".csv")
        copy_one(item, dst)
        manifest["files"].append({"logical": name, "type": "raw_kaggle", "source": item,
                                  "raw": dst, "sha256": sha256(dst), "size": os.path.getsize(dst)})
        print(f"[EXTRACT] kaggle   -> raw/{name}.csv  ({os.path.getsize(dst)} o)")

with open(os.path.join(C.RAW, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f"\n[EXTRACT] {len(manifest['files'])} fichiers figures dans raw/ (manifest.json)")
