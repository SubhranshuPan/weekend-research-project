---
name: run-research-assistant
description: Build, launch, and drive the research assistant CLI tool
---

# Research Assistant Skill

This skill provides a programmatic interface to build, launch, and interact with the research assistant CLI tool for indexing and searching document collections.

## Prerequisites

- Python 3.12+
- pip package manager

## Installation

```bash
# Install required dependencies
python -m pip install -r requirements.txt
```

## Run (Agent Path)

Use the provided driver script for programmatic access:

```bash
# Install dependencies
python .claude/skills/run-research-assistant/driver.py install

# Index documents (default: test_papers directory)
python .claude/skills/run-research-assistant/driver.py index

# Index with specific extensions
python .claude/skills/run-research-assistant/driver.py index test_papers .txt .pdf .docx .md

# Search the index
python .claude/skills/run-research-assistant/driver.py search "machine learning"

# Verify installation
python .claude/skills/run-research-assistant/driver.py verify

# Run complete demo workflow
python .claude/skills/run-research-assistant/driver.py demo
```

## Run (Human Path)

For manual interaction:

```bash
# Index a directory of papers
python -m research_assistant.cli index --dir /path/to/papers

# Search the index
python -m research_assistant.cli search --query "your query" --limit 10
```

## Gotchas

- The first time NLTK runs, it may download stopword data (requires internet)
- PDF support requires PyPDF2 - if not installed, PDF files will be skipped silently
- DOCX support requires python-docx - if not installed, .docx files will be skipped silently
- The CLI requires `--dir` argument for search command
- Scores are BM25 relevance scores (higher = more relevant)

## Troubleshooting

- **"Module not found" errors**: Ensure you're running from the project root and have installed dependencies
- **"No index found"**: Run the index command first before searching
- **Encoding errors**: The indexer uses `errors='ignore'` when reading files to handle various encodings
- **Empty search results**: Verify the index contains documents and your query terms exist in the indexed text

## Direct Invocation

For advanced usage, you can import and use the research assistant modules directly:

```python
from research_assistant.indexer import Indexer
from research_assistant.searcher import Searcher

# Index documents
indexer = Indexer()
indexer.index_directory("/path/to/papers", [".txt", ".pdf"])

# Search
searcher = Searcher()
searcher.load_index("/path/to/papers")
results = searcher.search("your query", limit=10)
```