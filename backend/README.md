# Justice Lens API (FastAPI)

This folder adds a Python backend API so you can build a separate web UI (instead of Streamlit) while keeping the same core logic:

- Groq chat (intent + report generation)
- Pinecone retrieval (RAG evidence)
- Optional Firebase ID-token verification

## Run locally

1) Install deps:

```bash
pip install -r backend/requirements.txt
```

2) Set env vars:

- `GROQ_API_KEY` (required)
- `PINECONE_KEY` (optional; if omitted, RAG uses “General context.”)
- `PINECONE_INDEX_NAME` (optional; default: `justice-lens`)
- `CORS_ORIGINS` (optional; default: `http://localhost:5173,http://localhost:3000`)
- Firebase (optional; for auth):
  - `FIREBASE_SERVICE_ACCOUNT_JSON` (JSON string), OR
  - `FIREBASE_SERVICE_ACCOUNT_PATH` (path to a service account JSON file)

3) Start API:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`

Chat: `POST http://localhost:8000/api/chat` body:

```json
{ "message": "Explain Section 66F" }
```

If using Firebase auth, send `Authorization: Bearer <id_token>` header.
