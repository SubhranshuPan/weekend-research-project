import os
import json
import re
from typing import Dict, List, Tuple
try:
    # pyrefly: ignore [missing-import]
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    # pyrefly: ignore [missing-import]
    import nltk
    # pyrefly: ignore [missing-import]
    from nltk.corpus import stopwords
    # pyrefly: ignore [missing-import]
    from nltk.stem import PorterStemmer
    HAS_NLTK = True
    # Download required NLTK data
    try:
        stopwords.words('english')
    except LookupError:
        nltk.download('stopwords')
except ImportError:
    HAS_NLTK = False

try:
    # pyrefly: ignore [missing-import]
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

class Indexer:
    def __init__(self):
        self.index: Dict[str, Dict[str, int]] = {}  # term -> {doc_id: frequency}
        self.stemmer = PorterStemmer() if HAS_NLTK else None
        self.stop_words = set(stopwords.words('english')) if HAS_NLTK else set()

    def _extract_text(self, file_path: str) -> str:
        """Extract text from a file based on extension."""
        if file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif file_path.lower().endswith('.pdf') and HAS_PDF:
            text = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            return text
        elif file_path.lower().endswith('.docx') and HAS_DOCX:
            text = ""
            try:
                doc = docx.Document(file_path)
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
            except Exception:
                # If any error occurs reading the docx, return empty string
                return ""
            return text
        elif file_path.lower().endswith('.md') or file_path.lower().endswith('.markdown'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            # Unsupported format or missing dependencies
            return ""

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text: lowercase, split by non-alphanumeric, remove stopwords, stem."""
        # Basic tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())

        # Remove stopwords if NLTK is available
        if HAS_NLTK:
            tokens = [token for token in tokens if token not in self.stop_words]

        # Apply stemming if NLTK is available
        if HAS_NLTK and self.stemmer:
            tokens = [self.stemmer.stem(token) for token in tokens]

        return tokens

    def index_directory(self, directory: str, extensions: List[str]) -> None:
        """Index all files with given extensions in directory and subdirectories."""
        # Walk the directory
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    # Use relative path from directory as doc_id for portability
                    doc_id = os.path.relpath(file_path, directory)

                    text = self._extract_text(file_path)
                    if not text:
                        continue

                    tokens = self._tokenize(text)
                    # Count term frequencies in this document
                    term_freq: Dict[str, int] = {}
                    for token in tokens:
                        term_freq[token] = term_freq.get(token, 0) + 1

                    # Update inverted index
                    for term, freq in term_freq.items():
                        if term not in self.index:
                            self.index[term] = {}
                        self.index[term][doc_id] = self.index[term].get(doc_id, 0) + freq

        # Save index to file
        index_path = os.path.join(directory, 'index.json')
        with open(index_path, 'w') as f:
            json.dump(self.index, f, indent=2)

    def load_index(self, directory: str) -> None:
        """Load index from file."""
        index_path = os.path.join(directory, 'index.json')
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                self.index = json.load(f)
        else:
            raise FileNotFoundError(f"No index found at {index_path}. Please run indexing first.")