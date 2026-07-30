#!/usr/bin/env python3
"""
Functional evaluation of the RAG assistant (plan Week 5).

Runs a small suite of test cases against the built knowledge base:
  - answerable questions  -> must retrieve the right source and give an answer
  - unanswerable / off-topic -> must refuse ("bilmiyorum") instead of inventing
  - edge cases (empty / whitespace) -> must not crash

Prereqs:
    foundry server start
    foundry model load phi-4-mini
    python src/ingest.py

Run:
    python tests/test_rag_eval.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from logging_setup import configure_logging
from rag_pipeline import FoundryError, RAGPipeline

DB_PATH = os.path.join(HERE, "..", "data", "rag.db")

# Phrases that signal the model correctly declined to answer.
REFUSAL_MARKERS = [
    "bilmiyorum", "bilgi bulunmam", "bilgi yok", "yer almıyor", "bulunmamakta",
    "don't have", "do not have", "not available", "no relevant", "cannot find",
    "does not contain", "does not provide", "no information", "not mentioned",
]

# Each case: question, expected source substring (or None), should the KB know it?
CASES = [
    # --- answerable (grounded in the knowledge base) ---
    dict(q="Zemin etüdünde en az kaç adet sondaj kuyusu açılır?",
         source="DSI", should_know=True),
    dict(q="Yüzeysel temelin taşıma gücünü hangi faktörler etkiler?",
         source=None, should_know=True),
    dict(q="What is a typical factor of safety against bearing capacity failure?",
         source="FHWA", should_know=True),
    dict(q="Eurocode 7'ye göre zemin araştırmasının amacı nedir?",
         source=None, should_know=True),
    # --- unanswerable / off-topic (must refuse) ---
    dict(q="Bana güzel bir pizza tarifi verir misin?",
         source=None, should_know=False),
]


def contains_any(text, markers):
    t = text.lower()
    return any(m in t for m in markers)


def main():
    configure_logging()
    try:
        rag = RAGPipeline(db_path=DB_PATH)
    except FoundryError as error:
        print(f"\nFoundry Local'e bağlanılamadı:\n{error}\n")
        sys.exit(1)

    print("\n" + "=" * 64)
    print("  RAG FONKSİYONEL DEĞERLENDİRME")
    print("=" * 64 + "\n")

    passed = 0
    total = 0

    for c in CASES:
        total += 1
        result = rag.answer(c["q"], top_k=3)
        answer = result["answer"] or ""
        sources = {s["file"] for s in result["sources"]}

        ok = True
        reasons = []

        if c["should_know"]:
            # right source retrieved?
            if c["source"] and not any(c["source"].lower() in s.lower() for s in sources):
                ok = False
                reasons.append(f"beklenen kaynak '{c['source']}' getirilmedi ({sources})")
            # a real (non-refusal) answer produced?
            if not answer.strip() or contains_any(answer, REFUSAL_MARKERS):
                ok = False
                reasons.append("cevaplanabilir soruya cevap verilemedi")
        else:
            # off-topic: must refuse rather than invent
            if not contains_any(answer, REFUSAL_MARKERS):
                ok = False
                reasons.append("alakasız soruyu reddetmedi (uydurmuş olabilir)")

        passed += ok
        status = "✅ GEÇTİ" if ok else "❌ KALDI"
        print(f"{status}  {c['q']}")
        print(f"        kaynaklar: {', '.join(sorted(sources)) or '(yok)'}")
        print(f"        cevap: {answer.strip()[:140]}...")
        if not ok:
            for r in reasons:
                print(f"        ↳ {r}")
        print()

    # --- edge cases: must not crash ---
    print("-" * 64)
    print("Edge case testleri (çökmemeli):")
    for edge in ["", "   ", "?"]:
        total += 1
        try:
            r = rag.answer(edge, top_k=3)
            assert isinstance(r, dict) and "answer" in r
            passed += 1
            print(f"  ✅ giriş {edge!r} -> güvenli şekilde işlendi")
        except Exception as e:
            print(f"  ❌ giriş {edge!r} -> HATA: {e}")

    rag.close()

    print("\n" + "=" * 64)
    print(f"  SONUÇ: {passed}/{total} test geçti")
    print("=" * 64 + "\n")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
