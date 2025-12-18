"""
Scan NEOM data files for species mentions.

This script walks through the external drive, reads non-image files,
and searches for species names in the actual data content.

Output: A CSV file with each file path and any species found within it.

Usage:
    python scan_species_mentions.py

Requires:
    pip install pandas geopandas fiona openpyxl PyPDF2 tqdm
"""

import os
import re
import csv
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================

# Root folder to scan
ROOT_PATH = "E:\\"

# Output file
OUTPUT_FILE = "species_mentions_scan.csv"

# ============================================================================
# SEARCH TERMS - ADD YOUR OWN TERMS HERE!
# ============================================================================
# 
# Each category below will create its own column in the output CSV.
# Just add new terms to any list, or create a new category!
#
# Tips:
#   - Terms are case-insensitive (shark matches Shark, SHARK, etc.)
#   - Terms match whole words (ray won't match "array")
#   - Plurals are matched automatically (shark matches sharks)
#   - Use spaces for multi-word terms ('whale shark', 'green turtle')
#

SEARCH_CATEGORIES = {
    
    # -------------------------------------------------------------------------
    # SPECIES - Marine mammals
    # -------------------------------------------------------------------------
    'marine_mammals': [
        'dugong', 'dolphin', 'whale', 'manatee', 'porpoise', 'cetacean',
        'bottlenose', 'spinner', 'humpback', 'brydes', 'bryde', 'minke', 'orca',
        'indo-pacific', 'pantropical', 'rissos', 'false killer',
    ],
    
    # -------------------------------------------------------------------------
    # SPECIES - Sharks and rays
    # -------------------------------------------------------------------------
    'sharks_rays': [
        'shark', 'ray', 'manta', 'stingray', 'guitarfish', 'sawfish', 'hammerhead',
        'whale shark', 'tiger shark', 'reef shark', 'blacktip', 'whitetip',
        'eagle ray', 'mobula', 'leopard shark', 'nurse shark', 'silky shark',
        'thresher', 'oceanic whitetip',
    ],
    
    # -------------------------------------------------------------------------
    # SPECIES - Reptiles
    # -------------------------------------------------------------------------
    'reptiles': [
        'turtle', 'hawksbill', 'loggerhead', 'green turtle', 'leatherback',
        'olive ridley', 'sea snake', 'sea turtle',
    ],
    
    # -------------------------------------------------------------------------
    # SPECIES - Fish
    # -------------------------------------------------------------------------
    'fish': [
        'grouper', 'parrotfish', 'snapper', 'barracuda', 'tuna', 'trevally',
        'fusilier', 'anthias', 'clownfish', 'moray', 'napoleonfish', 'napoleon',
        'bumphead', 'sweetlips', 'emperor', 'rabbitfish', 'surgeonfish',
        'wrasse', 'damselfish', 'butterflyfish', 'angelfish', 'goby', 'blenny',
        'pufferfish', 'triggerfish', 'lionfish', 'scorpionfish',
    ],
    
    # -------------------------------------------------------------------------
    # SPECIES - Birds
    # -------------------------------------------------------------------------
    'birds': [
        'osprey', 'falcon', 'sooty falcon', 'eagle', 'tern', 'gull', 'heron',
        'cormorant', 'pelican', 'booby', 'frigatebird', 'flamingo', 'plover',
        'sandpiper', 'egret', 'shearwater', 'petrel', 'tropicbird', 'raptor',
        'sooty gull', 'white-eyed gull', 'crab plover', 'reef heron',
    ],
    
    # -------------------------------------------------------------------------
    # SPECIES - Invertebrates & Habitat
    # -------------------------------------------------------------------------
    'invertebrates_habitat': [
        'coral', 'seagrass', 'sea grass', 'sponge', 'urchin', 'starfish',
        'sea cucumber', 'octopus', 'squid', 'cuttlefish', 'jellyfish',
        'crab', 'lobster', 'shrimp', 'giant clam', 'triton', 'nudibranch',
        'anemone', 'bryozoan', 'hydroid', 'tunicate', 'mangrove', 'algae',
    ],
    
    # -------------------------------------------------------------------------
    # SURVEY TYPES - What kind of data collection?
    # -------------------------------------------------------------------------
    'survey_types': [
        'survey', 'transect', 'quadrat', 'monitoring', 'assessment', 'census',
        'sighting', 'observation', 'encounter', 'stranding', 'nesting',
        'tagging', 'satellite tag', 'acoustic', 'photo-id', 'photo id',
        'biopsy', 'genetic', 'sample', 'capture', 'recapture', 'telemetry',
        'drone', 'aerial', 'boat survey', 'dive survey', 'snorkel',
        'BRUV', 'baited remote', 'camera trap', 'ROV', 'AUV',
        'benthic', 'pelagic', 'intertidal', 'subtidal',
        'baseline', 'impact', 'EIA', 'environmental impact',
    ],
    
    # -------------------------------------------------------------------------
    # PLACE NAMES - Locations in NEOM / Red Sea region
    # -------------------------------------------------------------------------
    'places': [
        # NEOM specific
        'NEOM', 'Sharma', 'Gayal', 'Sindalah', 'Magna',
        # Gulf of Aqaba
        'Aqaba', 'Gulf of Aqaba', 'Tiran', 'Sanafir',
        # Red Sea general
        'Red Sea', 'Farasan', 'Yanbu', 'Jeddah', 'Thuwal', 'Rabigh',
        'Al Wajh', 'Umluj', 'Duba', 'Haql', 'Tabuk',
        # Islands (add more as needed)
        'island', 'reef', 'lagoon', 'bay', 'coast', 'offshore',
    ],
    
    # -------------------------------------------------------------------------
    # DATA TYPES - What kind of information?
    # -------------------------------------------------------------------------
    'data_types': [
        'GPS', 'coordinate', 'latitude', 'longitude', 'waypoint', 'track',
        'depth', 'temperature', 'salinity', 'chlorophyll', 'turbidity',
        'abundance', 'density', 'biomass', 'count', 'frequency',
        'size', 'length', 'weight', 'measurement',
        'behaviour', 'behavior', 'feeding', 'breeding', 'migration',
        'habitat', 'substrate', 'bathymetry', 'geomorphology',
    ],
    
    # -------------------------------------------------------------------------
    # CONSERVATION / MANAGEMENT TERMS
    # -------------------------------------------------------------------------
    'conservation': [
        'protected', 'MPA', 'marine protected', 'sanctuary', 'reserve',
        'endangered', 'threatened', 'vulnerable', 'IUCN', 'CITES',
        'conservation', 'restoration', 'rehabilitation', 'management',
        'impact', 'disturbance', 'pollution', 'debris', 'plastic',
        'bycatch', 'fishery', 'fishing', 'boat strike', 'collision',
    ],
    
    # -------------------------------------------------------------------------
    # ADD YOUR OWN CATEGORY HERE!
    # -------------------------------------------------------------------------
    # 'your_category_name': [
    #     'term1', 'term2', 'term3',
    # ],
    
}

