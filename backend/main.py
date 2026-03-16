from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.authn import Identity, build_auth
from backend.config import load_settings
from backend.logic import ChatResult, GroqClient, ask_groq_lawyer_validated, classify_intent
from backend.rag import build_rag


settings = load_settings()

groq = GroqClient(api_key=settings.groq_api_key)
rag = build_rag(pinecone_api_key=settings.pinecone_api_key, index_name=settings.pinecone_index_name)
authn = build_auth(settings.firebase_service_account)


app = FastAPI(title="Justice Lens API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class ChatResponse(BaseModel):
    category: str
    answer: str


def _get_identity(authorization: Optional[str]) -> Optional[Identity]:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        ident = authn.verify_bearer(token)
        if not ident.uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        return ident
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, authorization: Optional[str] = Header(default=None)):
    if not settings.groq_api_key:
        raise HTTPException(status_code=500, detail="Server missing GROQ_API_KEY")

    _ = _get_identity(authorization)
    msg = payload.message.strip()

    category = classify_intent(groq, msg)
    if category == "PHYSICAL":
        answer = "⚠️ This tool handles cyber crimes only. For other types of crimes, file an FIR under IPC."
        return ChatResponse(category=category, answer=answer)
    if category == "NON_LEGAL":
        answer = "ℹ️ I can only help with cyber-law topics (IT Act / cybercrime). Ask a cyber-legal question and I’ll help."
        return ChatResponse(category=category, answer=answer)

    evidence = rag.retrieve_evidence(msg, top_k=5)
    answer = ask_groq_lawyer_validated(groq, msg, evidence, category)
    result = ChatResult(category=category, answer=answer)
    return ChatResponse(category=result.category, answer=result.answer)


def _mount_frontend_if_enabled() -> None:
    enabled = os.getenv("SERVE_FRONTEND", "").strip().lower() in ("1", "true", "yes")
    if not enabled:
        return

    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if not frontend_dir.exists():
        return

    # Mount last so /api/* routes still win.
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


_mount_frontend_if_enabled()
