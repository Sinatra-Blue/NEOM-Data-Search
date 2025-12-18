"""
Build search index from species_mentions_scan.csv

This script takes the output from scan_species_mentions.py and builds
a search index for the web interface.

Usage:
    python build_index.py

Requires species_mentions_scan.csv in the same folder.
"""

import pandas as pd
import numpy as np
import json
from sentence_transformers import SentenceTransformer

# Categories from the scan (must match scan_species_mentions.py)
CATEGORIES = [
    'marine_mammals',
    'sharks_rays', 
    'reptiles',
    'fish',
    'birds',
    'invertebrates_habitat',
    'survey_types',
    'places',
    'data_types',
    'conservation',
]


def build_searchable_text(row):
    """Build a searchable text string from all the metadata."""
    parts = []
    
    # Add filename
    if pd.notna(row.get('file_name')):
        parts.append(f"filename: {row['file_name']}")
    
    # Add file type
    if pd.notna(row.get('file_type')):
        parts.append(f"type: {row['file_type']}")
    
    # Add each category's matches
    for cat in CATEGORIES:
        if pd.notna(row.get(cat)) and row[cat]:
            parts.append(f"{cat}: {row[cat]}")
    
    # Add path keywords (extract folder names)
    if pd.notna(row.get('file_path')):
        path = str(row['file_path']).replace('\\', '/')
        folders = [p for p in path.split('/') if len(p) > 2 and '.' not in p]
        if folders:
            parts.append(f"location: {' '.join(folders[-4:])}")  # Last 4 folders
    
    return " | ".join(parts)


def main():
    print("=" * 60)
    print("Building Search Index")
    print("=" * 60)
    
    # Load the scan results
    print("\nLoading species_mentions_scan.csv...")
    df = pd.read_csv('species_mentions_scan.csv')
    print(f"  Loaded {len(df)} records")
    
    # Filter to successful scans only
    df_success = df[df['status'] == 'success'].copy()
    print(f"  Successful scans: {len(df_success)}")
    
    # Build searchable text for each record
    print("\nBuilding searchable text...")
    df_success['searchable_text'] = df_success.apply(build_searchable_text, axis=1)
    
    # Extract unique values for each category (for filter dropdowns)
    print("\nExtracting filter options...")
    filter_options = {}
    for cat in CATEGORIES:
        all_values = set()
        for val in df_success[cat].dropna():
            if val:
                all_values.update([v.strip() for v in str(val).split(',')])
        filter_options[cat] = sorted(all_values)
        print(f"  {cat}: {len(filter_options[cat])} unique values")
    
    # Build records for JSON
    print("\nBuilding records...")
    records = []
    for _, row in df_success.iterrows():
        record = {
            'file_path': row['file_path'],
            'file_name': row['file_name'],
            'file_type': row['file_type'],
            'searchable_text': row['searchable_text'],
        }
        # Add each category
        for cat in CATEGORIES:
            record[cat] = row[cat] if pd.notna(row[cat]) else ''
        records.append(record)
    
    # Save index JSON
    print(f"\nSaving search_index.json...")
    with open('search_index.json', 'w', encoding='utf-8') as f:
        json.dump({
            'records': records,
            'categories': CATEGORIES,
            'filters': filter_options,
        }, f, indent=2)
    
    # Generate embeddings
    print("\nGenerating embeddings (this may take a minute)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    texts = [r['searchable_text'] for r in records]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    
    np.save('search_embeddings.npy', embeddings.astype('float32'))
    
    print(f"\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print(f"  Records: {len(records)}")
    print(f"  Embeddings shape: {embeddings.shape}")
    print(f"\nFiles created:")
    print(f"  - search_index.json")
    print(f"  - search_embeddings.npy")
    print(f"\nNext: Run 'uvicorn search_service:app --reload' to start the search server")


if __name__ == "__main__":
    main()