# File extensions to skip entirely
SKIP_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff', '.cr2', '.nef', '.bmp', '.raw',
    # Audio/Video  
    '.avi', '.mp4', '.mov', '.wav', '.mp3', '.wmv',
    # GIS support files (we read .shp directly, which uses .dbf)
    '.shx', '.prj', '.cpg', '.sbn', '.sbx', '.shp.xml', '.qmd', '.dbf',
    # Geodatabase support files
    '.gdbtable', '.gdbtablx', '.gdbindexes', '.atx', '.freelist', '.horizon', '.spx',
    # Other
    '.lock', '.xml', '.html', '.htm', '.pptx', '.docx',
}

# Maximum file size to read (skip very large files)
MAX_FILE_SIZE_MB = 500

# For large tables, limit rows scanned
MAX_ROWS = 100000

# ============================================================================
# COMPILE REGEX PATTERNS (don't edit this section)
# ============================================================================

# Build regex patterns for each category
CATEGORY_PATTERNS = {}
for category, terms in SEARCH_CATEGORIES.items():
    CATEGORY_PATTERNS[category] = {}
    for term in terms:
        pattern = r'\b' + re.escape(term) + r's?\b'  # Match plurals too
        CATEGORY_PATTERNS[category][term] = re.compile(pattern, re.IGNORECASE)


def find_matches_in_text(text):
    """
    Search text for all category matches.
    Returns dict with category names as keys and sets of found terms as values.
    """
    if not text or not isinstance(text, str):
        return {cat: set() for cat in SEARCH_CATEGORIES}
    
    results = {}
    for category, patterns in CATEGORY_PATTERNS.items():
        found = set()
        for term, pattern in patterns.items():
            if pattern.search(text):
                found.add(term)
        results[category] = found
    
    return results


