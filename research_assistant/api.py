from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import shutil
from pathlib import Path

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from .indexer import Indexer
from .searcher import Searcher
from .metadata import extract_metadata, generate_bibtex
from .semantic_searcher import SemanticSearcher

app = FastAPI(title="Research Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PAPERS_DIR = "papers"
os.makedirs(PAPERS_DIR, exist_ok=True)

# Mount papers directory for serving files directly
app.mount("/api/files", StaticFiles(directory=PAPERS_DIR), name="files")

indexer = Indexer()
searcher = Searcher()
semantic_searcher = SemanticSearcher()

def load_indexes():
    try:
        searcher.load_index(PAPERS_DIR)
    except FileNotFoundError:
        pass
    try:
        semantic_searcher.load_index(PAPERS_DIR)
    except Exception:
        pass

load_indexes()

@app.get("/api/search")
def search(q: str, limit: int = 10):
    if not q:
        return {"results": []}
    
    try:
        load_indexes()
        bm25_results = searcher.search(q, limit=limit)
        semantic_results = semantic_searcher.search(q, limit=limit)
        
        # Hybrid scoring (simple linear combination or dict merge)
        # Normalize BM25 scores roughly based on max score, since they are unbounded
        # Semantic scores are cosine similarities [-1, 1]
        combined = {}
        max_bm25 = max([s for _, s in bm25_results]) if bm25_results else 1
        
        for doc_id, score in bm25_results:
            combined[doc_id] = score / max_bm25 * 0.5
            
        for doc_id, score in semantic_results:
            combined[doc_id] = combined.get(doc_id, 0) + score * 0.5
            
        # Sort combined
        sorted_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        formatted_results = []
        for doc_id, score in sorted_results:
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
        
    indexer = Indexer()
    indexer.index_directory(PAPERS_DIR, [".txt", ".pdf", ".docx", ".md"])
    semantic_searcher.build_index(indexer, PAPERS_DIR)
    
    load_indexes()
        
    return {"message": "Files uploaded and indexed successfully", "files": saved_files}

@app.get("/api/papers")
def list_papers():
    files = os.listdir(PAPERS_DIR)
    papers = []
    for file in files:
        if file.endswith(('.txt', '.pdf', '.docx', '.md')):
            papers.append({
                "id": file,
                "filename": file,
                "path": os.path.join(PAPERS_DIR, file)
            })
    return {"papers": papers}

@app.get("/api/graph")
def get_graph():
    load_indexes()
    try:
        graph = semantic_searcher.get_similarity_graph(threshold=0.5)
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}/metadata")
def get_metadata(paper_id: str):
    file_path = os.path.join(PAPERS_DIR, paper_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Paper not found")
        
    meta = extract_metadata(file_path)
    bibtex = generate_bibtex(meta, paper_id)
    return {
        "metadata": meta,
        "bibtex": bibtex
    }

@app.get("/api/papers/{paper_id}/summary")
def get_summary(paper_id: str, x_gemini_key: Optional[str] = Header(None)):
    file_path = os.path.join(PAPERS_DIR, paper_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Paper not found")
        
    if not x_gemini_key or not HAS_GENAI:
        return {
            "summary": "AI Summarization requires a Gemini API Key. Please click the Settings gear icon in the top right to configure your API key."
        }
        
    try:
        from google import genai
        client = genai.Client(api_key=x_gemini_key)
        
        # Extract text using Indexer
        indexer = Indexer()
        text = indexer._extract_text(file_path)
        if not text:
            return {"summary": "Could not extract text from this document for summarization."}
            
        # Limit to ~30k characters to avoid token limits on base models, just in case
        text = text[:30000]
        
        prompt = f"""
        You are an expert academic research assistant. Please read the following paper and provide a concise, bullet-point digest of its:
        - Core Methodology
        - Main Contributions/Findings
        - Key Limitations
        
        PAPER CONTENT:
        {text}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return {"summary": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

from pydantic import BaseModel
class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
def chat_library(req: ChatRequest, x_gemini_key: Optional[str] = Header(None)):
    if not x_gemini_key or not HAS_GENAI:
        raise HTTPException(status_code=401, detail="API Key required")
        
    try:
        from google import genai
        client = genai.Client(api_key=x_gemini_key)
        
        # Retrieve top documents
        load_indexes()
        bm25_results = searcher.search(req.query, limit=3)
        sem_results = semantic_searcher.search(req.query, limit=3)
        
        # Combine top 3 unique docs
        doc_ids = list(set([doc_id for doc_id, _ in bm25_results] + [doc_id for doc_id, _ in sem_results]))[:3]
        
        context = ""
        indexer = Indexer()
        for doc_id in doc_ids:
            file_path = os.path.join(PAPERS_DIR, doc_id)
            text = indexer._extract_text(file_path)
            if text:
                context += f"\n--- PAPER: {doc_id} ---\n{text[:5000]}\n"
                
        prompt = f"""
        You are an expert research assistant. Answer the user's question based ONLY on the following context from their paper library.
        If the answer is not in the context, say "I couldn't find an answer to this in your current library."
        Always cite the paper name when you mention a fact (e.g. [paper.pdf]).
        
        CRITICAL FORMATTING INSTRUCTION: 
        Output your response in clean, concise bullet points rather than lengthy text paragraphs. Prioritize readability and brevity.
        
        CONTEXT:
        {context}
        
        USER QUESTION: {req.query}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return {"answer": response.text, "sources": doc_ids}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import json

TAGS_FILE = os.path.join(PAPERS_DIR, "tags.json")

def load_tags():
    if os.path.exists(TAGS_FILE):
        with open(TAGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tags(tags_dict):
    with open(TAGS_FILE, 'w') as f:
        json.dump(tags_dict, f)

@app.get("/api/tags")
def get_all_tags():
    tags_dict = load_tags()
    
    # Also invert it so we get folder -> list of papers
    folders = {}
    for pid, tags in tags_dict.items():
        for t in tags:
            if t not in folders:
                folders[t] = []
            folders[t].append(pid)
            
    return {"paper_tags": tags_dict, "folders": folders}

@app.get("/api/papers/{paper_id}/auto_tag")
def auto_tag_paper(paper_id: str, x_gemini_key: str = Header(None)):
    if not HAS_GENAI or not x_gemini_key:
        raise HTTPException(status_code=401, detail="Missing Gemini API Key or genai not installed")
        
    file_path = os.path.join(PAPERS_DIR, paper_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Paper not found")
        
    text = indexer._extract_text(file_path)
    if not text:
        return {"tags": []}
        
    try:
        client = genai.Client(api_key=x_gemini_key)
        prompt = f"Analyze the following academic paper text and provide 1 to 3 broad category tags (e.g., 'Deep Learning', 'Healthcare', 'Robotics'). Return ONLY a comma-separated list of tags, nothing else. Do not use quotes or bullets.\n\nTEXT:\n{text[:5000]}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        tags_str = response.text.strip().replace('"', '')
        tags = [t.strip() for t in tags_str.split(',') if t.strip()][:3]
        
        tags_dict = load_tags()
        tags_dict[paper_id] = tags
        save_tags(tags_dict)
        
        return {"tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/papers/{paper_id}")
def delete_paper(paper_id: str):
    file_path = os.path.join(PAPERS_DIR, paper_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Paper not found")
    
    os.remove(file_path)
    
    # Re-index
    indexer = Indexer()
    indexer.index_directory(PAPERS_DIR, [".txt", ".pdf", ".docx", ".md"])
    semantic_searcher.build_index(indexer, PAPERS_DIR)
    
    load_indexes()
    
    return {"message": "Paper deleted and re-indexed"}

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

@app.get("/api/discover")
def discover_papers(q: str):
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Simple arXiv API search
        query = urllib.parse.quote(q)
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
        
        req = urllib.request.urlopen(url, context=ctx)
        xml_data = req.read()
        
        root = ET.fromstring(xml_data)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        results = []
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', namespace).text.strip()
            authors = [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)]
            
            # Find the pdf link
            pdf_url = ""
            for link in entry.findall('atom:link', namespace):
                if link.attrib.get('title') == 'pdf':
                    pdf_url = link.attrib.get('href')
                    break
            
            if not pdf_url:
                continue
                
            published = entry.find('atom:published', namespace).text
            
            results.append({
                "title": title,
                "authors": authors,
                "summary": summary,
                "pdf_url": pdf_url + ".pdf", # Ensure it ends with .pdf for direct download
                "published": published[:10]
            })
            
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DownloadRequest(BaseModel):
    title: str
    pdf_url: str

@app.post("/api/discover/download")
def download_paper(req: DownloadRequest):
    try:
        # Clean up title for filename
        safe_title = "".join([c if c.isalnum() or c in " -_" else "_" for c in req.title])[:100]
        filename = f"{safe_title}.pdf"
        file_path = os.path.join(PAPERS_DIR, filename)
        
        if os.path.exists(file_path):
            return {"message": "Already downloaded", "filename": filename}
            
        import ssl
        import shutil
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        pdf_url = req.pdf_url.replace('/abs/', '/pdf/')
        
        with urllib.request.urlopen(pdf_url, context=ctx) as response, open(file_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        
        # Re-index library
        indexer = Indexer()
        indexer.index_directory(PAPERS_DIR, [".txt", ".pdf", ".docx", ".md"])
        semantic_searcher.build_index(indexer, PAPERS_DIR)
        
        load_indexes()
        
        return {"message": "Downloaded and indexed successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
