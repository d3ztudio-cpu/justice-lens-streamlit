from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RAG:
    pinecone_index: object
    embeddings: object

    @classmethod
    def create(cls, *, pinecone_api_key: str, index_name: str) -> "RAG":
        from pinecone import Pinecone
        from langchain_huggingface import HuggingFaceEmbeddings

        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(index_name)
        embeddings = HuggingFaceEmbeddings(model_name="nlpaueb/legal-bert-base-uncased")
        return cls(pinecone_index=index, embeddings=embeddings)

    def retrieve_evidence(self, query: str, *, top_k: int = 5) -> str:
        v = self.embeddings.embed_query(query)
        matches = self.pinecone_index.query(vector=v, top_k=top_k, include_metadata=True).get("matches", [])
        text = " ".join([x.get("metadata", {}).get("text", "") for x in matches]).strip()
        return text or "General context."


@dataclass(frozen=True)
class NullRAG:
    def retrieve_evidence(self, query: str, *, top_k: int = 5) -> str:
        return "General context."


def build_rag(*, pinecone_api_key: str, index_name: str):
    if not pinecone_api_key:
        return NullRAG()

    try:
        return RAG.create(pinecone_api_key=pinecone_api_key, index_name=index_name)
    except Exception:
        # If embeddings deps fail to install/import on a host, keep the API up.
        return NullRAG()
