import os
import json
from typing import List, Tuple, Dict

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False

class SemanticSearcher:
    def __init__(self):
        self.model = None
        self.doc_ids = []
        self.embeddings = None
        
        if HAS_ST:
            # Load a small, fast model
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                pass

    def build_index(self, indexer_instance, directory: str):
        """Build semantic embeddings from the extracted text of the indexer."""
        if not HAS_ST or self.model is None:
            return
            
        doc_ids = []
        texts = []
        
        # We need to extract text from files in the directory
        extensions = ['.txt', '.pdf', '.docx', '.md']
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    doc_id = os.path.relpath(file_path, directory)
                    text = indexer_instance._extract_text(file_path)
                    if text:
                        # Take the first 1000 characters to represent the document semantics
                        # In a real app, we might chunk the document
                        texts.append(text[:2000])
                        doc_ids.append(doc_id)
                        
        if texts:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            
            # Save the embeddings
            np.save(os.path.join(directory, 'embeddings.npy'), embeddings)
            with open(os.path.join(directory, 'doc_ids.json'), 'w') as f:
                json.dump(doc_ids, f)

    def load_index(self, directory: str):
        if not HAS_ST or self.model is None:
            return False
            
        emb_path = os.path.join(directory, 'embeddings.npy')
        ids_path = os.path.join(directory, 'doc_ids.json')
        
        if os.path.exists(emb_path) and os.path.exists(ids_path):
            self.embeddings = np.load(emb_path)
            with open(ids_path, 'r') as f:
                self.doc_ids = json.load(f)
            return True
        return False

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        if not HAS_ST or not self.embeddings is not None or not query.strip():
            return []
            
        try:
            query_emb = self.model.encode(query)
            
            # Cosine similarity
            # Normalize vectors
            norm_embs = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            norm_query = query_emb / np.linalg.norm(query_emb)
            
            similarities = np.dot(norm_embs, norm_query)
            
            results = []
            for i, doc_id in enumerate(self.doc_ids):
                results.append((doc_id, float(similarities[i])))
                
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        except Exception as e:
            print(f"Semantic search failed: {e}")
            return []

    def get_similarity_graph(self, threshold: float = 0.5) -> Dict:
        if self.embeddings is None:
            return {"nodes": [], "links": []}
            
        doc_ids = list(self.doc_ids)
        nodes = [{"id": d, "name": d} for d in doc_ids]
        links = []
        
        if HAS_ST and len(doc_ids) > 1:
            try:
                norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1
                normalized_embeddings = self.embeddings / norms
                
                sim_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)
                
                for i in range(len(doc_ids)):
                    for j in range(i + 1, len(doc_ids)):
                        sim = sim_matrix[i, j]
                        if sim > threshold:
                            links.append({"source": doc_ids[i], "target": doc_ids[j], "value": float(sim)})
            except Exception as e:
                print(f"Graph gen failed: {e}")
                
        return {"nodes": nodes, "links": links}
