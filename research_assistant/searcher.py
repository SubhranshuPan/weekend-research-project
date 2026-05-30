import json
import os
import math
from typing import List, Tuple, Dict

class Searcher:
    def __init__(self):
        self.index: Dict[str, Dict[str, int]] = {}  # term -> {doc_id: frequency}
        self.doc_lengths: Dict[str, int] = {}  # doc_id -> total terms in doc
        self.num_docs: int = 0

    def load_index(self, directory: str) -> None:
        """Load index from file and compute document lengths."""
        index_path = os.path.join(directory, 'index.json')
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"No index found at {index_path}. Please run indexing first.")

        with open(index_path, 'r') as f:
            self.index = json.load(f)

        # Compute document lengths and number of documents
        doc_lengths: Dict[str, int] = {}
        doc_set = set()
        for term, postings in self.index.items():
            for doc_id, freq in postings.items():
                doc_set.add(doc_id)
                doc_lengths[doc_id] = doc_lengths.get(doc_id, 0) + freq
        self.doc_lengths = doc_lengths
        self.num_docs = len(doc_set)

    def _tokenize(self, query: str) -> List[str]:
        """Simple tokenization for query."""
        import re
        tokens = re.findall(r'\b\w+\b', query.lower())
        return tokens

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Search using TF-IDF cosine similarity."""
        if not self.index:
            raise ValueError("Index not loaded. Call load_index first.")

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Compute query term frequencies
        query_freq: Dict[str, int] = {}
        for token in query_tokens:
            query_freq[token] = query_freq.get(token, 0) + 1

        # Compute query vector (TF-IDF)
        query_vector: Dict[str, float] = {}
        for term, qtf in query_freq.items():
            if term in self.index:
                idf = math.log(self.num_docs / (1 + len(self.index[term])))  # add 1 to avoid division by zero
                query_vector[term] = qtf * idf

        # Compute document scores
        scores: Dict[str, float] = {}
        for term, q_weight in query_vector.items():
            if term in self.index:
                for doc_id, dtf in self.index[term].items():
                    # TF in document (already raw frequency)
                    idf = math.log(self.num_docs / (1 + len(self.index[term])))
                    d_weight = dtf * idf
                    scores[doc_id] = scores.get(doc_id, 0.0) + q_weight * d_weight

        # Normalize by document length (optional, but we can use cosine normalization)
        # For simplicity, we'll just return the raw scores and then sort.
        # Alternatively, we can normalize by the length of the document vector and query vector.
        # Let's do a simple normalization by dividing by the document length (as a proxy for vector length).
        normalized_scores: Dict[str, float] = {}
        for doc_id, score in scores.items():
            length = self.doc_lengths.get(doc_id, 1)
            normalized_scores[doc_id] = score / (length + 1)  # add 1 to avoid division by zero

        # Sort and return top results
        results = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
        return results[:limit]