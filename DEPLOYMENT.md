# Hosting (website) options

You can deploy this in two ways:

## 1) Single deploy (easiest): backend serves the UI

This repo includes:
- `backend/` FastAPI API
- `frontend/` static UI

If you set `SERVE_FRONTEND=true`, FastAPI serves `frontend/` at `/` and your API is at `/api/*`.

### Render (recommended for beginners)

1) Push this repo to GitHub.
2) Go to Render → New → Blueprint.
3) Select your repo. Render will detect `render.yaml` and create the service.
4) In Render → service → Environment, set:
   - `GROQ_API_KEY`
   - `PINECONE_KEY` (optional)
   - `CORS_ORIGINS` (set to your Render URL, e.g. `https://justice-lens.onrender.com`)
   - `SERVE_FRONTEND=true`
5) Deploy. Open your Render URL.

## 2) Split deploy: host frontend + backend separately

### Backend
Deploy `backend/` using `backend/Dockerfile` and set `CORS_ORIGINS` to your frontend domain.

### Frontend
Deploy `frontend/` to Vercel/Netlify/GitHub Pages and set API base:
- Edit `frontend/app.js` `DEFAULT_API_BASE`, OR
- Use `?apiBase=https://your-api.example`.

## Local run (2 terminals)

Backend:
```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Frontend:
```bash
python -m http.server 5173 --directory frontend
```

Open: `http://localhost:5173`
