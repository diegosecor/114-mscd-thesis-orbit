"""Persistent Chroma retrieval over original abstracts, using local multilingual vectors.

Two collections serve different purposes: passages answer a text query; normalized
means of a thesis's passage vectors support thesis recommendations and a PCA map.
No category, advisor or year is embedded: those remain exact metadata filters.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from pathlib import Path

import chromadb
import numpy as np
from chromadb.config import Settings
from fastembed import TextEmbedding
from research_clusters import cluster_profiles

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_models: dict[str, TextEmbedding] = {}
_model_lock = threading.Lock()
_indexes: dict[str, "SemanticIndex"] = {}
_index_lock = threading.Lock()


# Prefer the original abstract; retain provenance when falling back to user text.
def passages(record: dict) -> tuple[list[str], str]:
    body = record.get("source_abstract") or record.get("ai_summary") or record.get("keywords") or record["title"]
    source = "Original abstract" if record.get("source_abstract") else "User description / summary"
    words = re.findall(r"\S+", body)
    chunks = []
    # Short overlapping passages fit the small multilingual sentence encoder.
    # This is the complete abstract, not sampled pages or generated additions.
    for start in range(0, len(words), 58):
        chunk = words[start:start + 70]
        if start and len(chunk) <= 12:
            break
        chunks.append(f"{record['title']}\n\n{' '.join(chunk)}")
        if start + 70 >= len(words):
            break
    return chunks or [record["title"]], source


# Hash index-relevant content so unchanged theses do not need re-embedding.
def fingerprint(record: dict) -> str:
    fields = {key: record.get(key) for key in (
        "title", "source_abstract", "ai_summary", "keywords", "category", "advisors", "year"
    )}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class SemanticIndex:
    # Open two persistent cosine collections with explicit locally computed vectors.
    def __init__(self, data_dir: Path, *, model_cache: Path | None = None):
        self.data_dir = Path(data_dir)
        self.model_cache = model_cache or self.data_dir / "model-cache"
        self.lock = threading.RLock()
        self.client = chromadb.PersistentClient(
            path=str(self.data_dir / "chroma_store"),
            settings=Settings(anonymized_telemetry=False),
        )
        self.profiles = self.client.get_or_create_collection(
            "thesis_profiles_multilingual_v1", embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}}, metadata={"model": MODEL},
        )
        self.chunks = self.client.get_or_create_collection(
            "thesis_passages_multilingual_v1", embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}}, metadata={"model": MODEL},
        )
        self._map = None

    # Share one cached CPU encoder per model directory and process texts in batches.
    def embed(self, texts: list[str]) -> list[list[float]]:
        cache = str(self.model_cache.resolve())
        with _model_lock:
            if cache not in _models:
                _models[cache] = TextEmbedding(MODEL, cache_dir=cache, threads=4)
            model = _models[cache]
        return [vector.tolist() for vector in model.embed(texts, batch_size=16)]

    # Replace a thesis's passages and normalized mean profile, then invalidate the map.
    def upsert(self, record: dict) -> None:
        with self.lock:
            texts, source = passages(record)
            vectors = self.embed(texts)
            mean = np.mean(vectors, axis=0)
            mean /= max(float(np.linalg.norm(mean)), 1e-12)
            thesis_id = int(record["id"])
            metadata = {
                "thesis_id": thesis_id, "title": record["title"],
                "category": record.get("category") or "Uncategorized",
                "advisors": record.get("advisors") or "",
                "year": record.get("year") or 0,
                "fingerprint": fingerprint(record), "source": source,
            }
            self.chunks.delete(where={"thesis_id": thesis_id})
            self.chunks.upsert(
                ids=[f"{thesis_id}:{i}" for i in range(len(texts))], documents=texts,
                embeddings=vectors,
                metadatas=[{**metadata, "passage": i + 1} for i in range(len(texts))],
            )
            # Profile fingerprint is the final commit marker for synchronization.
            self.profiles.upsert(ids=[str(thesis_id)], documents=[record["title"]],
                                 embeddings=[mean.tolist()], metadatas=[metadata])
            self._map = None

    # Delete both passage and profile vectors, invalidating derived visual groups.
    def remove(self, thesis_id: int) -> None:
        with self.lock:
            self.chunks.delete(where={"thesis_id": int(thesis_id)})
            self.profiles.delete(ids=[str(thesis_id)])
            self._map = None

    # Reconcile the visible corpus using fingerprints and remove stale vectors.
    def synchronize(self, records: list[dict]) -> None:
        with self.lock:
            stored = self.profiles.get(include=["metadatas"])
            existing = dict(zip(stored["ids"], stored["metadatas"]))
            wanted = {str(record["id"]) for record in records}
            for stale_id in existing.keys() - wanted:
                self.remove(int(stale_id))
            for record in records:
                previous = existing.get(str(record["id"]), {})
                if previous.get("fingerprint") != fingerprint(record):
                    print(f"Embedding thesis {record['id']}: {record['title'][:60]}", flush=True)
                    self.upsert(record)

    # Cache PCA display coordinates and clusters from original embedding dimensions.
    def map(self) -> dict:
        with self.lock:
            if self._map is not None:
                return self._map
            stored = self.profiles.get(include=["embeddings", "metadatas"])
            points = {}
            variance = []
            if stored["ids"]:
                matrix = np.asarray(stored["embeddings"], dtype=float)
                centered = matrix - matrix.mean(axis=0)
                u, singular, vh = np.linalg.svd(centered, full_matrices=False)
                dims = min(3, len(singular))
                coordinates = u[:, :dims] * singular[:dims]
                for axis in range(dims):
                    if vh[axis, np.argmax(np.abs(vh[axis]))] < 0:
                        coordinates[:, axis] *= -1
                coordinates = np.pad(coordinates, ((0, 0), (0, 3 - dims)))
                scale = max(float(np.linalg.norm(coordinates, axis=1).max()), 1e-12)
                coordinates *= 320 / scale
                points = {key: dict(zip(("x", "y", "z"), row.tolist()))
                          for key, row in zip(stored["ids"], coordinates)}
                total_variance = float(np.sum(singular ** 2))
                variance = (singular[:dims] ** 2 / max(total_variance, 1e-12)).tolist()
            self._map = {"points": points, "model": MODEL, "dimensions": 384,
                         "theses": len(points), "passages": self.chunks.count(),
                         "projection": "PCA", "explained_variance": variance}
            # Group in the original space: projected screen distances lose information.
            self._map["constellations"] = cluster_profiles(
                stored["ids"], stored["embeddings"],
                [metadata["title"] for metadata in stored["metadatas"]])
            return self._map

    # Rank eligible thesis profiles by cosine similarity, excluding the selected seed.
    def neighbors(self, thesis_id: int, *, ids: list[int] | None = None,
                  k: int = 8, minimum: float = 0.35) -> list[dict]:
        with self.lock:
            seed = self.profiles.get(ids=[str(thesis_id)], include=["embeddings"])
            if not seed["ids"]:
                raise KeyError("This thesis has not been indexed.")
            available = self.profiles.get(include=["metadatas"])
            allowed = {int(key) for key in available["ids"]}
            if ids is not None:
                allowed.intersection_update(ids)
            allowed.discard(thesis_id)
            if not allowed:
                return []
            result = self.profiles.query(
                query_embeddings=[seed["embeddings"][0].tolist()],
                where={"thesis_id": {"$in": sorted(allowed)}},
                n_results=min(k, len(allowed)), include=["distances", "metadatas"],
            )
            return [{"id": int(key), "similarity": round(1 - distance, 5),
                     "title": meta["title"]}
                    for key, distance, meta in zip(result["ids"][0], result["distances"][0], result["metadatas"][0])
                    if 1 - distance >= minimum]

    # Rank passages, then keep each thesis's best matching source excerpt.
    def search(self, query: str, *, ids: list[int], k: int = 20) -> list[dict]:
        with self.lock:
            if not ids or not self.chunks.count():
                return []
            result = self.chunks.query(
                query_embeddings=self.embed([query]), where={"thesis_id": {"$in": ids}},
                n_results=self.chunks.count(), include=["documents", "metadatas", "distances"],
            )
            matches = {}
            for document, metadata, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
                key = metadata["thesis_id"]
                if key not in matches:
                    matches[key] = {"id": key, "similarity": round(1 - distance, 5),
                                    "excerpt": document.split("\n\n", 1)[-1],
                                    "passage": metadata["passage"], "source": metadata["source"]}
            return list(matches.values())[:k]


# Reuse one thread-safe index wrapper for each resolved data directory.
def get_index(data_dir: Path) -> SemanticIndex:
    key = str(Path(data_dir).resolve())
    with _index_lock:
        if key not in _indexes:
            _indexes[key] = SemanticIndex(Path(data_dir))
        return _indexes[key]
