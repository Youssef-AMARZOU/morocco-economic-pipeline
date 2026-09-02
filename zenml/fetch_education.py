"""Fetch real education data from World Bank."""
import requests
import pandas as pd

EDU = {
    'SE.PRM.ENRR': 'primary_enrollment',
    'SE.SEC.ENRR': 'secondary_enrollment',
    'SE.TER.ENRR': 'tertiary_enrollment',
    'SE.XPD.TOTL.GD.ZS': 'education_spending_gdp',
    'SE.ADT.LITR.ZS': 'literacy_rate',
}

years = list(range(1960, 2025))
data = {'year': years}

for code, name in EDU.items():
    try:
        url = f'https://api.worldbank.org/v2/country/MAR/indicator/{code}'
        resp = requests.get(url, params={'format': 'json', 'per_page': 500, 'date': '1960:2024'}, timeout=15)
        json_data = resp.json()
        if len(json_data) > 1 and json_data[1]:
            items = json_data[1]
            vals = {int(i['date']): float(i['value']) for i in items if i['value']}
            data[name] = [vals.get(y) for y in years]
            n = sum(1 for v in data[name] if v is not None)
            print(f'{name}: {n} years ({min(vals.keys())}-{max(vals.keys())})')
        else:
            data[name] = [None] * len(years)
            print(f'{name}: NO DATA')
    except Exception as e:
        data[name] = [None] * len(years)
        print(f'{name}: ERROR ({e})')

df = pd.DataFrame(data)
df.to_csv(r'C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\enhanced_data\education_real.csv', index=False)
print(f'\nSaved: education_real.csv ({df.shape[0]} rows, {df.shape[1]} columns)')
