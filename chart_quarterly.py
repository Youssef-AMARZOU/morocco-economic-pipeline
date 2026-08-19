import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import csv, os

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kaggle_kernel", "out")

years, af, dette, inad = [], [], [], []
with open(os.path.join(OUTDIR, "quarterly_macro_indicators.csv"), encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        y = int(row["year"])
        if y > 2024:
            continue
        years.append(y)
        af.append(float(row["autonomie_financiere"]) if row["autonomie_financiere"] else None)
        dette.append(float(row["dette_publique"]) if row["dette_publique"] else None)
        inad.append(float(row["inad"]) if row["inad"] else None)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [2, 1]})
fig.suptitle("Indicateurs Macro Trimestriels du Maroc (1990-2024)", fontsize=16, fontweight='bold', y=0.98)

# --- Top panel: Autonomie Financiere + Dette Publique (left axis) + INAD (right axis) ---
color_af = '#27ae60'
color_dt = '#2980b9'
color_inad = '#e74c3c'

ax1.plot(years, af, color=color_af, linewidth=2, marker='o', markersize=4, label='Autonomie Financiere (% PIB)', zorder=3)
ax1.plot(years, dette, color=color_dt, linewidth=2, marker='s', markersize=4, label='Dette Publique (% PIB)', zorder=3)
ax1.set_ylabel("Autonomie Financiere / Dette Publique (% PIB)", fontsize=11)
ax1.tick_params(axis='y')
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(min(years) - 1, max(years) + 1)

ax1b = ax1.twinx()
inad_years = [y for y, v in zip(years, inad) if v is not None]
inad_vals = [v for v in inad if v is not None]
ax1b.plot(inad_years, inad_vals, color=color_inad, linewidth=2.5, marker='D', markersize=5,
          label='INAD (Skill Mismatch Index)', zorder=4, linestyle='--')
ax1b.set_ylabel("INAD (indice)", fontsize=11, color=color_inad)
ax1b.tick_params(axis='y', labelcolor=color_inad)
ax1b.legend(loc='upper right', fontsize=10)

# Annotate key events
events = {
    1998: "Reforme\nfiscale",
    2008: "Crise\nmondiale",
    2020: "COVID-19",
}
for yr, txt in events.items():
    if yr in years:
        idx = years.index(yr)
        if inad[idx] is not None:
            ax1b.annotate(txt, xy=(yr, inad[idx]), xytext=(yr + 1.5, inad[idx] + 3),
                         fontsize=8, ha='left', color=color_inad, alpha=0.8,
                         arrowprops=dict(arrowstyle='->', color=color_inad, alpha=0.5))

# --- Bottom panel: evolution of all three normalized ---
import statistics
af_clean = [v for v in af if v is not None]
dette_clean = [v for v in dette if v is not None]
inad_clean = [v for v in inad if v is not None]

mu_af, sd_af = statistics.mean(af_clean), statistics.stdev(af_clean)
mu_dt, sd_dt = statistics.mean(dette_clean), statistics.stdev(dette_clean)
mu_in, sd_in = statistics.mean(inad_clean), statistics.stdev(inad_clean)

af_norm = [(v - mu_af) / sd_af if v is not None else None for v in af]
dt_norm = [(v - mu_dt) / sd_dt if v is not None else None for v in dette]
in_norm = [(v - mu_in) / sd_in if v is not None else None for v in inad]

ax2.plot(years, af_norm, color=color_af, linewidth=1.8, label='Autonomie Financiere (std)')
ax2.plot(years, dt_norm, color=color_dt, linewidth=1.8, label='Dette Publique (std)')
ax2.plot(years, in_norm, color=color_inad, linewidth=1.8, label='INAD (std)', linestyle='--')
ax2.axhline(0, color='gray', linewidth=0.8, linestyle=':')
ax2.set_xlabel("Annee", fontsize=11)
ax2.set_ylabel("Valeur standardisee (z-score)", fontsize=11)
ax2.legend(loc='best', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(min(years) - 1, max(years) + 1)

plt.tight_layout(rect=[0, 0, 1, 0.96])
out_path = os.path.join(OUTDIR, "quarterly_macro_indicators.png")
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Chart saved: {out_path}")
