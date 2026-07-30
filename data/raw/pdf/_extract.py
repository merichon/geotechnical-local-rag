#!/usr/bin/env python3
"""Extract text from the downloaded geotechnical PDFs into ../<name>.txt"""
import os
import sys
from pypdf import PdfReader

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))

for fn in sorted(os.listdir(HERE)):
    if not fn.lower().endswith(".pdf"):
        continue
    src = os.path.join(HERE, fn)
    base = os.path.splitext(fn)[0]
    dst = os.path.join(OUT, base + ".txt")
    try:
        reader = PdfReader(src)
        pages = len(reader.pages)
        parts = []
        for p in reader.pages:
            t = p.extract_text() or ""
            if t.strip():
                parts.append(t)
        text = "\n\n".join(parts)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{fn}: {pages} pages -> {len(text):,} chars -> {os.path.basename(dst)}")
    except Exception as e:
        print(f"{fn}: ERROR {e}")
