#!/usr/bin/env python3
"""
Environment check - verify every component of the local RAG stack is working.

Covers the four things that break a fresh install: Python packages, the
offline embedding model, SQLite read/write, and the Foundry Local service.

Run:
    python tests/test_setup.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import logging_setup  # noqa: F401  (UTF-8 safe stdio before the first "✓")

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_rag.db")

print("\n" + "=" * 60)
print("  TESTING RAG SETUP")
print("=" * 60 + "\n")

# Test 1: Python packages
print("1. Testing Python packages...")
try:
    import numpy  # noqa: F401
    print("   ✓ numpy")
    import sentence_transformers  # noqa: F401
    print("   ✓ sentence-transformers")
    import torch  # noqa: F401
    print("   ✓ torch")
    import sqlite3  # noqa: F401
    print("   ✓ sqlite3")
    import openai  # noqa: F401
    print("   ✓ openai (Foundry Local client)")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Embedding Service
print("\n2. Testing Embedding Service...")
try:
    from embeddings import DEFAULT_MODEL, EmbeddingService

    # Same model the pipeline uses, so a pass here means the pipeline can load it.
    embedder = EmbeddingService(os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL))

    embed1 = embedder.embed("Foundation depth requirements")
    embed2 = embedder.embed("Soil bearing capacity")
    print(f"   ✓ Embeddings created ({embed1.shape[0]} dimensions)")
    print(f"   ✓ Similarity computed: {embedder.similarity(embed1, embed2):.3f}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 3: Database
print("\n3. Testing Database...")
try:
    import numpy as np
    from database import RAGDatabase

    db = RAGDatabase(TEST_DB)
    db.setup_schema()

    doc_id = db.insert_document(
        content="Test document for foundation design",
        embedding=np.random.randn(embedder.dimension),
        original_file="test.txt",
    )
    print(f"   ✓ Document inserted (ID: {doc_id})")

    doc = db.get_document(doc_id)
    print(f"   ✓ Document retrieved: '{doc['content'][:30]}...'")

    results = db.search_by_content("foundation")
    print(f"   ✓ Search works: found {len(results)} results")

    db.close()
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)
finally:
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

# Test 4: Foundry Local service
print("\n4. Testing Foundry Local...")
try:
    from rag_pipeline import FoundryError, discover_foundry_endpoint
    from openai import OpenAI

    endpoint = discover_foundry_endpoint()
    print(f"   ✓ Service running at {endpoint}")

    models = [m.id for m in OpenAI(base_url=endpoint,
                                   api_key="not-needed").models.list().data]
    if models:
        print(f"   ✓ Loaded models: {len(models)}")
        for model in models[:3]:
            print(f"      - {model}")
    else:
        print("   ⚠ No model loaded: foundry model load phi-4-mini --device GPU")
except FoundryError as e:
    print(f"   ⚠ {e}")
except Exception as e:
    print(f"   ⚠ Foundry check: {e}")

print("\n" + "=" * 60)
print("  SETUP VERIFICATION COMPLETE ✓")
print("=" * 60)
print("""
Next steps:
1. Build the knowledge base:  python src/ingest.py
2. Ask questions in the CLI:  python src/chat.py
3. Or launch the web UI:      run_app.bat
""")
