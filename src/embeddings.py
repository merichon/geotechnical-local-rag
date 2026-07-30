"""Embedding module for RAG - generates vector representations of text."""

import logging
import os

# Force fully-offline operation: load the embedding model from the local
# cache and never contact the HuggingFace Hub at runtime. (To download a NEW
# embedding model, temporarily set these to "0".) Must be set BEFORE importing
# sentence_transformers.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
from sentence_transformers import SentenceTransformer

import logging_setup  # noqa: F401  (UTF-8 safe stdio on import)

logger = logging.getLogger(__name__)

# Multilingual by default: the knowledge base mixes Turkish (DSİ, KGM) and
# English (FHWA, Eurocode) documents, and queries arrive in either language.
DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingService:
    """Generate and manage text embeddings."""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: str = "cpu"):
        """
        Initialize embedding model.

        Args:
            model_name: HuggingFace model identifier (must already be cached
                locally — the hub is disabled above).
            device: torch device. Defaults to "cpu" on purpose so the GPU
                VRAM stays free for the Foundry Local LLM (this tiny model
                runs fine on CPU; sharing the GPU caused CUDA out-of-memory).
        """
        logger.info("Loading embedding model: %s (device=%s)...", model_name, device)
        self.model = SentenceTransformer(model_name, device=device)
        # Renamed in sentence-transformers 5.x; keep working on older versions.
        get_dimension = getattr(self.model, "get_embedding_dimension",
                                self.model.get_sentence_embedding_dimension)
        self.dimension = get_dimension()
        logger.info("✓ Model loaded. Dimension: %d", self.dimension)

    def embed(self, text: str | list[str]) -> np.ndarray:
        """
        Convert text to embedding vector(s).

        Args:
            text: Single string or list of strings

        Returns:
            numpy array of shape (dimension,) for a single string, or
            (n, dimension) for a list.
        """
        return self.model.encode(text)

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Cosine similarity between two embedding vectors (-1..1)."""
        v1 = vec1 / np.linalg.norm(vec1)
        v2 = vec2 / np.linalg.norm(vec2)
        return float(np.dot(v1, v2))
