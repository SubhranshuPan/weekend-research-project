# Research Assistant Enhancement Plan

## Immediate Next Steps
1. Install Python 3.12+ from https://python.org (or use Microsoft Store)
2. Install dependencies: `pip install -r requirements.txt`
3. Index test papers: `python -m research_assistant.cli index --dir test_papers`
4. Test search: `python -m research_assistant.cli search --query "machine learning"`

## Planned Enhancements
### Phase 1: Core Improvements
- Add stopword removal and stemming (NLTK/spaCy)
- Support additional formats: .docx, .md
- Improve tokenization (handle hyphenated words, preserve key phrases)
- Add BM25 ranking instead of TF-IDF

### Phase 2: Features
- Web crawler to fetch papers from arXiv, Google Scholar
- Duplicate detection and document similarity
- Export results to CSV/JSON
- Simple web interface (Flask/FastAPI)

### Phase 3: Research Utility
- Citation extraction and tracking
- Topic modeling (LDA) to discover themes
- Timeline visualization of research trends
- Collaboration features (shared annotations)

### Phase 4: Optimization
- Incremental indexing (watch for file changes)
- Distributed indexing for large corpora
- Caching layer for frequent queries
- Dockerfile for containerized deployment

## Success Metrics
- Indexing speed: <1 sec per 1MB text
- Search relevance: Top 3 results contain query terms
- Scalability: Handle 10k+ documents
- Usability: One-command setup for new users