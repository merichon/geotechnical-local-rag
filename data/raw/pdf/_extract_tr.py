#!/usr/bin/env python3
"""Re-extract the Turkish (table-heavy) PDFs with pdfplumber.

pypdf fragments tables; pdfplumber's reading-order extract_text() keeps table
rows intact (e.g. "AX 44 45 53"), which matters a lot for the DSİ/KGM specs.
Overwrites the matching ../<name>.txt files.
"""
import os
import re
import warnings
import pdfplumber

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))

TURKISH_PDFS = [
    "DSI_jeoteknik_etut_sartnamesi.pdf",
    "KGM_teknik_sartname.pdf",
]


def clean(text: str) -> str:
    # collapse 3+ blank lines to a single blank line
    return re.sub(r"\n{3,}", "\n\n", text).strip()


for fn in TURKISH_PDFS:
    src = os.path.join(HERE, fn)
    dst = os.path.join(OUT, os.path.splitext(fn)[0] + ".txt")
    parts = []
    with pdfplumber.open(src) as pdf:
        n = len(pdf.pages)
        for p in pdf.pages:
            t = p.extract_text() or ""      # reading-order, keeps table rows
            if t.strip():
                parts.append(t)
    text = clean("\n\n".join(parts))
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{fn}: {n} pages -> {len(text):,} chars (pdfplumber) -> "
          f"{os.path.basename(dst)}")
