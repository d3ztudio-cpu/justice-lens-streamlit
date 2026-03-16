# Hosting (website) options

If your frontend is on **Cloudflare Pages**, it is static and cannot run Python.
So your app must be:
- **Frontend:** Cloudflare Pages (`frontend/`)
- **Backend:** another host (Render/Fly/Railway/etc) running `backend/main.py`

## Cloudflare Pages (frontend)

Build settings:
- Framework preset: `None`
- Root directory (advanced): `frontend`
- Build command: (empty)
- Build output directory: `.`

After deploy, open your Pages URL.

## Backend (FastAPI)

Deploy using `backend/Dockerfile`.
Set environment variables in your backend host:
- `GROQ_API_KEY` (required)
- `PINECONE_KEY` (optional)
- `PINECONE_INDEX_NAME` (optional; default `justice-lens`)
- `CORS_ORIGINS` (set to your Pages URL, e.g. `https://justice-lens-streamlit.pages.dev`)

Optional (Firebase auth):
- `FIREBASE_SERVICE_ACCOUNT_JSON` or `FIREBASE_SERVICE_ACCOUNT_PATH`

## Connect frontend to backend

On your deployed website, click **API** (top bar) and paste your backend URL, e.g. `https://your-api.onrender.com`.

Or add to your website URL:

`?apiBase=https://your-api.onrender.com`
