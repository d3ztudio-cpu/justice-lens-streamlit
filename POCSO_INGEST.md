# Add India cyber records (POCSO + cyber categories)

The app queries a Pinecone index (default: `justice-lens`) for relevant legal snippets.  
To add curated, India-only cyber records (including POCSO-linked cyber patterns like CSAM/grooming/sextortion of minors), ingest the JSONL into the same index.

## What gets added

- `data/india_cyber_law_pocso_cases.jsonl` (POCSO-linked cyber records + common India cyber categories)

## Prereqs

Set environment variables:

- `PINECONE_KEY` (or `PINECONE_API_KEY`)
- optional: `INDEX_NAME` (defaults to `justice-lens`)
- optional: `PINECONE_NAMESPACE` (leave empty unless your index uses one)

## Ingest

```bash
python scripts/pinecone_ingest_jsonl.py --jsonl data/india_cyber_law_pocso_cases.jsonl
```

Dry run (no write):

```bash
python scripts/pinecone_ingest_jsonl.py --dry-run
```

