# 🦭 NEOM Data Search

A semantic search tool for finding your way through NEOM's marine research files. No more clicking through endless folders — just search like you'd ask a colleague!

![dugongs](https://github.com/user-attachments/assets/4e80f0dc-655b-48a4-bdea-4a9d2e679f1e)


*Our unofficial mascots are not impressed by disorganised data.*

---

## ✨ What Does It Do?

Ever tried to find "that shapefile with the dugong feeding trails from the Sharma survey"? This tool lets you search across **shapefiles, geodatabases, CSVs, PDFs, and more** using plain English queries.

- 🔍 **Semantic search** — Type "dugong feeding habitat" and find relevant files, even if they don't contain those exact words
- 🐋 **Filter by species** — Marine mammals, sharks & rays, turtles, birds, fish, corals, you name it
- 📍 **Filter by location** — NEOM sites, Red Sea locations, islands, reefs
- 📊 **Filter by survey type** — Transects, tagging, aerial surveys, BRUVs, monitoring programmes
- 🗂️ **Filter by file type** — Geodatabase, shapefile, CSV, Excel, PDF, GPX
- ⚡ **Properly fast** — Pre-computed embeddings mean instant results

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Sinatra-Blue/NEOM-Data-Search.git
cd NEOM-Data-Search
```

### 2. Set up your environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Scan your data files

First, edit `scan_species_mentions.py` to point to your data folder:

```python
ROOT_PATH = "E:\\"  # Change this to wherever your data lives
```

Then run the scan (grab a cuppa, this takes about 30 mins for ~250GB):

```bash
python scan_species_mentions.py
```

### 5. Build the search index

```bash
python build_index.py
```

### 6. Fire it up!

```bash
uvicorn search_service:app --reload
```

Then open your browser to: **http://127.0.0.1:8000**

---

## 🔧 How It Works

### The Scan

The scanner reads through your files (shapefiles, geodatabases, CSVs, PDFs, etc.) and looks for:

- **Species mentions** — dugong, dolphin, turtle, shark, coral, seagrass...
- **Place names** — NEOM, Sharma, Magna, Aqaba, Red Sea...
- **Survey types** — transect, tagging, BRUV, aerial, monitoring...
- **Data types** — coordinates, depth, abundance, behaviour...
- **Conservation terms** — protected, endangered, restoration...

It saves all this to `species_mentions_scan.csv`.

### The Index

The build script takes that CSV and creates:
- `search_index.json` — All the searchable metadata
- `search_embeddings.npy` — Vector embeddings for semantic matching

### The Search

When you search for "turtle nesting beaches", the system:
1. Converts your query into a vector embedding
2. Finds files with semantically similar metadata
3. Ranks them by relevance
4. Applies any filters you've selected

So you find files that are *about* turtle nesting beaches, not just files that happen to contain those words somewhere random.

---

## 🎨 Customising

Want to add more species, places, or search terms? Edit the `SEARCH_CATEGORIES` dictionary in `scan_species_mentions.py`:

```python
SEARCH_CATEGORIES = {
    'marine_mammals': [
        'dugong', 'dolphin', 'whale', ...
    ],
    'places': [
        'NEOM', 'Sharma', 'Aqaba', ...
    ],
    # Add your own!
    'your_category': [
        'term1', 'term2', 'term3',
    ],
}
```

Then re-run the scan and rebuild the index.

---

## 📁 What's In The Box

| File | What it does |
|------|--------------|
| `scan_species_mentions.py` | Scans your data files for species, places, etc. |
| `build_index.py` | Builds the search index from scan results |
| `search_service.py` | FastAPI backend that powers the search |
| `sentence_model.py` | Loads the embedding model |
| `frontend.html` | The web interface |
| `requirements.txt` | Python dependencies |
| `dugongs.png` | Our grumpy mascots |

---

## 🔌 API Endpoints

If you want to integrate this with other tools:

| Endpoint | What you get |
|----------|--------------|
| `GET /` | The web interface |
| `GET /api/filters` | Available filter options |
| `GET /api/search` | Search results (supports `q`, `species`, `places`, `file_type`, etc.) |
| `GET /api/stats` | Index statistics |

---

## 🛠️ Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) — Backend API
- [Sentence Transformers](https://www.sbert.net/) — Semantic embeddings (all-MiniLM-L6-v2)
- [GeoPandas](https://geopandas.org/) — Reading shapefiles and geodatabases
- [PyPDF2](https://pypdf2.readthedocs.io/) — PDF text extraction

---

## 📝 Notes

- First run downloads ~500MB of ML models — make sure you've got decent wifi
- The scanner skips images and media files (no point reading pixels for species names!)
- Generated files (`species_mentions_scan.csv`, `search_index.json`, `search_embeddings.npy`) are git-ignored since they're specific to your data

---

## 🦭 Acknowledgements

Built for NEOM marine research data management.

The grumpy dugongs approve this tool. Reluctantly.
