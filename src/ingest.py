#!/usr/bin/env python3
"""
Ingest the geotechnical knowledge base (data/raw/*.txt) into the RAG database.

Plan Week 3: read documents from disk, chunk them, embed each chunk, and
store chunk + embedding in SQLite for later retrieval.

Usage:
    python src/ingest.py            # rebuild DB from all data/raw/*.txt
    python src/ingest.py --append   # add to the existing DB without clearing
"""

import os
import sys
import glob
import time

from logging_setup import configure_logging
from rag_pipeline import RAGPipeline

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RAW_DIR = os.path.join(ROOT, "data", "raw")
DB_PATH = os.path.join(ROOT, "data", "rag.db")


def main():
    configure_logging()
    append = "--append" in sys.argv

    # Fresh build by default so re-running doesn't duplicate chunks.
    if not append and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing DB: {DB_PATH}\n")

    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.txt")))
    if not files:
        print(f"No .txt files found in {RAW_DIR}")
        sys.exit(1)

    print(f"Found {len(files)} document(s) to ingest:\n")
    for f in files:
        print(f"  - {os.path.basename(f)}  ({os.path.getsize(f):,} bytes)")
    print()

    rag = RAGPipeline(db_path=DB_PATH)

    total_chunks = 0
    t0 = time.time()
    for path in files:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        # Chunk size/overlap come from the pipeline defaults so ingestion and
        # retrieval can never drift apart.
        total_chunks += rag.ingest_document(
            content, filename=os.path.basename(path))

    dt = time.time() - t0
    print("=" * 60)
    print(f"  INGESTION COMPLETE: {total_chunks} chunks from {len(files)} "
          f"docs in {dt:.1f}s")
    print("=" * 60 + "\n")

    # Quick verification: one Turkish, one English question over the new KB.
    sample_queries = [
        "Zemin etüdünde sondaj derinliği nasıl belirlenir?",
        "What factors affect the bearing capacity of a shallow foundation?",
    ]
    print("=== VERIFICATION QUERIES ===\n")
    for q in sample_queries:
        result = rag.answer(q, top_k=3)
        print(f"Answer: {result['answer']}\n")
        print("-" * 60 + "\n")

    rag.close()


if __name__ == "__main__":
    main()
