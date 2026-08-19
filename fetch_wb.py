import requests, csv, time, os, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://api.worldbank.org/v2/country/MA/indicator/{ind}?format=json&per_page=200&page={page}"

INDICATORS = {
    "NY.GDP.MKTP.CD": "PIB (USD courants)",
    "NY.GDP.MKTP.KD.ZG": "Croissance PIB (% annuel)",
    "NY.GDP.PCAP.CD": "PIB par habitant (USD courants)",
    "NY.GDP.PCAP.KD.ZG": "Croissance PIB par habitant (%)",
    "FP.CPI.TOTL.ZG": "Inflation CPI (% annuel)",
    "NY.GDP.DEFL.KD.ZG": "Déflateur PIB (%)",
    "SL.UEM.TOTL.ZS": "Taux de chômage (% population active)",
    "SL.UEM.TOTL.MA.ZS": "Chômage hommes (%)",
    "SL.UEM.TOTL.FE.ZS": "Chômage femmes (%)",
    "GC.XPN.TOTL.GD.ZS": "Dépenses publiques (% PIB)",
    "GC.REV.XGRT.GD.ZS": "Recettes publiques (% PIB)",
    "GC.DOD.TOTL.GD.ZS": "Dette publique (% PIB)",
    "GC.BAL.CASH.GD.ZS": "Solde budgétaire (% PIB)",
    "BN.CAB.XOKA.GD.ZS": "Balance courante (% PIB)",
    "BN.CAB.XOKA.CD": "Balance courante (USD)",
    "BX.KLT.DINV.CD.WD": "IDE entrants (USD)",
    "NE.EXP.GNFS.CD": "Exportations biens et services (USD)",
    "NE.IMP.GNFS.CD": "Importations biens et services (USD)",
    "NE.TRD.GNFS.ZS": "Commerce extérieur (% PIB)",
    "SP.POP.TOTL": "Population totale",
    "SP.POP.TOTL.FE.ZS": "Population féminine (%)",
    "SP.POP.1564.TO.ZS": "Population 15-64 ans (%)",
    "SP.POP.65UP.TO.ZS": "Population 65+ (%)",
    "SP.URB.TOTL.IN.ZS": "Population urbaine (%)",
    "NY.GNP.PCAP.CD": "RNB par habitant (USD)",
    "NY.GDP.MKTP.KD": "PIB (USD constants 2015)",
    "SI.POV.GINI": "Indice de Gini",
    "AG.AGR.TRAC.NO": "Tracteurs agricoles",
    "AG.LND.AGRI.ZS": "Terres agricoles (% superficie)",
    "EN.ATM.CO2E.PC": "Émissions CO2 par habitant",
    "EG.USE.ELEC.KH.PC": "Consommation électricité/habitant",
    "IT.NET.USER.ZS": "Utilisateurs Internet (%)",
    "IT.NET.BBND.P2": "Abonnements haut débit/100",
    "NY.GSR.NFCY.CD": "Épargne brute (USD)",
    "BX.TRF.CURR.CD": "Transferts courants reçus (USD)",
    "BX.PWF.TOTL.CD.WD": "Envois de fonds reçus (USD)",
    "SL.AGR.EMPL.ZS": "Emploi agriculture (%)",
    "SL.IND.EMPL.ZS": "Emploi industrie (%)",
    "SL.SRV.EMPL.ZS": "Emploi services (%)",
    "SL.TLF.TOTL.FE.ZS": "Femmes dans la population active (%)",
    "SE.XPD.TOTL.GD.ZS": "Dépenses éducation (% PIB)",
    "SH.XPD.CHEX.GD.ZS": "Dépenses santé (% PIB)",
    "MS.MIL.XPND.GD.ZS": "Dépenses militaires (% PIB)",
    "DT.DOD.DECT.GN.ZS": "Dette extérieure (% RNB)",
    "DT.DOD.DECT.CD": "Dette extérieure totale (USD)",
    "FR.INR.RINR": "Taux d'intérêt réel (%)",
    "FR.INR.LEND": "Taux prêt (%)",
    "FS.AST.PRVT.GD.ZS": "Crédit secteur privé (% PIB)",
    "FM.LBL.BMNY.ZG": "Croissance masse monétaire (%)",
    "FB.AST.NPER.ZS": "Actifs bancaires non performants (%)",
    "PA.NUS.FCRF": "Taux de change (unité USD)",
    "PA.NUS.FCRF.XD": "Taux de change effectif",
    "NV.AGR.TOTL.ZS": "Agriculture (% PIB)",
    "NV.IND.TOTL.ZS": "Industrie (% PIB)",
    "NV.SRV.TOTL.ZS": "Services (% PIB)",
    "NV.IND.MANF.ZS": "Manufacture (% PIB)",
    "BX.CUR.DIS.CD": "Exportations (USD)",
    "BM.CUR.DIS.CD": "Importations (USD)",
    "ST.INT.ARVL": "Arrivées touristiques",
    "ST.INT.DPRT": "Départs touristiques",
    "ST.INT.TVLR.CD": "Recettes touristiques (USD)",
    # --- Indicateurs additionnels (extension du corpus) ---
    "SI.POV.DDAY": "Pauvrete extreme <2.15$/jour (%)",
    "SI.POV.NAHC": "Pauvrete nationale (% population)",
    "SP.DYN.LE00.IN": "Esperance de vie naissance (ans)",
    "SP.DYN.IMRT.IN": "Mortalite infantile (pour 1000 naissances)",
    "SP.DYN.TFRT.IN": "Indice de fecondite (enfants/femme)",
    "SE.PRM.NENR": "Scolarisation primaire nette (%)",
    "SE.SEC.NENR": "Scolarisation secondaire nette (%)",
    "EG.USE.PCAP.KG.OE": "Consommation energie/habitant (kg eq petrole)",
    "EG.FEC.RNEW.ZS": "Energie renouvelable (% consommation)",
    "TT.PRI.MRCH.XD": "Termes de l'echange (indice 2010=100)",
    "FX.RES.TOTL.CD": "Reserves de changes totales (USD)",
    "AG.LND.FRST.ZS": "Superficie forestiere (% terres)",
    "SL.TLF.ACTI.ZS": "Taux d'activite (% pop 15+)",
    "NY.ADJ.AEDU.GN.ZS": "Depenses educatives ajustees (% PIB)",
    "SH.IMM.I109.MCV": "Couverture vaccinale RRO triple (%, <12 mois)",
    "EN.POP.SLUM.UR.ZS": "Population urbaine en bidonvilles (%)",
    "EG.ELC.ACCS.ZS": "Acces a l'electricite (% population)",
    "SP.DYN.CBRT.IN": "Taux de natalite (pour 1000)",
    "SP.DYN.CDRT.IN": "Taux de mortalite (pour 1000)",
}

def fetch_indicator(ind, name):
    rows = []
    page = 1
    while True:
        url = BASE.format(ind=ind, page=page)
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            break
        data = r.json()
        if len(data) < 2 or not data[1]:
            break
        for rec in data[1]:
            rows.append((rec["date"], rec["value"]))
        total = data[0]["total"]
        per = data[0]["per_page"]
        if page * per >= total:
            break
        page += 1
        time.sleep(0.3)
    return rows

outdir = r"C:\Users\youss\OneDrive\Desktop\Morocco_Official_Data"
os.makedirs(outdir, exist_ok=True)

all_rows = []
with open(os.path.join(outdir, "morocco_worldbank_wdi.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["indicator_code", "indicator_name", "year", "value"])
    for ind, name in INDICATORS.items():
        try:
            rows = fetch_indicator(ind, name)
            print(f"{ind}: {len(rows)} années")
            for year, val in rows:
                w.writerow([ind, name, year, val])
                all_rows.append((ind, name, year, val))
        except Exception as e:
            print(f"{ind}: ERROR {e}")
        time.sleep(0.3)

print(f"TOTAL LIGNES: {len(all_rows)}")
print(f"Fichier créé: {outdir}\\morocco_worldbank_wdi.csv")