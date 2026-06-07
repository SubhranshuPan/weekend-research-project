import os
import re
from typing import Dict, Any

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a document."""
    basename = os.path.basename(file_path)
    metadata = {
        "title": basename.rsplit(".", 1)[0].replace("_", " ").title(),
        "authors": "Unknown Author",
        "year": "2024",
        "journal": "Local Repository",
        "type": "article"
    }
    
    if file_path.lower().endswith('.pdf') and HAS_PDF:
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                info = reader.metadata
                if info:
                    if info.title:
                        metadata["title"] = info.title
                    if info.author:
                        metadata["authors"] = info.author
                    # Could try to regex year from creation date
        except Exception:
            pass
            
    # Simple regex fallback for txt/md
    if file_path.lower().endswith(('.txt', '.md')):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000) # Read first 2000 chars
                # Look for patterns like "Title: something" or "Author: someone"
                title_match = re.search(r'(?i)^title:\s*(.+)$', content, re.MULTILINE)
                if title_match:
                    metadata["title"] = title_match.group(1).strip()
                    
                author_match = re.search(r'(?i)^author[s]?:\s*(.+)$', content, re.MULTILINE)
                if author_match:
                    metadata["authors"] = author_match.group(1).strip()
                    
                year_match = re.search(r'(?i)(19|20)\d{2}', content)
                if year_match:
                    metadata["year"] = year_match.group(0)
        except Exception:
            pass
            
    return metadata

def generate_bibtex(metadata: Dict[str, Any], doc_id: str) -> str:
    """Generate a BibTeX string from metadata."""
    bib_id = f"{metadata['authors'].split()[0].lower()}{metadata['year']}{metadata['title'].split()[0].lower()}"
    bib_id = re.sub(r'[^a-zA-Z0-9]', '', bib_id)
    if not bib_id:
        bib_id = doc_id.replace('.', '_')
        
    bibtex = f"@{metadata['type']}{{{bib_id},\n"
    bibtex += f"  title = {{{metadata['title']}}},\n"
    bibtex += f"  author = {{{metadata['authors']}}},\n"
    bibtex += f"  year = {{{metadata['year']}}},\n"
    bibtex += f"  journal = {{{metadata['journal']}}}\n"
    bibtex += "}"
    return bibtex
