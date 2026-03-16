# Backend failed on Render?

If you see an error like:

`ImportError: Could not import sentence_transformers ...`

Fix:
1) Ensure your service uses `pip install -r backend/requirements.txt`
2) Redeploy

This repo now includes `sentence-transformers` in `backend/requirements.txt`.

If your host still can’t install ML dependencies, the backend will start with a safe fallback (RAG disabled) instead of crashing.
