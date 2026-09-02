"""Generate charts with REAL data - no fake flat lines."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = '#f8f9fa'

# Load real data
df = pd.read_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\enhanced_data\education_real.csv")
df_indicators = pd.read_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\enhanced_data\morocco_real_data.csv")

output_dir = r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\enhanced_data\charts_real"
os.makedirs(output_dir, exist_ok=True)

# === 1. Education Enrollment (REAL) ===
fig, ax = plt.subplots(figsize=(12, 6))
years_edu = df['year']
primary = df['primary_enrollment']
secondary = df['secondary_enrollment']
tertiary = df['tertiary_enrollment']

ax.plot(years_edu, primary, color='blue', linewidth=2, marker='o', markersize=3, label='Primaire')
ax.plot(years_edu, secondary, color='green', linewidth=2, marker='s', markersize=3, label='Secondaire')
ax.plot(years_edu, tertiary, color='red', linewidth=2, marker='^', markersize=3, label='Superieur')
ax.axhline(y=100, color='black', linestyle='--', alpha=0.3, label='100%')
ax.fill_between(years_edu, primary, alpha=0.1, color='blue')
ax.fill_between(years_edu, secondary, alpha=0.1, color='green')
ax.set_xlabel('Annee', fontsize=12)
ax.set_ylabel('%', fontsize=12)
ax.set_title("Taux de Scolarisation au Maroc (1971-2024) - Donnees Reelles", fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.set_xlim(1970, 2025)
plt.tight_layout()
plt.savefig(f'{output_dir}/01_education_real.png', dpi=300, bbox_inches='tight')
plt.close()

# === 2. Education Spending (REAL) ===
fig, ax = plt.subplots(figsize=(12, 6))
edu_spend = df['education_spending_gdp'].dropna()
ax.plot(edu_spend.index + 1973, edu_spend.values, color='purple', linewidth=2, marker='o', markersize=4)
ax.fill_between(edu_spend.index + 1973, edu_spend.values, alpha=0.3, color='purple')
ax.set_xlabel('Annee', fontsize=12)
ax.set_ylabel('% du PIB', fontsize=12)
ax.set_title("Depenses d'Education (% PIB) - Donnees Reelles", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{output_dir}/02_education_spending_real.png', dpi=300, bbox_inches='tight')
plt.close()

# === 3. GDP Growth (REAL) ===
fig, ax = plt.subplots(figsize=(12, 6))
years = df_indicators['year']
gdp = df_indicators['gdp_growth']
colors = ['green' if g >= 0 else 'red' for g in gdp]
ax.bar(years, gdp, color=colors, alpha=0.7, edgecolor='white', linewidth=0.5)
ax.axhline(y=gdp.mean(), color='blue', linestyle='--', alpha=0.7, label=f'Moyenne: {gdp.mean():.2f}%')
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_xlabel('Annee', fontsize=12)
ax.set_ylabel('Croissance PIB (%)', fontsize=12)
ax.set_title('Croissance du PIB au Maroc (1999-2026) - Donnees Reelles', fontsize=14, fontweight='bold')
ax.legend()
ax.set_xlim(years.min()-0.5, years.max()+0.5)
plt.tight_layout()
plt.savefig(f'{output_dir}/03_gdp_real.png', dpi=300, bbox_inches='tight')
plt.close()

# === 4. Unemployment (REAL) ===
fig, ax = plt.subplots(figsize=(12, 6))
unemp = df_indicators['unemployment']
ax.plot(years, unemp, color='red', linewidth=2, marker='s', markersize=4)
ax.fill_between(years, unemp, alpha=0.3, color='red')
ax.axhline(y=unemp.mean(), color='blue', linestyle='--', alpha=0.7, label=f'Moyenne: {unemp.mean():.2f}%')
ax.set_xlabel('Annee', fontsize=12)
ax.set_ylabel('Chomage (%)', fontsize=12)
ax.set_title('Chomage au Maroc (1999-2026) - Donnees Reelles', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(f'{output_dir}/04_unemployment_real.png', dpi=300, bbox_inches='tight')
plt.close()

# === 5. Inflation (REAL) ===
fig, ax = plt.subplots(figsize=(12, 6))
cpi = df_indicators['cpi_inflation']
ax.plot(years, cpi, color='orange', linewidth=2, marker='o', markersize=4)
ax.fill_between(years, cpi, alpha=0.3, color='orange')
ax.axhline(y=2, color='red', linestyle='--', alpha=0.7, label='Objectif: 2%')
ax.axhline(y=cpi.mean(), color='blue', linestyle='--', alpha=0.7, label=f'Moyenne: {cpi.mean():.2f}%')
ax.set_xlabel('Annee', fontsize=12)
ax.set_ylabel('Inflation (%)', fontsize=12)
ax.set_title('Inflation au Maroc (1999-2026) - Donnees Reelles', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(f'{output_dir}/05_inflation_real.png', dpi=300, bbox_inches='tight')
plt.close()

# === 6. Trade Balance (REAL) ===
fig, ax = plt.subplots(figsize=(12, 6))
exports = df_indicators['exports_pct']
imports = df_indicators['imports_pct']
trade = df_indicators['trade_balance']
ax.bar(years, trade, color=['red' if t < 0 else 'green' for t in trade], alpha=0.7)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_xlabel('Annee', fontsize=12)
ax.set_ylabel('% du PIB', fontsize=12)
ax.set_title('Balance Commerciale du Maroc (1999-2026) - Donnees Reelles', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{output_dir}/06_trade_real.png', dpi=300, bbox_inches='tight')
plt.close()

# === 7. Dashboard ===
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

ax = axes[0, 0]
ax.plot(years, gdp, color='blue', linewidth=2, marker='o', markersize=4)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_title('Croissance PIB', fontweight='bold')
ax.set_ylabel('%')

ax = axes[0, 1]
ax.bar(years, trade, color=['red' if t < 0 else 'green' for t in trade], alpha=0.7)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_title('Balance Commerciale (% PIB)', fontweight='bold')
ax.set_ylabel('%')

ax = axes[1, 0]
ax.plot(years, unemp, color='red', linewidth=2, marker='s', markersize=4)
ax.set_title('Chomage', fontweight='bold')
ax.set_ylabel('%')

ax = axes[1, 1]
ax.plot(years, cpi, color='orange', linewidth=2, marker='o', markersize=4)
ax.set_title('Inflation', fontweight='bold')
ax.set_ylabel('%')

plt.suptitle('Tableau de Bord Economique du Maroc (1999-2026) - Donnees Reelles', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{output_dir}/07_dashboard_real.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"Saved 7 charts to {output_dir}")
print("DONE")
