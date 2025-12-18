"""
NEOM File Search Service v2
- Semantic search on scanned file content
- Filter by species, places, survey types, and more
"""

import json
import re
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from sentence_model import embed

app = FastAPI(title="NEOM File Search v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for the dugong image)
app.mount("/static", StaticFiles(directory="."), name="static")

# Load index and embeddings
print("Loading search index...")
with open("search_index.json", encoding="utf-8") as f:
    index_data = json.load(f)
    records = index_data['records']
    categories = index_data['categories']
    filters = index_data['filters']

print(f"Loaded {len(records)} records")
print(f"Categories: {categories}")

embeddings = np.load("search_embeddings.npy")
print(f"Loaded embeddings: {embeddings.shape}")


@app.get("/", response_class=HTMLResponse)
def home():
    with open("frontend.html", encoding="utf-8") as f:
        return f.read()


@app.get("/api/filters")
def get_filters():
    """Return available filter options for each category."""
    return {
        'categories': categories,
        'options': filters,
    }


@app.get("/api/search")
def search(
    q: str = "",
    marine_mammals: Optional[str] = None,
    sharks_rays: Optional[str] = None,
    reptiles: Optional[str] = None,
    fish: Optional[str] = None,
    birds: Optional[str] = None,
    invertebrates_habitat: Optional[str] = None,
    survey_types: Optional[str] = None,
    places: Optional[str] = None,
    data_types: Optional[str] = None,
    conservation: Optional[str] = None,
    file_type: Optional[str] = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    limit: int = 100
):
    """
    Search files with semantic ranking and category filtering.
    """
    
    # Collect category filters
    category_filters = {
        'marine_mammals': marine_mammals,
        'sharks_rays': sharks_rays,
        'reptiles': reptiles,
        'fish': fish,
        'birds': birds,
        'invertebrates_habitat': invertebrates_habitat,
        'survey_types': survey_types,
        'places': places,
        'data_types': data_types,
        'conservation': conservation,
    }
    
    # Start with all indices
    candidate_indices = list(range(len(records)))
    
    # Apply category filters
    for cat, filter_val in category_filters.items():
        if filter_val:
            # Check if the filter value appears in the record's category field
            candidate_indices = [
                i for i in candidate_indices 
                if filter_val.lower() in records[i].get(cat, '').lower()
            ]
    
    # Apply file type filter
    if file_type:
        candidate_indices = [
            i for i in candidate_indices 
            if records[i]['file_type'] == file_type
        ]
    
    # Apply regex include filter
    if include:
        try:
            r_inc = re.compile(include, re.IGNORECASE)
            candidate_indices = [
                i for i in candidate_indices 
                if r_inc.search(records[i]['searchable_text']) or r_inc.search(records[i]['file_path'])
            ]
        except re.error as e:
            return {"error": f"Include regex error: {e}"}
    
    # Apply regex exclude filter
    if exclude:
        try:
            r_exc = re.compile(exclude, re.IGNORECASE)
            candidate_indices = [
                i for i in candidate_indices 
                if not (r_exc.search(records[i]['searchable_text']) or r_exc.search(records[i]['file_path']))
            ]
        except re.error as e:
            return {"error": f"Exclude regex error: {e}"}
    
    # Semantic ranking or alphabetical fallback
    if q.strip():
        q_emb = embed(q)
        
        if candidate_indices:
            candidate_embeddings = embeddings[candidate_indices]
            sims = (candidate_embeddings @ q_emb.T).ravel()
            
            sorted_order = np.argsort(-sims)
            ranked_indices = [candidate_indices[i] for i in sorted_order]
            ranked_scores = [float(sims[i]) for i in sorted_order]
        else:
            ranked_indices = []
            ranked_scores = []
    else:
        # Alphabetical sort by filename
        sorted_candidates = sorted(candidate_indices, key=lambda i: records[i]['file_name'].lower())
        ranked_indices = sorted_candidates
        ranked_scores = [None] * len(sorted_candidates)
    
    # Build results
    results = []
    for idx, score in zip(ranked_indices[:limit], ranked_scores[:limit]):
        rec = records[idx]
        result = {
            'file_name': rec['file_name'],
            'file_path': rec['file_path'],
            'file_type': rec['file_type'],
        }
        
        if score is not None:
            result['score'] = round(score, 4)
        
        # Add category data
        for cat in categories:
            if rec.get(cat):
                result[cat] = rec[cat]
        
        results.append(result)
    
    return {
        'total_matches': len(ranked_indices),
        'showing': len(results),
        'results': results
    }


@app.get("/api/stats")
def get_stats():
    """Return index statistics."""
    type_counts = {}
    category_counts = {cat: 0 for cat in categories}
    
    for rec in records:
        # Count file types
        ft = rec['file_type']
        type_counts[ft] = type_counts.get(ft, 0) + 1
        
        # Count categories with data
        for cat in categories:
            if rec.get(cat):
                category_counts[cat] += 1
    
    return {
        'total_files': len(records),
        'by_type': type_counts,
        'by_category': category_counts,
    }
