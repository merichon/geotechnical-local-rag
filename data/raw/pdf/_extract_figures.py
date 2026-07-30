#!/usr/bin/env python3
"""
Extract real figures FROM THE SOURCE PDFs into ../../../assets/figures/.

Figures are rendered from the page region where each image sits (via its
rect), so they come out in the document's true colors — not hand-drawn and
not the inverted image-masks you get from raw embedded-image extraction.
Writes assets/figures/<source>/fig_*.png and a manifest.json the app reads.
"""
import os
import json
import fitz  # PyMuPDF

HERE = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = HERE
OUT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "assets", "figures"))
MAX_PER_SOURCE = 10


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    manifest = {}

    for fn in sorted(os.listdir(PDF_DIR)):
        if not fn.lower().endswith(".pdf"):
            continue
        base = os.path.splitext(fn)[0]
        doc = fitz.open(os.path.join(PDF_DIR, fn))

        # collect candidate figure rectangles (not tiny icons, not full pages)
        cands = []
        for pno, page in enumerate(doc):
            parea = page.rect.width * page.rect.height
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    rects = page.get_image_rects(xref)
                except Exception:
                    rects = []
                for r in rects:
                    a = r.width * r.height
                    if a <= 0:
                        continue
                    if r.width >= 110 and r.height >= 90 and 0.05 <= a / parea <= 0.72:
                        cands.append((a, pno, fitz.Rect(r)))

        # biggest first, drop near-duplicate rects on the same page
        cands.sort(key=lambda t: -t[0])
        picked, used = [], []
        for a, pno, r in cands:
            if any(pno == p2 and abs(r.x0 - q.x0) < 8 and abs(r.y0 - q.y0) < 8
                   for p2, q in used):
                continue
            picked.append((pno, r))
            used.append((pno, r))
            if len(picked) >= MAX_PER_SOURCE:
                break

        out_dir = os.path.join(OUT_ROOT, base)
        os.makedirs(out_dir, exist_ok=True)
        figs = []
        for i, (pno, r) in enumerate(picked):
            page = doc[pno]
            pad = 6
            clip = fitz.Rect(r.x0 - pad, r.y0 - pad, r.x1 + pad, r.y1 + pad) & page.rect
            pix = page.get_pixmap(clip=clip, dpi=150)
            name = f"fig_{i + 1:02d}_p{pno + 1}.png"
            pix.save(os.path.join(out_dir, name))
            # Text on the figure's page = its topical context. The app embeds
            # this to pick figures RELEVANT to the user's question instead of
            # showing arbitrary figures from the cited document.
            page_text = " ".join((page.get_text() or "").split())[:600]
            figs.append({"file": f"assets/figures/{base}/{name}", "page": pno + 1,
                         "w": int(r.width), "h": int(r.height),
                         "page_text": page_text})

        manifest[base] = figs
        print(f"{base}: {len(figs)} figure(s)")

    with open(os.path.join(OUT_ROOT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"TOTAL {sum(len(v) for v in manifest.values())} figures -> "
          f"assets/figures/manifest.json")


if __name__ == "__main__":
    main()
