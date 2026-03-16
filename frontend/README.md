# Justice Lens Web UI (static)

This is a static HTML/CSS/JS UI inspired by the layout you shared (left nav + center chat + right panel).

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

If your API runs elsewhere, open:

`http://localhost:5173/?apiBase=http://localhost:8000`
