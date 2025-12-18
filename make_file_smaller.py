"""
Extract dugong sighting data from a File Geodatabase and save to CSV.

Requirements:
    pip install geopandas fiona

Usage:
    1. Change the gdb_path below to point to your .gdb folder
    2. Run: python extract_gdb_to_csv.py
    3. Upload the resulting CSV to Claude
"""

import geopandas as gpd
import fiona
import pandas as pd
from pathlib import Path

# === CONFIGURE THIS ===
gdb_path = r"C:\Users\sw1207\OneDrive - University of Exeter\Desktop\SHAPES DUGONG\83242_20230615_KBD_NEOM_TREP_MSR_CAP_Dugong_IR_Rev01.gdb"  # Change this to your .gdb folder path
output_csv = r"C:\Users\sw1207\OneDrive - University of Exeter\Desktop\SHAPES DUGONG\dugong_data.csv"  # Change this to where you want the CSV saved
# ======================

# List all layers in the geodatabase
print(f"Reading geodatabase: {gdb_path}\n")
layers = fiona.listlayers(gdb_path)
print(f"Found {len(layers)} layers:")
for i, layer in enumerate(layers):
    print(f"  {i+1}. {layer}")

print("\n" + "="*50)
print("Extracting data from each layer...")
print("="*50 + "\n")

all_data = []

for layer in layers:
    try:
        gdf = gpd.read_file(gdb_path, layer=layer)
        print(f"\n--- {layer} ---")
        print(f"  Rows: {len(gdf)}")
        print(f"  Columns: {list(gdf.columns)}")
        
        if len(gdf) == 0:
            continue
        
        # Extract coordinates from geometry
        if 'geometry' in gdf.columns and gdf.geometry is not None:
            # Get centroid for any geometry type (point, polygon, etc.)
            gdf['lat'] = gdf.geometry.centroid.y
            gdf['lon'] = gdf.geometry.centroid.x
        else:
            gdf['lat'] = None
            gdf['lon'] = None
        
        # Add source layer name
        gdf['source_layer'] = layer
        
        # Keep all columns for now - we can filter later
        all_data.append(gdf.drop(columns=['geometry'], errors='ignore'))
        
    except Exception as e:
        print(f"  Error reading {layer}: {e}")

# Combine all data
if all_data:
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n{'='*50}")
    print(f"Total rows extracted: {len(combined)}")
    print(f"Saving to: {output_csv}")
    combined.to_csv(output_csv, index=False)
    print("Done!")
else:
    print("No data extracted!")