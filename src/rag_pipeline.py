"""RAG Pipeline - Complete system combining embeddings, database, and LLM.

Generation runs on Microsoft Foundry Local (on-device LLM, fully offline) via
its OpenAI-compatible REST endpoint. Embeddings run locally with
sentence-transformers (Foundry Local's catalog currently ships no embedding
model, and the plan explicitly allows "local ones" for embeddings).
"""

import logging
import os
import re
import subprocess
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

import logging_setup  # noqa: F401  (UTF-8 safe stdio on import)
from database import RAGDatabase
from embeddings import DEFAULT_MODEL as DEFAULT_EMBEDDING_MODEL, EmbeddingService

load_dotenv()

logger = logging.getLogger(__name__)

# Chunking: a specific rule (e.g. "sondaj derinliği en az 2B") has to dominate
# its chunk rather than be diluted among unrelated text. At 1200 chars such
# rules sank to ~25th place in retrieval; at 500 they surface in the top few.
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100

# Retrieval: score added per distinct matched query stem, on top of cosine
# similarity, capped at MAX_KEYWORD_MATCHES stems.
DEFAULT_KEYWORD_BOOST = 0.12
MAX_KEYWORD_MATCHES = 4

# Turkish is agglutinative ("sondajı", "sondajların", "derinlikleri"), so
# keyword matching compares a short stem prefix rather than the whole word.
STEM_LENGTH = 5
MIN_TERM_LENGTH = 4

DEFAULT_LLM_MODEL = "phi-4-mini"


class FoundryError(RuntimeError):
    """Foundry Local is unreachable, or has no usable model loaded."""


def _load_hint(model: str | None = None) -> str:
    """Copy-pasteable commands to get Foundry Local into a working state."""
    model = model or os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
    return (f"  foundry server start\n"
            f"  foundry model load {model}")


# Foundry renamed the CLI group from "service" to "server" in 0.10; try the
# current name first and fall back so both CLI generations work.
_STATUS_COMMANDS = (["foundry", "server", "status"],
                    ["foundry", "service", "status"])


def discover_foundry_endpoint() -> str:
    """Read the running Foundry Local service URL from the CLI status output.

    Returns the base URL including the OpenAI-style `/v1` suffix, e.g.
    "http://127.0.0.1:57480/v1". The port changes every time the daemon
    restarts, so this is re-run instead of hard-coding an endpoint.
    """
    for command in _STATUS_COMMANDS:
        try:
            out = subprocess.run(
                command, capture_output=True, text=True, shell=True).stdout
        except FileNotFoundError:
            raise FoundryError(
                "Foundry CLI not found. Install Foundry Local, then:\n"
                + _load_hint())
        match = re.search(r"http://[\d.]+:\d+", out)
        if match:
            return match.group(0).rstrip("/") + "/v1"

    raise FoundryError(
        "Foundry Local server is not running. Start it with:\n" + _load_hint())


def resolve_model_id(available: list[str], preferred: str | None) -> str:
    """Pick the model id to call from what `/v1/models` reports.

    That endpoint lists every model Foundry has *downloaded*, not just the one
    currently loaded in memory, so taking available[0] can pick a model that
    errors with "is not loaded". Match the requested alias as a substring
    instead: "phi-4-mini" -> "Phi-4-mini-instruct-cuda-gpu:5".
    """
    if not available:
        raise FoundryError(
            "No model available in Foundry Local. Run:\n" + _load_hint())

    if not preferred:
        return available[0]

    match = next(
        (mid for mid in available if preferred.lower() in mid.lower()), None)
    if match is None:
        raise FoundryError(
            f"Requested model '{preferred}' is not available in Foundry.\n"
            f"Available: {available}\n" + _load_hint(preferred))
    return match


