import sys
sys.path.append('.')
from research_assistant.indexer import Indexer
from research_assistant.searcher import Searcher

# Test tokenization
indexer = Indexer()
print("Indexer stopwords:", len(indexer.stop_words) if hasattr(indexer, 'stop_words') else 'None')
print("Indexer stemmer:", indexer.stemmer)
print("Tokenize 'learning':", indexer._tokenize("learning"))
print("Tokenize 'Learning':", indexer._tokenize("Learning"))
print("Tokenize 'learn':", indexer._tokenize("learn"))

# Load index and see what's actually indexed
searcher = Searcher()
try:
    searcher.load_index('test_papers')
    print("\nIndex keys (first 10):", list(searcher.index.keys())[:10])
    print("Doc lengths:", searcher.doc_lengths)
    print("Num docs:", searcher.num_docs)

    # Check if 'learn' or similar is in index
    for term in searcher.index:
        if 'learn' in term:
            print(f"Found term '{term}' in index with docs: {list(searcher.index[term].keys())}")
except Exception as e:
    print("Error loading index:", e)