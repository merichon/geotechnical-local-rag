#!/usr/bin/env python3
"""
Streamlit web UI for the local geotechnical RAG assistant.

Runs fully offline: Foundry Local LLM +
sentence-transformers embeddings + SQLite knowledge base.
"""

import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

import streamlit as st
from logging_setup import configure_logging
from rag_pipeline import FoundryError, RAGPipeline

configure_logging()

DB_PATH = os.path.join(HERE, "data", "rag.db")

st.set_page_config(page_title="Geoteknik Asistan", page_icon="🪨", layout="centered")


@st.cache_resource(show_spinner="Model ve bilgi tabanı yükleniyor… (ilk açılışta biraz sürer)")
def get_rag():
    return RAGPipeline(db_path=DB_PATH)


@st.cache_data
def load_figures():
    """Figure manifest extracted from the source PDFs (assets/figures/)."""
    p = os.path.join(HERE, "assets", "figures", "manifest.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {}


FIGURES = load_figures()


@st.cache_resource(show_spinner=False)
def figure_index(_rag):
    """Embed each figure's page text once → lets us rank figures by relevance
    to the user's question instead of showing arbitrary ones."""
    flat = []
    for base, figs in FIGURES.items():
        for f in figs:
            if f.get("page_text"):
                flat.append({"base": base, **f})
    if not flat:
        return [], None
    embs = _rag.embedder.embed([f["page_text"] for f in flat])
    return flat, embs


def relevant_figures(rag, query, cited_files, n=3, min_sim=0.30):
    """Top-n figures from the cited documents, ranked by similarity between
    the question and each figure's page text. Below min_sim → show nothing
    (no figure is better than a random one)."""
    flat, embs = figure_index(rag)
    if not flat:
        return []
    cited_bases = {f.rsplit(".", 1)[0] for f in cited_files}
    q_emb = rag.embedder.embed(query)
    scored = []
    for fig, emb in zip(flat, embs):
        if fig["base"] not in cited_bases:
            continue
        scored.append((rag.embedder.similarity(q_emb, emb), fig))
    scored.sort(key=lambda x: -x[0])
    return [(s, f) for s, f in scored[:n] if s >= min_sim]


st.title("🪨 Geoteknik Soru-Cevap Asistanı")
st.caption("Yerel / offline · Foundry Local + RAG · Kaynaklar: DSİ, KGM, FHWA, Eurocode 7")

try:
    rag = get_rag()
except FoundryError as e:
    st.error(f"Foundry Local'e bağlanılamadı:\n\n```\n{e}\n```")
    st.stop()

with st.sidebar:
    st.subheader("Bilgi")
    st.write(f"**Model:** `{rag.llm_model}`")
    st.write("**Bilgi tabanı:** data/rag.db")
    n_figs = sum(len(v) for v in FIGURES.values())
    st.write(f"**Belgelerden çıkarılan şekil:** {n_figs}")
    top_k = st.slider("Kaç belge getirilsin (top-k)", 1, 6, 3)
    if st.button("Sohbeti temizle"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Bir geoteknik soru sor… (TR veya EN)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor…"):
            result = rag.answer(prompt, top_k=top_k)

        if result.get("error"):
            # Model unreachable — show it as a failure, not as an answer.
            st.error(result["answer"])
        else:
            st.markdown(result["answer"])

        sources = result["sources"]
        if sources and not result.get("error"):
            # retrieved sources with a short snippet (plan: log retrieved chunks)
            seen = set()
            with st.expander("📎 Kaynaklar ve getirilen metin"):
                for s in sources:
                    key = (s["file"], s["chunk"])
                    if key in seen:
                        continue
                    seen.add(key)
                    st.markdown(
                        f"**{s['file']}** — parça {s['chunk']} "
                        f"(benzerlik {s['similarity']:.2f})"
                    )
                    st.caption(s.get("snippet", ""))

            # figures from the cited documents, ranked by relevance to the question
            cited = [s["file"] for s in sources]
            figs = relevant_figures(rag, prompt, cited, n=3)
            if figs:
                st.markdown("**📐 Soruyla ilgili şekiller (kaynak belgelerden):**")
                cols = st.columns(len(figs))
                for col, (score, fig) in zip(cols, figs):
                    img_path = os.path.join(HERE, fig["file"])
                    col.image(
                        img_path,
                        caption=f"{fig['base']} · sayfa {fig['page']} "
                                f"(alaka {score:.2f})",
                        use_container_width=True,
                    )

    st.session_state.messages.append(
        {"role": "assistant", "content": result["answer"]}
    )
