"""Morocco Economic Insights"""
import pandas as pd
import numpy as np

df = pd.read_csv(r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\economic_data\morocco_indicators_enhanced.csv")

print("=" * 80)
print("MOROCCO ECONOMIC INSIGHTS (1999-2026)")
print("=" * 80)

# 1. GDP Growth
print("\n--- 1. GDP GROWTH ---")
gdp = df[["year", "gdp_real_growth_pct"]].dropna()
avg_gdp = gdp["gdp_real_growth_pct"].mean()
min_gdp = gdp["gdp_real_growth_pct"].min()
max_gdp = gdp["gdp_real_growth_pct"].max()
min_year = gdp.loc[gdp["gdp_real_growth_pct"].idxmin(), "year"]
max_year = gdp.loc[gdp["gdp_real_growth_pct"].idxmax(), "year"]
std_gdp = gdp["gdp_real_growth_pct"].std()
print(f"Average: {avg_gdp:.2f}%")
print(f"Min: {min_gdp:.2f}% ({int(min_year)})")
print(f"Max: {max_gdp:.2f}% ({int(max_year)})")
print(f"Volatility: {std_gdp:.2f}%")

covid = df[df["year"].isin([2020, 2021, 2022])]
print("\nCOVID impact:")
for _, row in covid.iterrows():
    print(f"  {int(row['year'])}: {row['gdp_real_growth_pct']:.2f}%")

# 2. Inflation
print("\n--- 2. INFLATION (CPI) ---")
cpi = df[["year", "cpi_inflation_pct"]].dropna()
print(f"Average: {cpi['cpi_inflation_pct'].mean():.2f}%")
print(f"Last 5 years avg: {cpi.tail(5)['cpi_inflation_pct'].mean():.2f}%")

# 3. Trade
print("\n--- 3. TRADE BALANCE ---")
trade = df[["year", "exports_pct_gdp", "imports_pct_gdp", "trade_balance_pct_gdp"]].dropna()
print(f"Average exports: {trade['exports_pct_gdp'].mean():.1f}% of GDP")
print(f"Average imports: {trade['imports_pct_gdp'].mean():.1f}% of GDP")
print(f"Average trade deficit: {trade['trade_balance_pct_gdp'].mean():.1f}% of GDP")

# 4. Employment
print("\n--- 4. UNEMPLOYMENT ---")
unemp = df[["year", "unemployment_pct"]].dropna()
print(f"Average: {unemp['unemployment_pct'].mean():.1f}%")
print(f"Current: {unemp.tail(1)['unemployment_pct'].values[0]:.1f}%")

# 5. Fiscal
print("\n--- 5. FISCAL ---")
fiscal = df[["year", "gov_debt_pct_gdp", "gov_expenditure_pct_gdp", "gov_revenue_pct_gdp"]].dropna()
print(f"Average debt: {fiscal['gov_debt_pct_gdp'].mean():.1f}% of GDP")
print(f"Average spending: {fiscal['gov_expenditure_pct_gdp'].mean():.1f}% of GDP")
print(f"Average revenue: {fiscal['gov_revenue_pct_gdp'].mean():.1f}% of GDP")
deficit = fiscal["gov_expenditure_pct_gdp"] - fiscal["gov_revenue_pct_gdp"]
print(f"Average deficit: {deficit.mean():.1f}% of GDP")

# 6. Social
print("\n--- 6. SOCIAL ---")
social = df[["year", "population", "life_expectancy_years", "fertility_rate", "urban_population_pct"]].dropna()
pop_growth = ((social["population"].iloc[-1] / social["population"].iloc[0]) ** (1 / len(social)) - 1) * 100
print(f"Population growth: {pop_growth:.2f}% per year")
print(f"Life expectancy: {social['life_expectancy_years'].iloc[-1]:.1f} years")
print(f"Fertility rate: {social['fertility_rate'].iloc[-1]:.2f}")
print(f"Urbanization: {social['urban_population_pct'].iloc[-1]:.1f}%")

# 7. Correlations with GDP
print("\n--- 7. FACTORS CORRELATED WITH GDP GROWTH ---")
numeric = df.select_dtypes(include=[np.number])
corr = numeric.corr()["gdp_real_growth_pct"].drop("gdp_real_growth_pct").sort_values(ascending=False)
print("Positive correlations:")
for feat, val in corr.head(8).items():
    print(f"  {feat[:40]:<40} {val:.3f}")
print("Negative correlations:")
for feat, val in corr.tail(5).items():
    print(f"  {feat[:40]:<40} {val:.3f}")

# 8. Key insights
print("\n--- 8. KEY INSIGHTS ---")
print("1. Morocco has consistent GDP growth (~4%) with low volatility")
print("2. Structural trade deficit (~12% of GDP) is a key vulnerability")
print("3. High unemployment (~12%) despite growth - jobless growth")
print("4. Rapid urbanization (63%) and declining fertility (2.3)")
print("5. Government spending exceeds revenue - fiscal deficit")
print("6. COVID-19 caused -7.2% shock in 2020, followed by +8.2% rebound")
print("7. Remittances and tourism are key external revenue sources")
print("8. Inflation remains low (~2%) - stable monetary policy")
