# Research Assistant

A tool to help researchers search and analyze a collection of academic papers.

## Features

- Index text from PDF and text files
- Search the index using keywords
- Simple CLI interface

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Index a directory of papers
python -m research_assistant.cli index --dir /path/to/papers

# Search the index
python -m research_assistant.cli search --query "your query"
```

## License

MIT