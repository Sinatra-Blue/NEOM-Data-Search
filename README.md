# NEOM Data Search v2

An improved semantic search tool for NEOM marine research files with structured metadata filtering.

## What's New in v2

- **Structured metadata search**: Searches against curated metadata (filename, species, activity, column/field names) rather than raw file contents
- **Faceted filtering**: Filter by Species, Activity type, and File type using dropdowns
- **Better relevance**: Results are ranked by how well they match your query's intent, not just keyword occurrence
- **Cleaner UI**: Modern dark interface with clear result cards showing file type, species, and available fields

## Files

- `build_index.py` - Script to build the search index from metadata CSV files
- `search_service.py` - FastAPI backend with semantic search and filtering
- `sentence_model.py` - Embedding model loader
- `frontend.html` - Web interface
- `requirements.txt` - Python dependencies

## Setup

### 1. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Build the search index

Copy your metadata CSV files to this directory:
- `csv_xlsx_tables_metadata.csv`
- `gdb_layer_metadata.csv`
- `shp_layer_metadata.csv`
- `images_layer_metadata.csv`

Then run:

```bash
python build_index.py
```

This will create:
- `search_index.json` - Unified metadata records
- `search_embeddings.npy` - Vector embeddings for semantic search

### 4. Run the search service

```bash
uvicorn search_service:app --reload
```

### 5. Open the web interface

Navigate to: http://127.0.0.1:8000/

## How It Works

### Search Modes

1. **Semantic Search**: Enter natural language queries like "dugong feeding habitat" or "turtle satellite tracking data". The system finds files whose metadata is semantically similar to your query.

2. **Faceted Filters**: Use the dropdowns to filter by:
   - Species (Bird, Cetaceans, Corals, Flora And Fauna, Flying Fish, Turtles)
   - Activity (Restoration, Species Management, Species_Recovery, Study, Survey)
   - File Type (spreadsheet, geodatabase, shapefile, image)

3. **Regex Filters**: Use include/exclude patterns for precise matching (e.g., `dugong.*\.csv` to find CSV files with "dugong" in the name)

### What Gets Indexed

For each file, the following metadata is combined into searchable text:
- Filename and path keywords
- Species and activity tags
- Column names (for spreadsheets)
- Field names (for geodatabases and shapefiles)
- Geometry types (for spatial files)

This means when you search for "feeding trails", you'll find files that are *about* feeding trails (based on their metadata), not files that just happen to contain those words somewhere in their contents.

## API Endpoints

- `GET /` - Web interface
- `GET /api/filters` - Available filter options
- `GET /api/search` - Search endpoint
  - `q` - Semantic search query
  - `species` - Filter by species
  - `activity` - Filter by activity
  - `file_type` - Filter by file type
  - `include` - Regex include pattern
  - `exclude` - Regex exclude pattern
  - `limit` - Max results (default 100)
- `GET /api/stats` - Index statistics
