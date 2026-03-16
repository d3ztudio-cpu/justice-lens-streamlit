from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials


@dataclass(frozen=True)
class Identity:
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None


class FirebaseAuth:
    def __init__(self, service_account: dict):
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred, {"projectId": service_account.get("project_id")})

    def verify_bearer(self, bearer_token: str) -> Identity:
        decoded = auth.verify_id_token(bearer_token)
        return Identity(
            uid=str(decoded.get("uid") or decoded.get("user_id") or ""),
            email=decoded.get("email"),
            name=decoded.get("name"),
        )


class NullAuth:
    def verify_bearer(self, bearer_token: str) -> Identity:
        raise ValueError("Firebase is not configured")


def build_auth(service_account: Optional[dict]):
    return FirebaseAuth(service_account) if service_account else NullAuth()
