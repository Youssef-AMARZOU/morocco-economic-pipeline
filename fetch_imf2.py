import requests, csv, time, os, sys
sys.stdout.reconfigure(encoding="utf-8")

INDICATORS = {
    "NGDP_RPCH": "Croissance PIB reel (%)",
    "NGDPD": "PIB nominal (M USD)",
    "NGDPDPC": "PIB par habitant (USD)",
    "NGDPRPPPPC": "PIB par habitant PPA (USD)",
    "PPPEX": "Taux de change PPA",
    "PCPIPCH": "Inflation IPC moyenne (%)",
    "PCPIE": "Inflation fin de periode (%)",
    "NGDP_D": "Deflateur PIB (variation %)",
    "LUR": "Taux de chomage (%)",
    "GGR_NGDP": "Recettes publiques (% PIB)",
    "GGX_NGDP": "Depenses publiques (% PIB)",
    "GGXWDG_NGDP": "Dette publique brute (% PIB)",
    "GGXCNL_NGDP": "Solde budgetaire net (% PIB)",
    "BCA_NGDPD": "Balance courante (% PIB)",
    "BCA": "Balance courante (M USD)",
    "BX_GSGNFS": "Exportations biens et services (M USD)",
    "BM_GSGNFS": "Importations biens et services (M USD)",
    "X_NGDPD": "Exportations (% PIB)",
    "M_NGDPD": "Importations (% PIB)",
    "NID_NGDP": "Investissement total (% PIB)",
    "NID_NGDPD": "Formation brute capital fixe (% PIB)",
    "GXD_NGDP": "Investissement public (% PIB)",
    "PXD_NGDP": "Investissement prive (% PIB)",
    "GG_GDP": "Epargne brute publique (% PIB)",
    "GGBP": "Epargne brute privee (% PIB)",
    "NGSD_NGDP": "Epargne brute nationale (% PIB)",
    "LP": "Population totale (millions)",
    "LP_GAP": "Croissance population (%)",
    "PCPI": "Indice des prix a la consommation",
    "NIRL": "Taux court terme (%)",
    "NIRR": "Taux de reescompte (%)",
    "DEP_NGDPD": "Depots bancaires (% PIB)",
    "FIN_DOM_CREDIT_PVT_NGDPD": "Credit secteur prive (% PIB)",
    "NGDP_R": "PIB reel (M devise locale)",
    "NGDP_R_PCH": "Croissance PIB reel (%)",
    "PPA": "Parite de pouvoir d'achat",
    "RER": "Taux de change reel effectif",
    "NGDP_F": "PIB nominal (M devise locale)",
}

outdir = r"C:\Users\youss\OneDrive\Desktop\Morocco_Official_Data"
os.makedirs(outdir, exist_ok=True)

n = 0
with open(os.path.join(outdir, "morocco_imf_weo.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["indicator_code", "indicator_name", "year", "value"])
    for ind, name in INDICATORS.items():
        url = f"https://www.imf.org/external/datamapper/api/v1/{ind}/MAR"
        try:
            r = requests.get(url, timeout=60)
            d = r.json()
            vals = d.get("values", {}).get(ind, {})
            years = vals.get("MAR", {})
            print(f"{ind}: {len(years)} annees")
            for year, val in sorted(years.items()):
                w.writerow([ind, name, year, val])
                n += 1
        except Exception as e:
            print(f"{ind}: ERREUR {e}")
        time.sleep(0.4)

print(f"TOTAL: {n} lignes")