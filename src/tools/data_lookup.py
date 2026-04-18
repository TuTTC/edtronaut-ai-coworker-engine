"""
FAISS-based vector store and data lookup for RAG retrieval.
Uses TF-IDF embeddings for the mock prototype — swappable for dense embeddings.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Try FAISS first, fall back to numpy-based search
try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger.warning("faiss-cpu not installed — falling back to NumPy cosine similarity")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not installed — using basic keyword matching")


class VectorStore:
    """
    A lightweight vector store backed by FAISS + TF-IDF.
    Falls back gracefully if FAISS or sklearn are unavailable.
    """

    def __init__(self, documents: list[dict[str, str]]):
        """
        Args:
            documents: list of {"id": ..., "content": ..., "source": ...}
        """
        self.documents = documents
        self.texts = [doc["content"] for doc in documents]
        self.index = None
        self.vectorizer = None

        if HAS_SKLEARN and self.texts:
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),
            )
            vectors = self.vectorizer.fit_transform(self.texts).toarray().astype(np.float32)

            if HAS_FAISS and vectors.shape[0] > 0:
                dim = vectors.shape[1]
                self.index = faiss.IndexFlatIP(dim)
                faiss.normalize_L2(vectors)
                self.index.add(vectors)
                logger.info(f"FAISS index built: {len(documents)} docs, dim={dim}")
            else:
                # Store raw vectors for numpy fallback
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self._vectors = vectors / norms
                logger.info(f"NumPy index built: {len(documents)} docs")

    def search(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """Search for the top-k most relevant documents."""
        if not self.texts:
            return []

        # TF-IDF + FAISS path
        if self.vectorizer is not None:
            query_vec = self.vectorizer.transform([query]).toarray().astype(np.float32)
            faiss.normalize_L2(query_vec) if HAS_FAISS else None

            if self.index is not None:
                scores, indices = self.index.search(query_vec, min(k, len(self.texts)))
                results = []
                for j, i in enumerate(indices[0]):
                    if i >= 0:
                        results.append({
                            "document": self.documents[i],
                            "score": float(scores[0][j]),
                        })
                return results
            elif hasattr(self, "_vectors"):
                # NumPy fallback
                qv = query_vec / (np.linalg.norm(query_vec) + 1e-10)
                scores = self._vectors @ qv.T
                top_k = np.argsort(scores.flatten())[::-1][:k]
                return [
                    {"document": self.documents[i], "score": float(scores[i])}
                    for i in top_k
                ]

        # Keyword fallback
        return self._keyword_search(query, k)

    def _keyword_search(self, query: str, k: int) -> list[dict[str, Any]]:
        """Simple keyword-overlap scoring."""
        query_words = set(query.lower().split())
        scored = []
        for doc in self.documents:
            doc_words = set(doc["content"].lower().split())
            overlap = len(query_words & doc_words)
            if overlap > 0:
                scored.append((overlap, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"document": doc, "score": float(score)}
            for score, doc in scored[:k]
        ]


class DataLookup:
    """
    High-level data lookup that loads all mock data and builds a vector store.
    Tools call this to retrieve context for NPC responses.
    """

    def __init__(self, data_dir: Path | None = None):
        from ..config import DATA_DIR
        self.data_dir = data_dir or DATA_DIR
        self._raw_data: dict[str, Any] = {}
        self._vector_store: VectorStore | None = None
        self._load_data()

    def _load_data(self):
        """Load all JSON and Markdown data files."""
        # JSON files
        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    self._raw_data[json_file.stem] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        # Build documents for vector store
        documents = []

        # Flatten JSON data into text chunks
        for source, data in self._raw_data.items():
            chunks = self._flatten_to_chunks(data, source)
            documents.extend(chunks)

        # Load policy markdown files
        policies_dir = self.data_dir / "policies"
        if policies_dir.exists():
            for md_file in policies_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    # Split into sections
                    sections = content.split("\n### ")
                    for i, section in enumerate(sections):
                        if section.strip():
                            documents.append({
                                "id": f"{md_file.stem}_section_{i}",
                                "content": section.strip(),
                                "source": md_file.stem,
                            })
                except Exception as e:
                    logger.error(f"Failed to load {md_file}: {e}")

        self._vector_store = VectorStore(documents)
        logger.info(f"DataLookup initialized: {len(documents)} document chunks")

    def _flatten_to_chunks(
        self, data: Any, source: str, prefix: str = ""
    ) -> list[dict[str, str]]:
        """Recursively flatten nested JSON into text chunks."""
        chunks = []
        if isinstance(data, dict):
            for key, value in data.items():
                path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str):
                    chunks.append({
                        "id": f"{source}_{path}",
                        "content": f"{key}: {value}",
                        "source": source,
                    })
                elif isinstance(value, list):
                    text_items = [
                        str(item) if not isinstance(item, dict)
                        else json.dumps(item, ensure_ascii=False)
                        for item in value
                    ]
                    chunks.append({
                        "id": f"{source}_{path}",
                        "content": f"{key}: " + "; ".join(text_items),
                        "source": source,
                    })
                elif isinstance(value, dict):
                    chunks.extend(self._flatten_to_chunks(value, source, path))
        return chunks

    def search(self, query: str, k: int = 3) -> list[dict]:
        """Search across all loaded data."""
        if self._vector_store:
            return self._vector_store.search(query, k)
        return []

    def get_raw(self, key: str) -> Any:
        """Direct access to a raw data file by stem name."""
        return self._raw_data.get(key)

    def lookup_group_data(self, query: str) -> str:
        """Tool: Look up Gucci Group data (CEO knowledge)."""
        results = self.search(query, k=3)
        if results:
            return "\n\n".join(
                f"[{r['document']['source']}] {r['document']['content']}"
                for r in results
            )
        return "No relevant data found."

    def lookup_hr_framework(self, query: str) -> str:
        """Tool: Look up HR/competency framework data (CHRO knowledge)."""
        results = self.search(query, k=3)
        hr_results = [
            r for r in results
            if r["document"]["source"] in ("competency_framework", "hr_metrics", "competency_framework")
        ]
        if hr_results:
            return "\n\n".join(
                f"[{r['document']['source']}] {r['document']['content']}"
                for r in hr_results
            )
        # Fallback to all results
        if results:
            return "\n\n".join(
                f"[{r['document']['source']}] {r['document']['content']}"
                for r in results
            )
        return "No relevant HR data found."

    def lookup_regional_data(self, query: str) -> str:
        """Tool: Look up regional Europe data (RM knowledge)."""
        results = self.search(query, k=3)
        regional_results = [
            r for r in results
            if r["document"]["source"] in ("regional_europe", "regional_rollout")
        ]
        if regional_results:
            return "\n\n".join(
                f"[{r['document']['source']}] {r['document']['content']}"
                for r in regional_results
            )
        if results:
            return "\n\n".join(
                f"[{r['document']['source']}] {r['document']['content']}"
                for r in results
            )
        return "No relevant regional data found."