# ============================================================================
# FILE READERS
# ============================================================================

def read_shapefile(shp_path):
    """Read a shapefile attribute table and return all text content."""
    try:
        import geopandas as gpd
        
        # Read without geometry for speed
        gdf = gpd.read_file(shp_path, ignore_geometry=True, rows=MAX_ROWS)
        
        # Combine all text columns into one big string
        text_parts = []
        for col in gdf.columns:
            # Add column name
            text_parts.append(str(col))
            # Add values from string columns
            if gdf[col].dtype == 'object':
                text_parts.extend(gdf[col].dropna().astype(str).tolist())
        
        return ' '.join(text_parts)
    
    except Exception as e:
        return f"ERROR: {e}"


def read_geodatabase(gdb_path):
    """Read all layers from a geodatabase and return all text content."""
    try:
        import fiona
        import geopandas as gpd
        
        layers = fiona.listlayers(str(gdb_path))
        
        text_parts = []
        for layer in layers:
            try:
                # Add layer name
                text_parts.append(layer)
                # Read layer data
                gdf = gpd.read_file(str(gdb_path), layer=layer, ignore_geometry=True, rows=MAX_ROWS)
                for col in gdf.columns:
                    text_parts.append(str(col))
                    if gdf[col].dtype == 'object':
                        text_parts.extend(gdf[col].dropna().astype(str).tolist())
            except Exception as layer_err:
                continue
        
        return ' '.join(text_parts)
    
    except Exception as e:
        return f"ERROR: {e}"


def read_excel(xlsx_path):
    """Read an Excel file and return all text content."""
    try:
        import pandas as pd
        
        xlsx = pd.ExcelFile(xlsx_path)
        text_parts = []
        
        for sheet_name in xlsx.sheet_names:
            try:
                text_parts.append(sheet_name)
                df = pd.read_excel(xlsx, sheet_name=sheet_name, nrows=MAX_ROWS)
                for col in df.columns:
                    text_parts.append(str(col))
                    if df[col].dtype == 'object':
                        text_parts.extend(df[col].dropna().astype(str).tolist())
            except:
                continue
        
        return ' '.join(text_parts)
    
    except Exception as e:
        return f"ERROR: {e}"


def read_csv_file(csv_path):
    """Read a CSV file and return all text content."""
    try:
        import pandas as pd
        
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(csv_path, encoding=encoding, nrows=MAX_ROWS, on_bad_lines='skip')
                break
            except:
                continue
        else:
            return None
        
        text_parts = []
        for col in df.columns:
            text_parts.append(str(col))
            if df[col].dtype == 'object':
                text_parts.extend(df[col].dropna().astype(str).tolist())
        
        return ' '.join(text_parts)
    
    except Exception as e:
        return f"ERROR: {e}"


def read_pdf(pdf_path):
    """Read a PDF file and return all text content."""
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(pdf_path)
        text_parts = []
        
        # Limit pages for very large PDFs
        max_pages = min(len(reader.pages), 100)
        
        for i in range(max_pages):
            try:
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text_parts.append(page_text)
            except:
                continue
        
        return ' '.join(text_parts)
    
    except Exception as e:
        return f"ERROR: {e}"


