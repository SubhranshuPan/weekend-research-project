from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import shutil
from pathlib import Path

from .indexer import Indexer
from .searcher import Searcher

app = FastAPI(title="Research Assistant API")

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PAPERS_DIR = "papers"
# Create papers directory if it doesn't exist
os.makedirs(PAPERS_DIR, exist_ok=True)

# Try to initialize searcher
searcher = Searcher()
try:
    searcher.load_index(PAPERS_DIR)
except FileNotFoundError:
    pass

@app.get("/api/search")
def search(q: str, limit: int = 10):
    if not q:
        return {"results": []}
    
    try:
        # Reload index in case it changed
        searcher.load_index(PAPERS_DIR)
        results = searcher.search(q, limit=limit)
        
        # Format results
        formatted_results = []
        for doc_id, score in results:
            formatted_results.append({
                "id": doc_id,
                "filename": os.path.basename(doc_id),
                "score": score
            })
            
        return {"results": formatted_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    saved_files = []
    for file in files:
        file_path = os.path.join(PAPERS_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
        
    # Re-index
    indexer = Indexer()
    indexer.index_directory(PAPERS_DIR, [".txt", ".pdf", ".docx", ".md"])
    
    # Reload searcher
    try:
        searcher.load_index(PAPERS_DIR)
    except Exception as e:
        pass
        
    return {"message": "Files uploaded and indexed successfully", "files": saved_files}

@app.get("/api/papers")
def list_papers():
    if not os.path.exists(PAPERS_DIR):
        return {"papers": []}
        
    papers = []
    for f in os.listdir(PAPERS_DIR):
        if f != "index.json" and not f.startswith("."):
            papers.append({
                "id": f,
                "filename": f,
                "size": os.path.getsize(os.path.join(PAPERS_DIR, f))
            })
            
    return {"papers": papers}
