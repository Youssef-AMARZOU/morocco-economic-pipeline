"""Extract quarterly GDP from HCP XLSX files."""
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

print("=== Extracting Quarterly GDP from HCP ===")

hcp_dir = r"C:\Users\youss\OneDrive\Desktop\morocco-economic-pipeline\enhanced_data\hcp_raw"

# Find GDP decomposition files
gdp_files = []
for fname in os.listdir(hcp_dir):
    if not fname.endswith('.xlsx'):
        continue
    fpath = os.path.join(hcp_dir, fname)
    try:
        xls = pd.ExcelFile(fpath)
        for sheet in xls.sheet_names:
            df_sheet = pd.read_excel(fpath, sheet_name=sheet, header=None)
            # Check for quarterly GDP data
            text = df_sheet.to_string()
            if any(x in text for x in ['Décomposition du PIB', 'PIB trimestriel', 'trimestrielle']):
                gdp_files.append((fname, sheet, df_sheet))
                print(f"Found GDP file: {fname} / {sheet}")
    except:
        pass

print(f"\nFound {len(gdp_files)} GDP files")

# Parse each GDP file
for fname, sheet, df_sheet in gdp_files:
    print(f"\n--- {fname} ({sheet}) ---")
    print(f"Shape: {df_sheet.shape}")
    # Print first 20 rows to understand structure
    print(df_sheet.head(20).to_string())
    print("...")
