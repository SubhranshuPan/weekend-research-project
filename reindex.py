import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from research_assistant.indexer import Indexer
from research_assistant.semantic_searcher import SemanticSearcher

def main():
    print("Initializing indexer and semantic searcher...")
    indexer = Indexer()
    semantic_searcher = SemanticSearcher()
    
    papers_dir = "papers"
    print(f"Indexing directory: {papers_dir}")
    indexer.index_directory(papers_dir, [".txt", ".pdf", ".docx", ".md"])
    
    print("Building semantic index...")
    semantic_searcher.build_index(indexer, papers_dir)
    print("Done!")

if __name__ == "__main__":
    main()
