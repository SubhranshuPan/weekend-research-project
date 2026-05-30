import sys
import os
sys.path.append('.')

def test_imports():
    print("Testing imports...")
    try:
        import PyPDF2
        print("  PyPDF2: OK")
    except ImportError as e:
        print(f"  PyPDF2: FAIL - {e}")
    try:
        import nltk
        print("  nltk: OK")
    except ImportError as e:
        print(f"  nltk: FAIL - {e}")
    try:
        from research_assistant.indexer import Indexer
        from research_assistant.searcher import Searcher
        print("  research_assistant modules: OK")
    except ImportError as e:
        print(f"  research_assistant modules: FAIL - {e}")

def test_indexer():
    print("\nTesting Indexer...")
    from research_assistant.indexer import Indexer
    indexer = Indexer()
    # Test tokenization
    test_text = "This is a test of the tokenizer."
    tokens = indexer._tokenize(test_text)
    print(f"  Tokenization test: '{test_text}' -> {tokens}")
    # Test that stopwords are removed and stemming applied
    # 'this', 'is', 'a', 'of' should be removed; 'test' -> 'test', 'tokenizer' -> 'tokeniz'
    expected = ['test', 'tokeniz']
    if set(tokens) == set(expected):
        print("  Stopword removal and stemming: OK")
    else:
        print(f"  Stopword removal and stemming: FAIL - got {tokens}, expected something like {expected}")

def test_searcher():
    print("\nTesting Searcher...")
    from research_assistant.searcher import Searcher
    searcher = Searcher()
    # Check that the indexer and searcher share the same stopwords and stemmer if NLTK is available
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import PorterStemmer
        expected_stopwords = set(stopwords.words('english'))
        expected_stemmer = PorterStemmer()
        if hasattr(searcher, 'stop_words') and searcher.stop_words == expected_stopwords:
            print("  Searcher stopwords: OK")
        else:
            print("  Searcher stopwords: FAIL")
        if hasattr(searcher, 'stemmer') and searcher.stemmer is not None:
            print("  Searcher stemmer: OK")
        else:
            print("  Searcher stemmer: FAIL (None)")
    except ImportError:
        print("  NLTK not available, skipping stopwords/stemmer check")

def test_end_to_end():
    print("\nTesting end-to-end indexing and search...")
    from research_assistant.indexer import Indexer
    from research_assistant.searcher import Searcher
    import json
    import os

    # Use the test_papers directory
    index_dir = 'test_papers'
    if not os.path.exists(index_dir):
        print(f"  Directory {index_dir} does not exist.")
        return

    # Index
    indexer = Indexer()
    indexer.index_directory(index_dir, ['.txt'])
    print(f"  Indexed files in {index_dir}")

    # Load index in searcher
    searcher = Searcher()
    try:
        searcher.load_index(index_dir)
        print("  Loaded index successfully")
    except Exception as e:
        print(f"  Failed to load index: {e}")
        return

    # Search for a known term
    results = searcher.search('learning', limit=5)
    print(f"  Search for 'learning' returned {len(results)} results:")
    for doc, score in results:
        print(f"    {doc}: {score:.4f}")

    # Check that we got both documents
    doc_names = {doc for doc, _ in results}
    expected = {'machine_learning.txt', 'deep_learning.txt'}
    if doc_names == expected:
        print("  Both documents found: OK")
    else:
        print(f"  Expected {expected}, got {doc_names}")

if __name__ == '__main__':
    test_imports()
    test_indexer()
    test_searcher()
    test_end_to_end()
    print("\nFoundation test complete.")