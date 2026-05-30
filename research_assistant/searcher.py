import json
import os
import math
from typing import List, Tuple, Dict
import re

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    HAS_NLTK = True
    # Download required NLTK data
    try:
        stopwords.words('english')
    except LookupError:
        nltk.download('stopwords')
except ImportError:
    HAS_NLTK = False

class Searcher:
    def __init__(self):
        self.index: Dict[str, Dict[str, int]] = {}  # term -> {doc_id: frequency}
        self.doc_lengths: Dict[str, int] = {}  # doc_id -> total terms in doc
        self.num_docs: int = 0
        self.avgdl: float = 0.0
        self.stemmer = PorterStemmer() if HAS_NLTK else None
        self.stop_words = set(stopwords.words('english')) if HAS_NLTK else set()
        self.k1: float = 1.2
        self.b: float = 0.75

    def load_index(self, directory: str) -> None:
        """Load index from file and compute document lengths and average length."""
        index_path = os.path.join(directory, 'index.json')
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"No index found at {index_path}. Please run indexing first.")

        with open(index_path, 'r') as f:
            self.index = json.load(f)

        # Compute document lengths, number of documents, and average document length
        doc_lengths: Dict[str, int] = {}
        doc_set = set()
        total_length = 0
        for term, postings in self.index.items():
            for doc_id, freq in postings.items():
                doc_set.add(doc_id)
                doc_lengths[doc_id] = doc_lengths.get(doc_id, 0) + freq
                total_length += freq
        self.doc_lengths = doc_lengths
        self.num_docs = len(doc_set)
        self.avgdl = total_length / self.num_docs if self.num_docs > 0 else 0.0

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

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Search using BM25 ranking."""
        if not self.index:
            raise ValueError("Index not loaded. Call load_index first.")

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Compute query term frequencies
        query_freq: Dict[str, int] = {}
        for token in query_tokens:
            query_freq[token] = query_freq.get(token, 0) + 1

        # Compute scores for each document
        scores: Dict[str, float] = {doc_id: 0.0 for doc_id in self.doc_lengths}
        for term, qtf in query_freq.items():
            if term in self.index:
                # Document frequency of term
                df = len(self.index[term])
                # IDF component of BM25
                idf = math.log(1 + (self.num_docs - df + 0.5) / (df + 0.5))
                for doc_id, dtf in self.index[term].items():
                    # BM25 score contribution for this term in this document
                    denominator = dtf + self.k1 * (1 - self.b + self.b * self.doc_lengths[doc_id] / self.avgdl)
                    score_contribution = idf * (dtf * (self.k1 + 1) / denominator)
                    scores[doc_id] += score_contribution

        # Sort and return top results
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return results[:limit]