class RAGPipeline:
    """Complete Retrieval-Augmented Generation pipeline."""

    def __init__(self, db_path: str = "./data/rag.db",
                 embedding_model: str | None = None,
                 foundry_endpoint: str | None = None,
                 llm_model: str | None = None):
        """
        Initialize RAG pipeline.

        Args:
            db_path: Path to SQLite database
            embedding_model: Sentence-transformers model (local embeddings).
                Defaults to EMBEDDING_MODEL in .env.
            foundry_endpoint: Foundry Local OpenAI endpoint (auto-discovered
                from `foundry service status` if not given)
            llm_model: Short model alias, matched against the loaded Foundry
                models by substring. Defaults to LLM_MODEL in .env.
        """
        logger.info("Initializing RAG Pipeline...")

        self.db = RAGDatabase(db_path)
        self.db.setup_schema()

        # Embedding model/device resolve from .env so the same model is used
        # for ingestion and querying (mismatched models break retrieval).
        embedding_model = embedding_model or os.getenv(
            "EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        self.embedder = EmbeddingService(
            embedding_model, device=os.getenv("EMBEDDING_DEVICE", "cpu"))

        # Connect to Foundry Local (on-device LLM, OpenAI-compatible API).
        self.foundry_endpoint = foundry_endpoint or discover_foundry_endpoint()
        self.client = self._make_client(self.foundry_endpoint)
        self.llm_model = self._resolve_model(llm_model)

        logger.info("✓ Foundry Local LLM: %s", self.llm_model)
        logger.info("✓ RAG Pipeline ready")

    @staticmethod
    def _make_client(endpoint: str) -> OpenAI:
        # Foundry Local needs no auth; the timeout is generous because a cold
        # model load on first call can take a while.
        return OpenAI(base_url=endpoint, api_key="not-needed", timeout=600)

    def _resolve_model(self, llm_model: str | None) -> str:
        """Pick which Foundry model this pipeline should call."""
        available = [m.id for m in self.client.models.list().data]
        return resolve_model_id(available, llm_model or os.getenv("LLM_MODEL"))

    def ingest_document(self, content: str, filename: str,
                        chunk_size: int = DEFAULT_CHUNK_SIZE,
                        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> int:
        """
        Chunk a document, embed each chunk, and store it.

        Args:
            content: Full document text
            filename: Source filename
            chunk_size: Characters per chunk
            chunk_overlap: Characters shared between consecutive chunks so
                context isn't lost at chunk boundaries

        Returns:
            Number of chunks stored.
        """
        logger.info("Ingesting: %s (%d chars)", filename, len(content))

        step = max(1, chunk_size - chunk_overlap)
        chunks = [
            chunk for chunk in (
                content[i:i + chunk_size].strip()
                for i in range(0, len(content), step)
            ) if chunk
        ]
        if not chunks:
            logger.warning("  (no text to ingest)")
            return 0

        # Batch-embed all chunks at once (much faster on CPU than one-by-one).
        embeddings = self.embedder.embed(chunks)

        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            self.db.insert_document(
                content=chunk,
                embedding=embedding,
                original_file=filename,
                chunk_index=idx,
            )

        logger.info("✓ Ingested %d chunks", len(chunks))
        return len(chunks)

    def retrieve(self, query: str, top_k: int = 3,
                 keyword_boost: float = DEFAULT_KEYWORD_BOOST) -> list[dict[str, Any]]:
        """
        Retrieve relevant chunks for a query using HYBRID search.

        Pure vector similarity can miss chunks that state a fact almost
        verbatim when that fact is diluted inside a long chunk. We combine
        semantic (embedding) similarity with a keyword-overlap boost so
        chunks containing the query's significant words rank higher.

        Args:
            query: User question
            top_k: Number of results to return
            keyword_boost: score added per distinct matched query stem, for at
                most MAX_KEYWORD_MATCHES stems, on top of cosine similarity

        Returns:
            Chunks ordered by combined score. Each carries 'similarity_score',
            which is the raw cosine similarity (not the boosted score) so the
            UI reports a meaningful number.
        """
        all_docs = self.db.get_all_documents()
        if not all_docs:
            return []

        query_embedding = self.embedder.embed(query)
        stems = {t[:STEM_LENGTH]
                 for t in re.findall(r"\w+", query.lower())
                 if len(t) > MIN_TERM_LENGTH}

        scored = []
        for doc in all_docs:
            similarity = self.embedder.similarity(query_embedding, doc["embedding"])
            content = doc["content"].lower()
            matches = sum(1 for stem in stems if stem in content)
            combined = similarity + min(matches, MAX_KEYWORD_MATCHES) * keyword_boost
            scored.append((combined, similarity, doc))

        scored.sort(key=lambda item: item[0], reverse=True)

        results = []
        for _combined, similarity, doc in scored[:top_k]:
            doc["similarity_score"] = similarity
            results.append(doc)
        return results

    def generate(self, query: str, context: str) -> str:
        """
        Ask the local LLM to answer `query` using only `context`.

        Raises:
            FoundryError: if the call fails twice (service down or model gone).
        """
        system_prompt = (
            "You are a helpful assistant that answers questions using ONLY the "
            "provided context. If the answer is not in the context, say you "
            "don't have that information - do not make anything up. When you "
            "answer, cite the source file name(s) the information came from. "
            "IMPORTANT: Always write your answer in the SAME language as the "
            "user's question. If the question is in Turkish, answer entirely "
            "in Turkish; if in English, answer in English."
        )
        user_prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer using only the context above and cite the source file(s)."
        )

        # Try once; if the call fails, Foundry has most likely restarted on a
        # NEW port and our cached client points at a dead endpoint — so
        # re-discover the endpoint, rebuild the client, and try again.
        last_error: Exception | None = None
        for attempt in (1, 2):
            try:
                response = self.client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=320,  # concise answers → faster generation
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as error:
                last_error = error
                logger.warning("Foundry call failed (attempt %d): %s", attempt, error)
                if attempt == 2:
                    break
                try:
                    self.foundry_endpoint = discover_foundry_endpoint()
                    self.client = self._make_client(self.foundry_endpoint)
                except FoundryError:
                    break

        raise FoundryError(
            f"Foundry Local call failed: {last_error}\n" + _load_hint())

    def answer(self, query: str, top_k: int = 3) -> dict[str, Any]:
        """
        Complete RAG pipeline: retrieve + generate.

        Never raises for an unreachable model — the error is returned in
        'answer' with 'error' set to True, so the CLI and Streamlit UI can
        display it without crashing mid-conversation.

        Returns:
            Dictionary with query, context, answer, sources, error
        """
        logger.info("Question: %s", query)

        retrieved = self.retrieve(query, top_k)
        if not retrieved:
            return {
                "query": query,
                "context": "",
                "answer": "No relevant documents found in database.",
                "sources": [],
                "error": False,
            }

        context = "\n".join(
            f"[{doc['original_file']}] {doc['content']}" for doc in retrieved)

        logger.info("Retrieved %d documents:", len(retrieved))
        for doc in retrieved:
            logger.info("  [%.3f] %s...", doc["similarity_score"], doc["content"][:60])

        logger.info("Generating answer...")
        try:
            answer = self.generate(query, context)
            failed = False
        except FoundryError as error:
            answer = str(error)
            failed = True

        if not failed:
            self.db.save_query(query, answer, [doc["id"] for doc in retrieved])

        return {
            "query": query,
            "context": context,
            "answer": answer,
            "error": failed,
            "sources": [
                {
                    "file": doc["original_file"],
                    "chunk": doc["chunk_index"],
                    "similarity": doc["similarity_score"],
                    "snippet": " ".join(doc["content"].split())[:240],
                }
                for doc in retrieved
            ],
        }

    def close(self):
        """Close pipeline resources."""
        self.db.close()
