# Justice Lens Web UI (static)

This is a static HTML/CSS/JS UI inspired by the layout you shared (left nav + center chat + right panel).

## Configure backend URL

In production, click the **API** button in the top bar and paste your backend URL (example: `https://your-api.onrender.com`).

Alternatively you can set it via URL:

`https://your-pages-site.pages.dev/?apiBase=https://your-api.onrender.com`

## Run locally

1) Start backend:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

2) Serve this folder (any static server works). Example:

```bash
python -m http.server 5173 --directory frontend
```

Open: `http://localhost:5173`
