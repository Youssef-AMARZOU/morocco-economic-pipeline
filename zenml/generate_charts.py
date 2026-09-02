"""Generate charts from real data."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = '#f8f9fa'
plt.rcParams['axes.edgecolor'] = '#dee2e6'
plt.rcParams['grid.alpha'] = 0.3

df = pd.read_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\morocco_real_data.csv")

output_dir = r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\charts"
import os
os.makedirs(output_dir, exist_ok=True)

# === 1. GDP Growth ===
fig, ax = plt.subplots(figsize=(12, 6))
years = df['year']
gdp = df['gdp_growth']
colors = ['green' if g >= 0 else 'red' for g in gdp]
ax.bar(years, gdp, color=colors, alpha=0.7, edgecolor='white', linewidth=0.5)
ax.axhline(y=gdp.mean(), color='blue', linestyle='--', alpha=0.7, label=f'Mean: {gdp.mean():.2f}%')
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('GDP Growth (%)', fontsize=12)
ax.set_title('Morocco GDP Growth (1999-2026)', fontsize=14, fontweight='bold')
ax.legend()
ax.set_xlim(years.min()-0.5, years.max()+0.5)
plt.tight_layout()
plt.savefig(f'{output_dir}/01_gdp_growth.png', dpi=300, bbox_inches='tight')
plt.close()

# === 2. Inflation ===
fig, ax = plt.subplots(figsize=(12, 6))
cpi = df['cpi_inflation']
ax.plot(years, cpi, color='orange', linewidth=2, marker='o', markersize=4)
ax.fill_between(years, cpi, alpha=0.3, color='orange')
ax.axhline(y=2, color='red', linestyle='--', alpha=0.7, label='Target: 2%')
ax.axhline(y=cpi.mean(), color='blue', linestyle='--', alpha=0.7, label=f'Mean: {cpi.mean():.2f}%')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Inflation (%)', fontsize=12)
ax.set_title('Morocco Inflation (CPI) (1999-2026)', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(f'{output_dir}/02_inflation.png', dpi=300, bbox_inches='tight')
plt.close()

# === 3. Trade Balance ===
fig, ax = plt.subplots(figsize=(12, 6))
exports = df['exports_pct']
imports = df['imports_pct']
trade = df['trade_balance']
x = np.arange(len(years))
width = 0.35
ax.bar(x - width/2, exports, width, label='Exports', color='green', alpha=0.7)
ax.bar(x + width/2, imports, width, label='Imports', color='red', alpha=0.7)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('% of GDP', fontsize=12)
ax.set_title('Morocco Trade Balance (1999-2026)', fontsize=14, fontweight='bold')
ax.set_xticks(x[::2])
ax.set_xticklabels(years[::2], rotation=45)
ax.legend()
plt.tight_layout()
plt.savefig(f'{output_dir}/03_trade.png', dpi=300, bbox_inches='tight')
plt.close()

# === 4. Unemployment ===
fig, ax = plt.subplots(figsize=(12, 6))
unemp = df['unemployment']
ax.plot(years, unemp, color='red', linewidth=2, marker='s', markersize=4)
ax.fill_between(years, unemp, alpha=0.3, color='red')
ax.axhline(y=unemp.mean(), color='blue', linestyle='--', alpha=0.7, label=f'Mean: {unemp.mean():.2f}%')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Unemployment (%)', fontsize=12)
ax.set_title('Morocco Unemployment (1999-2026)', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(f'{output_dir}/04_unemployment.png', dpi=300, bbox_inches='tight')
plt.close()

# === 5. Population ===
fig, ax = plt.subplots(figsize=(12, 6))
pop = df['population'] / 1e6
ax.plot(years, pop, color='blue', linewidth=2, marker='o', markersize=4)
ax.fill_between(years, pop, alpha=0.3, color='blue')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Population (Millions)', fontsize=12)
ax.set_title('Morocco Population (1999-2026)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{output_dir}/05_population.png', dpi=300, bbox_inches='tight')
plt.close()

# === 6. Government Finance ===
fig, ax = plt.subplots(figsize=(12, 6))
debt = df['gov_debt']
spending = df['gov_spending']
revenue = df['gov_revenue']
ax.plot(years, debt, color='red', linewidth=2, label='Debt', marker='o', markersize=4)
ax.plot(years, spending, color='orange', linewidth=2, label='Spending', marker='s', markersize=4)
ax.plot(years, revenue, color='green', linewidth=2, label='Revenue', marker='^', markersize=4)
ax.axhline(y=60, color='red', linestyle='--', alpha=0.5, label='Debt Threshold: 60%')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('% of GDP', fontsize=12)
ax.set_title('Morocco Government Finance (1999-2026)', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(f'{output_dir}/06_fiscal.png', dpi=300, bbox_inches='tight')
plt.close()

# === 7. Actual vs Predicted ===
fig, ax = plt.subplots(figsize=(12, 6))
# Use the best model results
test_years = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
actual = [-7.18, 8.15, 1.81, 3.66, 3.79, 4.60, 4.60]
predicted = [0.89, 5.00, 4.82, 4.19, 2.53, 2.87, 2.88]

x = np.arange(len(test_years))
width = 0.35
ax.bar(x - width/2, actual, width, label='Actual', color='blue', alpha=0.7)
ax.bar(x + width/2, predicted, width, label='Predicted', color='orange', alpha=0.7)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('GDP Growth (%)', fontsize=12)
ax.set_title('Actual vs Predicted GDP Growth (SVR_linear, R2=0.33)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(test_years)
ax.legend()
plt.tight_layout()
plt.savefig(f'{output_dir}/07_actual_vs_predicted.png', dpi=300, bbox_inches='tight')
plt.close()

# === 8. Correlation Heatmap ===
fig, ax = plt.subplots(figsize=(14, 10))
numeric = df.select_dtypes(include=[np.number])
corr_cols = ['gdp_growth', 'cpi_inflation', 'unemployment', 'exports_pct', 'imports_pct',
             'trade_balance', 'current_account', 'gov_debt', 'gov_spending', 'gov_revenue',
             'fdi_pct', 'remittances_pct', 'population', 'urban_pct', 'internet_pct']
corr_cols = [c for c in corr_cols if c in numeric.columns]
corr = numeric[corr_cols].corr()

im = ax.imshow(corr, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
ax.set_xticks(range(len(corr_cols)))
ax.set_yticks(range(len(corr_cols)))
ax.set_xticklabels([c.replace('_', ' ').title()[:20] for c in corr_cols], rotation=45, ha='right', fontsize=8)
ax.set_yticklabels([c.replace('_', ' ').title()[:20] for c in corr_cols], fontsize=8)

for i in range(len(corr_cols)):
    for j in range(len(corr_cols)):
        text = ax.text(j, i, f'{corr.iloc[i, j]:.2f}', ha='center', va='center', fontsize=6)

plt.colorbar(im, ax=ax, label='Correlation')
ax.set_title('Morocco Economic Indicators Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{output_dir}/08_correlation.png', dpi=300, bbox_inches='tight')
plt.close()

# === 9. Key Insights Dashboard ===
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# GDP growth trend
ax = axes[0, 0]
ax.plot(years, gdp, color='blue', linewidth=2, marker='o', markersize=4)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.axhline(y=gdp.mean(), color='red', linestyle='--', alpha=0.7)
ax.set_title('GDP Growth Trend', fontweight='bold')
ax.set_ylabel('%')

# Trade deficit
ax = axes[0, 1]
ax.bar(years, trade, color=['red' if t < 0 else 'green' for t in trade], alpha=0.7)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_title('Trade Balance (% GDP)', fontweight='bold')
ax.set_ylabel('%')

# Unemployment trend
ax = axes[1, 0]
ax.plot(years, unemp, color='red', linewidth=2, marker='s', markersize=4)
ax.set_title('Unemployment Rate', fontweight='bold')
ax.set_ylabel('%')

# Population growth
ax = axes[1, 1]
ax.plot(years, pop, color='green', linewidth=2, marker='o', markersize=4)
ax.set_title('Population (Millions)', fontweight='bold')
ax.set_ylabel('M')

plt.suptitle('Morocco Economic Dashboard (1999-2026)', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{output_dir}/09_dashboard.png', dpi=300, bbox_inches='tight')
plt.close()

# === 10. Model Performance ===
fig, ax = plt.subplots(figsize=(10, 8))
models = ['Ridge', 'Lasso', 'ElasticNet', 'Random Forest', 'GBM', 'SVR (linear)', 'SVR (RBF)']
r2_scores = [0.20, 0.15, 0.18, 0.12, 0.15, 0.33, 0.25]
colors = ['blue' if r2 > 0 else 'red' for r2 in r2_scores]
bars = ax.barh(models, r2_scores, color=colors, alpha=0.7)
ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
ax.axvline(x=0.4, color='green', linestyle='--', alpha=0.7, label='Target: R2=0.40')
ax.set_xlabel('R2 Score', fontsize=12)
ax.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
ax.legend()

# Add value labels
for bar, r2 in zip(bars, r2_scores):
    ax.text(r2 + 0.01, bar.get_y() + bar.get_height()/2, f'{r2:.2f}', va='center', fontsize=10)

plt.tight_layout()
plt.savefig(f'{output_dir}/10_model_performance.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"Saved 10 charts to {output_dir}")
print("DONE")
