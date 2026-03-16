import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


def _read_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_json_env(var_name: str) -> Optional[Dict[str, Any]]:
    raw = os.getenv(var_name)
    if not raw:
        return None
    return json.loads(raw)


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str
    firebase_service_account: Optional[Dict[str, Any]]
    cors_origins: list[str]


def load_settings() -> Settings:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    pinecone_api_key = os.getenv("PINECONE_KEY", "").strip()
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "justice-lens").strip() or "justice-lens"

    firebase_service_account = _read_json_env("FIREBASE_SERVICE_ACCOUNT_JSON")
    if firebase_service_account is None:
        sa_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
        if sa_path and os.path.exists(sa_path):
            firebase_service_account = _read_json_file(sa_path)

    cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").strip()
    cors_origins = [x.strip() for x in cors_raw.split(",") if x.strip()]

    return Settings(
        groq_api_key=groq_api_key,
        pinecone_api_key=pinecone_api_key,
        pinecone_index_name=pinecone_index_name,
        firebase_service_account=firebase_service_account,
        cors_origins=cors_origins,
    )
