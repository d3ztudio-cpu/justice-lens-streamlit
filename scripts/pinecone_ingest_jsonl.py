import argparse
import json
import os
import sys
from typing import Any

from pinecone import Pinecone

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: langchain-huggingface. Install requirements.txt first."
    ) from exc


def _iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {lineno} in {path}") from e
            yield obj


def _build_text(rec: dict[str, Any]) -> str:
    text = (rec.get("text") or "").strip()
    title = (rec.get("title") or "").strip()
    category = (rec.get("category") or "").strip()
    keywords = rec.get("keywords") or []

    parts = []
    if title:
        parts.append(f"TITLE: {title}")
    if category:
        parts.append(f"CATEGORY: {category}")
    if keywords:
        parts.append("KEYWORDS: " + ", ".join([str(k) for k in keywords if k]))
    if text:
        parts.append(text)
    return "\n\n".join(parts).strip()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Ingest curated India cyber-law JSONL records into Pinecone (Justice Lens index)."
    )
    ap.add_argument(
        "--jsonl",
        default=os.path.join("data", "india_cyber_law_pocso_cases.jsonl"),
        help="Path to JSONL records file.",
    )
    ap.add_argument(
        "--index",
        default=os.environ.get("INDEX_NAME") or os.environ.get("PINECONE_INDEX") or "justice-lens",
        help="Pinecone index name (default: justice-lens).",
    )
    ap.add_argument(
        "--namespace",
        default=os.environ.get("PINECONE_NAMESPACE") or "",
        help="Pinecone namespace (default: empty).",
    )
    ap.add_argument(
        "--api-key",
        default=os.environ.get("PINECONE_KEY") or os.environ.get("PINECONE_API_KEY") or "",
        help="Pinecone API key (reads PINECONE_KEY/PINECONE_API_KEY).",
    )
    ap.add_argument(
        "--model",
        default="nlpaueb/legal-bert-base-uncased",
        help="Embedding model name (default matches app).",
    )
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--dry-run", action="store_true", help="Compute embeddings but do not upsert.")
    args = ap.parse_args(argv)

    if not args.api_key:
        print("Error: missing Pinecone API key. Set PINECONE_KEY (or pass --api-key).", file=sys.stderr)
        return 2

    records = list(_iter_jsonl(args.jsonl))
    if not records:
        print(f"No records found in {args.jsonl}", file=sys.stderr)
        return 2

    embedder = HuggingFaceEmbeddings(model_name=args.model)
    pc = Pinecone(api_key=args.api_key)
    index = pc.Index(args.index)

    batch: list[dict[str, Any]] = []
    texts: list[str] = []

    def flush():
        nonlocal batch, texts
        if not batch:
            return
        vectors = embedder.embed_documents(texts)
        payload = []
        for rec, vec, full_text in zip(batch, vectors, texts, strict=True):
            rid = str(rec.get("id") or "").strip()
            if not rid:
                raise ValueError("Record missing required field: id")
            metadata = {
                "text": full_text,
                "title": (rec.get("title") or "").strip(),
                "category": (rec.get("category") or "").strip(),
                "keywords": rec.get("keywords") or [],
                "jurisdiction": "India",
                "source": "justice-lens-curated",
            }
            payload.append({"id": rid, "values": vec, "metadata": metadata})

        if args.dry_run:
            print(f"DRY RUN: prepared {len(payload)} vectors")
        else:
            index.upsert(vectors=payload, namespace=args.namespace)
            print(f"Upserted {len(payload)} vectors into index='{args.index}' namespace='{args.namespace}'")

        batch = []
        texts = []

    for rec in records:
        batch.append(rec)
        texts.append(_build_text(rec))
        if len(batch) >= args.batch_size:
            flush()

    flush()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))

