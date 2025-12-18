"""
Prepare unified search index from NEOM metadata files.

This script:
1. Loads all metadata CSVs (csv_xlsx, gdb, shp, images)
2. Creates a unified record format with searchable text
3. Generates embeddings for semantic search
4. Saves the index for the search service
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

def clean_text(val):
    """Convert value to clean string, handling NaN and None."""
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()

def build_searchable_text(record):
    """
    Build a weighted searchable text string from record fields.
    Important fields are repeated to give them more weight in embeddings.
    """
    parts = []
    
    # High weight: filename/layer name (repeat 3x)
    name = record.get('name', '')
    if name:
        parts.extend([name] * 3)
    
    # High weight: species (repeat 2x)
    species = record.get('species', '')
    if species:
        parts.extend([species] * 2)
    
    # Medium weight: activity type
    activity = record.get('activity', '')
    if activity:
        parts.append(activity)
    
    # Medium weight: filename tokens (already tokenised)
    tokens = record.get('filename_tokens', '')
    if tokens:
        parts.append(tokens)
    
    # Lower weight: field/column names
    fields = record.get('fields', '')
    if fields:
        parts.append(fields)
    
    # Context: file path keywords
    path = record.get('path', '')
    if path:
        # Extract meaningful path segments
        path_parts = path.replace('\\', '/').split('/')
        meaningful = [p for p in path_parts if p and not p.startswith('.') and ':' not in p]
        parts.append(' '.join(meaningful[-4:]))  # Last 4 path segments
    
    return ' '.join(parts)

def process_csv_xlsx(filepath):
    """Process CSV/XLSX metadata file."""
    df = pd.read_csv(filepath)
    records = []
    
    for _, row in df.iterrows():
        record = {
            'type': 'table',
            'subtype': clean_text(row.get('file_extension', '')).replace('.', ''),
            'path': clean_text(row.get('file_path', '')),
            'name': clean_text(row.get('file_name', '')),
            'species': clean_text(row.get('Species', '')),
            'activity': clean_text(row.get('activity', '')),
            'filename_tokens': clean_text(row.get('filename_tokens', '')),
            'fields': clean_text(row.get('column_names', '')),
            'status': clean_text(row.get('status', '')),
            'row_count': row.get('row_count') if pd.notna(row.get('row_count')) else None,
            'file_size_mb': row.get('file_size_mb') if pd.notna(row.get('file_size_mb')) else None,
            'min_date': clean_text(row.get('min_date', '')),
            'max_date': clean_text(row.get('max_date', '')),
        }
        record['searchable_text'] = build_searchable_text(record)
        records.append(record)
    
    return records

def process_gdb(filepath):
    """Process geodatabase layer metadata file."""
    df = pd.read_csv(filepath)
    records = []
    
    for _, row in df.iterrows():
        record = {
            'type': 'geodatabase',
            'subtype': 'gdb_layer',
            'path': clean_text(row.get('geodatabase', '')),
            'name': clean_text(row.get('layer', '')),
            'species': clean_text(row.get('Species', '')),
            'activity': clean_text(row.get('activity', '')),
            'filename_tokens': clean_text(row.get('first_word', '')),
            'fields': clean_text(row.get('field_names', '')),
            'status': clean_text(row.get('status', '')),
            'feature_count': row.get('feature_count') if pd.notna(row.get('feature_count')) else None,
            'geometry_types': clean_text(row.get('geometry_types', '')),
            'crs': clean_text(row.get('crs', '')),
            'min_date': clean_text(row.get('min_date', '')),
            'max_date': clean_text(row.get('max_date', '')),
        }
        record['searchable_text'] = build_searchable_text(record)
        records.append(record)
    
    return records

def process_shp(filepath):
    """Process shapefile metadata file."""
    df = pd.read_csv(filepath)
    records = []
    
    for _, row in df.iterrows():
        record = {
            'type': 'shapefile',
            'subtype': 'shp',
            'path': clean_text(row.get('shapefile_path', '')),
            'name': clean_text(row.get('layer_name', '')),
            'species': clean_text(row.get('Species', '')),
            'activity': clean_text(row.get('activity', '')),
            'filename_tokens': clean_text(row.get('first_word', '')),
            'fields': clean_text(row.get('field_names', '')),
            'status': clean_text(row.get('status', '')),
            'feature_count': row.get('feature_count') if pd.notna(row.get('feature_count')) else None,
            'geometry_types': clean_text(row.get('geometry_types', '')),
            'crs': clean_text(row.get('crs', '')),
            'min_date': clean_text(row.get('min_date', '')),
            'max_date': clean_text(row.get('max_date', '')),
        }
        record['searchable_text'] = build_searchable_text(record)
        records.append(record)
    
    return records

def process_images(filepath):
    """Process image metadata file."""
    df = pd.read_csv(filepath)
    records = []
    
    for _, row in df.iterrows():
        record = {
            'type': 'image',
            'subtype': clean_text(row.get('file_extension', '')).replace('.', ''),
            'path': clean_text(row.get('image_path', '')),
            'name': clean_text(row.get('file_name', '')),
            'species': clean_text(row.get('Species', '')),
            'activity': clean_text(row.get('activity', '')),
            'filename_tokens': clean_text(row.get('filename_tokens', '')),
            'fields': '',  # Images don't have fields
            'status': clean_text(row.get('status', '')),
            'file_size_mb': row.get('file_size_mb') if pd.notna(row.get('file_size_mb')) else None,
            'width_px': row.get('width_px') if pd.notna(row.get('width_px')) else None,
            'height_px': row.get('height_px') if pd.notna(row.get('height_px')) else None,
            'camera_make': clean_text(row.get('camera_make', '')),
            'camera_model': clean_text(row.get('camera_model', '')),
            'has_gps': row.get('gps_info') == True or str(row.get('gps_info', '')).lower() == 'true',
        }
        record['searchable_text'] = build_searchable_text(record)
        records.append(record)
    
    return records

def main():
    data_dir = Path('/mnt/user-data/uploads')
    output_dir = Path('/home/claude/neom_search_v2')
    
    print("Loading metadata files...")
    
    all_records = []
    
    # Process each metadata type
    csv_xlsx_path = data_dir / 'csv_xlsx_tables_metadata.csv'
    if csv_xlsx_path.exists():
        records = process_csv_xlsx(csv_xlsx_path)
        print(f"  CSV/XLSX: {len(records)} records")
        all_records.extend(records)
    
    gdb_path = data_dir / 'gdb_layer_metadata.csv'
    if gdb_path.exists():
        records = process_gdb(gdb_path)
        print(f"  GDB: {len(records)} records")
        all_records.extend(records)
    
    # Also check for gdb_layer_metadata_2.csv
    gdb_path2 = data_dir / 'gdb_layer_metadata_2.csv'
    if gdb_path2.exists():
        records = process_gdb(gdb_path2)
        print(f"  GDB (2): {len(records)} records")
        all_records.extend(records)
    
    shp_path = data_dir / 'shp_layer_metadata.csv'
    if shp_path.exists():
        records = process_shp(shp_path)
        print(f"  Shapefiles: {len(records)} records")
        all_records.extend(records)
    
    images_path = data_dir / 'images_layer_metadata.csv'
    if images_path.exists():
        records = process_images(images_path)
        print(f"  Images: {len(records)} records")
        all_records.extend(records)
    
    print(f"\nTotal records: {len(all_records)}")
    
    # Extract unique values for filters
    species_set = set()
    activity_set = set()
    type_set = set()
    
    for r in all_records:
        if r['species']:
            species_set.add(r['species'])
        if r['activity']:
            activity_set.add(r['activity'])
        if r['type']:
            type_set.add(r['type'])
    
    filters = {
        'species': sorted(list(species_set)),
        'activity': sorted(list(activity_set)),
        'type': sorted(list(type_set)),
    }
    
    print(f"\nFilter options:")
    print(f"  Species: {filters['species']}")
    print(f"  Activity: {filters['activity']}")
    print(f"  Types: {filters['type']}")
    
    # Generate embeddings
    print("\nLoading sentence transformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Generating embeddings...")
    texts = [r['searchable_text'] for r in all_records]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    
    # Save outputs
    print("\nSaving index...")
    
    # Save embeddings
    np.save(output_dir / 'embeddings.npy', embeddings.astype('float32'))
    
    # Save records (without searchable_text to save space)
    records_clean = []
    for r in all_records:
        r_clean = {k: v for k, v in r.items() if k != 'searchable_text'}
        records_clean.append(r_clean)
    
    with open(output_dir / 'records.json', 'w', encoding='utf-8') as f:
        json.dump(records_clean, f, indent=2)
    
    # Save filter options
    with open(output_dir / 'filters.json', 'w', encoding='utf-8') as f:
        json.dump(filters, f, indent=2)
    
    # Also save searchable texts for debugging
    with open(output_dir / 'searchable_texts.txt', 'w', encoding='utf-8') as f:
        for t in texts:
            f.write(t + '\n')
    
    print("Done!")
    print(f"\nOutput files:")
    print(f"  {output_dir / 'embeddings.npy'}")
    print(f"  {output_dir / 'records.json'}")
    print(f"  {output_dir / 'filters.json'}")

if __name__ == '__main__':
    main()
