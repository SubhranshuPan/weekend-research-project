# Deploying Research Assistant From `prod`

This guide deploys the current `prod` branch without changing `master`.

## Assumptions

- The GitHub repo has a pushed `prod` branch.
- The backend is deployed on Render using the included `Dockerfile` and `render.yaml`.
- The frontend is deployed on Vercel or Netlify from the `frontend` directory.
- Uploaded papers and generated indexes are stored on the backend disk mounted at `/app/papers`.

## 1. Confirm the Branch

Locally:

```bash
git switch prod
git pull origin prod
```

The production deployment should use this branch:

```text
prod
```

## 2. Deploy the Backend on Render

1. Open Render and create a new service from the GitHub repository.
2. Select the `prod` branch.
3. Use the root of the repository as the service root.
4. Deploy with Docker. Render should use the root `Dockerfile`.
5. If using Render Blueprints, use the root `render.yaml`.

Set these environment variables on Render:

```text
PAPERS_DIR=/app/papers
CORS_ORIGINS=https://your-frontend-domain
GEMINI_API_KEY=your-gemini-api-key
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

Notes:

- `GEMINI_API_KEY` is optional, but semantic search needs it in production unless you install a local embedding model.
- `CORS_ORIGINS` should be the final Vercel or Netlify URL. For a first smoke test, you can temporarily use `*`, then replace it with the exact frontend URL.
- The included `render.yaml` mounts a 1 GB disk at `/app/papers`.

After Render deploys, copy the backend URL. It should look like:

```text
https://your-render-service.onrender.com
```

Your API base URL is:

```text
https://your-render-service.onrender.com/api
```

## 3. Deploy the Frontend on Vercel

1. Import the GitHub repository into Vercel.
2. Select the `prod` branch.
3. Set the project root directory to:

```text
frontend
```

4. Use these build settings:

```text
Install command: npm install
Build command: npm run build
Output directory: dist
```

5. Add this frontend environment variable:

```text
VITE_API_URL=https://your-render-service.onrender.com/api
```

6. Deploy the project.

## 4. Deploy the Frontend on Netlify

Use this instead of Vercel if you prefer Netlify.

1. Import the GitHub repository into Netlify.
2. Select the `prod` branch.
3. Set the base directory to:

```text
frontend
```

4. Use these build settings:

```text
Build command: npm run build
Publish directory: frontend/dist
```

5. Add this frontend environment variable:

```text
VITE_API_URL=https://your-render-service.onrender.com/api
```

6. Deploy the site.

## 5. Update Backend CORS

After the frontend has a final deployed URL, return to Render and set:

```text
CORS_ORIGINS=https://your-frontend-domain
```

Redeploy or restart the backend after changing the environment variable.

## 6. Smoke Test

Open the deployed frontend and check:

1. The library page loads without browser console API errors.
2. Uploading a small PDF or text file succeeds.
3. The uploaded paper appears in the library.
4. Search returns results for text contained in the uploaded file.
5. If `GEMINI_API_KEY` is set, AI summary, chat, auto-tagging, and semantic graph features work.
6. Opening a paper link loads the file from the backend.

## 7. Troubleshooting

If the frontend cannot reach the backend:

- Confirm `VITE_API_URL` ends with `/api`.
- Confirm Render is running and the backend URL is correct.
- Confirm `CORS_ORIGINS` exactly matches the frontend domain, including `https://`.

If uploads work but files disappear after redeploys:

- Confirm the Render disk is attached.
- Confirm `PAPERS_DIR=/app/papers`.

If semantic search or graph features do not work:

- Confirm `GEMINI_API_KEY` is set on Render.
- Re-upload or re-index papers so embeddings are generated with the production backend.

If AI summary or chat fails:

- Confirm the Gemini key is valid.
- Confirm the frontend request includes the key saved in the app settings, or use the server-side key where supported.

## 8. Current Production Limitation

This deployment keeps paper files, tags, BM25 index data, and embedding files on the Render disk. That is fine for a first production deploy or personal use. For multi-user or highly durable production use, migrate storage to S3, metadata to Postgres or Supabase, and vectors to a managed vector database.
