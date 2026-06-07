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

## Local API

```bash
uvicorn research_assistant.api:app --reload
```

The API stores uploaded papers and generated indexes in `papers` by default.
Copy `.env.example` to `.env` or set these variables in your shell:

- `PAPERS_DIR`: storage directory for uploaded papers and local indexes.
- `CORS_ORIGINS`: comma-separated frontend origins. Use your Vercel/Netlify URL in production.
- `GEMINI_API_KEY`: optional server-side key for API-based semantic embeddings.
- `GEMINI_EMBEDDING_MODEL`: defaults to `text-embedding-004`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` to the deployed backend API URL, for example:

```bash
VITE_API_URL=https://your-render-service.onrender.com/api
```

## Deployment Notes

- Deploy the frontend to Vercel or Netlify with `frontend` as the project root.
- Deploy the backend with the included `Dockerfile` or `render.yaml`.
- On Render, set `CORS_ORIGINS` to your frontend URL and `GEMINI_API_KEY` if you want semantic search without installing `sentence-transformers`.
- This first deployment still uses backend disk storage. The included Render config mounts `/app/papers`; use S3/Postgres/vector storage next if you need durable multi-instance production storage.

## CLI Usage

```bash
# Index a directory of papers
python -m research_assistant.cli index --dir /path/to/papers

# Search the index
python -m research_assistant.cli search --query "your query"
```

## License

MIT