def read_gpx(gpx_path):
    """Read a GPX file and return all text content."""
    try:
        with open(gpx_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f"ERROR: {e}"


# ============================================================================
# MAIN SCANNER
# ============================================================================

def get_files_to_scan(root_path):
    """Walk directory tree and return list of files to scan."""
    files_to_scan = []
    gdb_folders_seen = set()
    
    print(f"Finding files in {root_path}...")
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        current_path = Path(dirpath)
        
        # If this is a .gdb folder, add it and skip contents
        if current_path.suffix.lower() == '.gdb':
            if str(current_path) not in gdb_folders_seen:
                gdb_folders_seen.add(str(current_path))
                files_to_scan.append({
                    'path': str(current_path),
                    'type': 'geodatabase',
                    'name': current_path.name
                })
            # Don't descend into .gdb folder
            dirnames.clear()
            continue
        
        # Skip if we're inside a .gdb folder (shouldn't happen but just in case)
        is_inside_gdb = any(p.suffix.lower() == '.gdb' for p in current_path.parents)
        if is_inside_gdb:
            continue
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            # Skip unwanted extensions
            if ext in SKIP_EXTENSIONS:
                continue
            
            # Get file size
            try:
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                if size_mb > MAX_FILE_SIZE_MB:
                    continue
            except:
                continue
            
            # Determine file type
            file_type = None
            if ext == '.shp':
                file_type = 'shapefile'
            elif ext in ['.xlsx', '.xls']:
                file_type = 'excel'
            elif ext == '.csv':
                file_type = 'csv'
            elif ext == '.pdf':
                file_type = 'pdf'
            elif ext == '.gpx':
                file_type = 'gpx'
            
            if file_type:
                files_to_scan.append({
                    'path': filepath,
                    'type': file_type,
                    'name': filename
                })
    
    return files_to_scan


def scan_file(file_info):
    """Scan a single file for matches in all categories."""
    filepath = file_info['path']
    file_type = file_info['type']
    
    # Read file content based on type
    text = None
    
    if file_type == 'shapefile':
        text = read_shapefile(filepath)
    elif file_type == 'geodatabase':
        text = read_geodatabase(filepath)
    elif file_type == 'excel':
        text = read_excel(filepath)
    elif file_type == 'csv':
        text = read_csv_file(filepath)
    elif file_type == 'pdf':
        text = read_pdf(filepath)
    elif file_type == 'gpx':
        text = read_gpx(filepath)
    
    # Check for errors
    if text and isinstance(text, str) and text.startswith("ERROR:"):
        result = {
            'file_path': filepath,
            'file_name': file_info['name'],
            'file_type': file_type,
            'status': 'error',
            'error': text,
        }
        # Add empty columns for each category
        for category in SEARCH_CATEGORIES:
            result[category] = ''
        return result
    
    # Find matches in all categories
    matches_from_content = find_matches_in_text(text) if text else {cat: set() for cat in SEARCH_CATEGORIES}
    matches_from_path = find_matches_in_text(filepath)
    
    # Combine matches from content and filepath
    result = {
        'file_path': filepath,
        'file_name': file_info['name'],
        'file_type': file_type,
        'status': 'success',
        'error': '',
    }
    
    for category in SEARCH_CATEGORIES:
        combined = matches_from_content[category] | matches_from_path[category]
        result[category] = ', '.join(sorted(combined)) if combined else ''
    
    return result


def main():
    print("=" * 60)
    print("NEOM File Content Scanner")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scanning: {ROOT_PATH}")
    print(f"\nSearch categories:")
    for cat, terms in SEARCH_CATEGORIES.items():
        print(f"  {cat}: {len(terms)} terms")
    print()
    
    # Find all files to scan
    files = get_files_to_scan(ROOT_PATH)
    
    print(f"\nFound {len(files)} files to scan:")
    type_counts = {}
    for f in files:
        t = f['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print()
    
    # Scan each file
    results = []
    errors = 0
    files_with_matches = 0
    
    print("Scanning files...")
    for file_info in tqdm(files, desc="Progress"):
        result = scan_file(file_info)
        results.append(result)
        
        if result['status'] == 'error':
            errors += 1
        # Check if any category has matches
        has_match = any(result.get(cat) for cat in SEARCH_CATEGORIES)
        if has_match:
            files_with_matches += 1
    
    # Build CSV fieldnames dynamically
    fieldnames = ['file_path', 'file_name', 'file_type', 'status', 'error'] + list(SEARCH_CATEGORIES.keys())
    
    # Write results to CSV
    print(f"\nWriting results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Summary
    print()
    print("=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"Total files scanned: {len(results)}")
    print(f"Files with matches: {files_with_matches}")
    print(f"Errors: {errors}")
    print(f"Output saved to: {OUTPUT_FILE}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show category stats
    print()
    print("Matches by category:")
    print("-" * 40)
    for cat in SEARCH_CATEGORIES:
        count = sum(1 for r in results if r.get(cat))
        print(f"  {cat}: {count} files")
    
    # Show some example findings
    print()
    print("Sample findings (first 10 files with matches):")
    print("-" * 60)
    count = 0
    for r in results:
        matches = {cat: r[cat] for cat in SEARCH_CATEGORIES if r.get(cat)}
        if matches and count < 10:
            print(f"\n{r['file_name']}")
            for cat, terms in matches.items():
                print(f"  {cat}: {terms}")
            count += 1


if __name__ == "__main__":
    main()
