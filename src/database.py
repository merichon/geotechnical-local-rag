"""Database module for RAG - SQLite operations for storing documents and embeddings."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np

import logging_setup  # noqa: F401  (UTF-8 safe stdio on import)

logger = logging.getLogger(__name__)

# Every read returns the same column set, so build the dict in one place.
_COLUMNS = "id, chunk_id, original_file, content, embedding, chunk_index"


def _row_to_document(row: tuple) -> dict[str, Any]:
    """Map a `_COLUMNS` row to a document dict, decoding the embedding BLOB."""
    return {
        "id": row[0],
        "chunk_id": row[1],
        "original_file": row[2],
        "content": row[3],
        "embedding": np.frombuffer(row[4], dtype=np.float32),
        "chunk_index": row[5],
    }


class RAGDatabase:
    """SQLite database for RAG system."""

    def __init__(self, db_path: str = "./data/rag.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        self.connect()

    def connect(self):
        """Create connection to database.

        check_same_thread=False lets the connection be reused across threads,
        which is required under Streamlit (the pipeline is created in one
        thread via st.cache_resource but queried from another). Safe here
        because access is effectively single-user and serialized.
        """
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.cursor = self.conn.cursor()
        logger.info("✓ Connected to database: %s", self.db_path)

    def setup_schema(self):
        """Create tables and indexes for the RAG system."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE,
                original_file TEXT,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                chunk_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                retrieved_chunks TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_original_file ON documents(original_file)')
        self.cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_chunk_id ON documents(chunk_id)')

        self.conn.commit()
        logger.info("✓ Database schema created")

    def insert_document(self, content: str, embedding: np.ndarray,
                        original_file: str, chunk_index: int = 0,
                        chunk_id: str | None = None) -> int:
        """
        Insert a document chunk with its embedding.

        Args:
            content: text content
            embedding: numpy array embedding (stored as a float32 BLOB)
            original_file: source file name
            chunk_index: position in document
            chunk_id: unique identifier (auto-generated if None); re-ingesting
                the same chunk replaces it instead of duplicating.

        Returns:
            inserted row id
        """
        if chunk_id is None:
            chunk_id = f"{original_file}_chunk_{chunk_index}"

        self.cursor.execute('''
            INSERT OR REPLACE INTO documents
            (chunk_id, original_file, content, embedding, chunk_index)
            VALUES (?, ?, ?, ?, ?)
        ''', (chunk_id, original_file, content,
              embedding.astype(np.float32).tobytes(), chunk_index))

        self.conn.commit()
        return self.cursor.lastrowid

    def get_document(self, doc_id: int) -> dict[str, Any] | None:
        """Retrieve a single document by ID, or None if it doesn't exist."""
        self.cursor.execute(
            f'SELECT {_COLUMNS} FROM documents WHERE id = ?', (doc_id,))
        row = self.cursor.fetchone()
        return _row_to_document(row) if row else None

    def get_all_documents(self) -> list[dict[str, Any]]:
        """Retrieve every stored chunk (the corpus is small enough to scan)."""
        self.cursor.execute(f'SELECT {_COLUMNS} FROM documents')
        return [_row_to_document(row) for row in self.cursor.fetchall()]

    def search_by_content(self, keyword: str) -> list[dict[str, Any]]:
        """Plain substring search over chunk text (used by the setup test)."""
        self.cursor.execute(
            f'SELECT {_COLUMNS} FROM documents WHERE content LIKE ?',
            (f"%{keyword}%",))
        return [_row_to_document(row) for row in self.cursor.fetchall()]

    def save_query(self, question: str, answer: str,
                   retrieved_chunks: list[int]):
        """Record a question, its answer, and which chunks fed it."""
        self.cursor.execute('''
            INSERT INTO queries (question, answer, retrieved_chunks)
            VALUES (?, ?, ?)
        ''', (question, answer, json.dumps(retrieved_chunks)))
        self.conn.commit()

    def close(self):
        """Close the database connection (idempotent)."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("✓ Database connection closed")
