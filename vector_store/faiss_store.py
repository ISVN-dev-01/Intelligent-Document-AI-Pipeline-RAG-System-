"""Exact cosine FAISS index with checksummed JSON metadata and atomic snapshots.

No pickle or LangChain dangerous-deserialization switch is used. A manifest is
published only after both snapshot files have been durably written.
"""
import hashlib
import json
import os
import re
from pathlib import Path
from uuid import uuid4

import faiss
import numpy as np
from filelock import FileLock
from pydantic import BaseModel, Field

from utils.errors import StorageError
from utils.logging_config import event


class ChunkMetadata(BaseModel):
    document_id: str
    document_name: str
    page_number: int = Field(ge=1)
    chunk_id: str
    source: str
    created_at: str


class StoredChunk(BaseModel):
    text: str = Field(min_length=1)
    metadata: ChunkMetadata


class RetrievedChunk(BaseModel):
    text: str
    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    score: float
    label: str = ""


def write_durable(path: Path, data: bytes):
    with path.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def normalized(vectors):
    array = np.array(vectors, dtype="float32", order="C", copy=True)
    if array.ndim != 2 or not array.shape[0] or not array.shape[1]:
        raise StorageError("Embedding provider returned an invalid vector shape.")
    if not np.isfinite(array).all() or (np.linalg.norm(array, axis=1) == 0).any():
        raise StorageError("Embedding provider returned an invalid or zero vector.")
    faiss.normalize_L2(array)
    return array


class FaissStore:
    def __init__(self, directory: Path, fingerprint: str):
        self.directory = directory
        self.fingerprint = fingerprint
        directory.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(directory / "index.lock"), timeout=120)
        self.index = None
        self.chunks: list[StoredChunk] = []
        self.generation = None
        with self.lock:
            self._reload()

    def _reload(self):
        path = self.directory / "manifest.json"
        if not path.exists():
            if self.generation is not None:
                raise StorageError("The vector manifest is missing. Restore a consistent backup.")
            return
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if manifest["fingerprint"] != self.fingerprint:
                raise StorageError("Embedding model differs from the saved index. Use a new DATA_DIR and re-ingest.")
            generation = manifest["generation"]
            if not re.fullmatch(r"[a-f0-9]{32}", generation):
                raise ValueError("Invalid generation")
            if generation == self.generation:
                return
            index_bytes = (self.directory / f"{generation}.faiss").read_bytes()
            metadata_bytes = (self.directory / f"{generation}.json").read_bytes()
            for data, key in ((index_bytes, "index_sha256"), (metadata_bytes, "metadata_sha256")):
                if hashlib.sha256(data).hexdigest() != manifest[key]:
                    raise ValueError("Snapshot checksum mismatch")
            metadata = json.loads(metadata_bytes)
            chunks = [StoredChunk.model_validate(row) for row in metadata]
            index = faiss.deserialize_index(np.frombuffer(index_bytes, dtype=np.uint8).copy())
            if index.ntotal != len(chunks) or index.metric_type != faiss.METRIC_INNER_PRODUCT:
                raise ValueError("Index and metadata mismatch")
            if len({chunk.metadata.chunk_id for chunk in chunks}) != len(chunks):
                raise ValueError("Duplicate chunk identifiers")
            self.index, self.chunks, self.generation = index, chunks, generation
        except StorageError:
            raise
        except Exception:
            raise StorageError("The vector index is unreadable or inconsistent. Restore a backup; do not load untrusted index files.") from None

    def _save(self, index, chunks):
        generation = uuid4().hex
        index_bytes = faiss.serialize_index(index).tobytes()
        metadata_bytes = json.dumps([chunk.model_dump() for chunk in chunks], ensure_ascii=False).encode()
        manifest = {"version": 1, "generation": generation, "fingerprint": self.fingerprint,
                    "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
                    "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest()}
        try:
            write_durable(self.directory / f"{generation}.faiss", index_bytes)
            write_durable(self.directory / f"{generation}.json", metadata_bytes)
            temporary = self.directory / "manifest.pending"
            write_durable(temporary, json.dumps(manifest).encode())
            os.replace(temporary, self.directory / "manifest.json")
        except OSError:
            raise StorageError("Unable to save the vector index. Check free space and directory permissions.") from None
        self.index, self.chunks, self.generation = index, chunks, generation
        # Remove unpublished/old generations while holding the inter-process lock.
        for path in self.directory.iterdir():
            if (re.fullmatch(r"[a-f0-9]{32}\.(faiss|json)", path.name)
                    and path.stem != generation):
                try:
                    path.unlink()
                except OSError:
                    event("snapshot_cleanup_failure")
        event("vector_index_saved", vectors=len(chunks))

    def add(self, chunks, vectors):
        with self.lock:
            self._reload()
            array = normalized(vectors)
            if len(chunks) != len(array):
                raise StorageError("The embedding count does not match the chunk count.")
            if self.index is not None and self.index.d != array.shape[1]:
                raise StorageError("Embedding dimensions differ from the saved index.")
            rows = [StoredChunk(text=c.page_content, metadata=ChunkMetadata(**c.metadata)) for c in chunks]
            ids = [c.metadata.chunk_id for c in self.chunks + rows]
            if len(ids) != len(set(ids)):
                raise StorageError("Duplicate chunk IDs cannot be indexed.")
            updated = faiss.clone_index(self.index) if self.index is not None else faiss.IndexFlatIP(array.shape[1])
            updated.add(array)
            self._save(updated, self.chunks + rows)

    def remove_document(self, document_id):
        with self.lock:
            self._reload()
            if self.index is None:
                return
            keep = [i for i, row in enumerate(self.chunks) if row.metadata.document_id != document_id]
            if len(keep) == len(self.chunks):
                return
            updated = faiss.IndexFlatIP(self.index.d)
            if keep:
                updated.add(np.array([self.index.reconstruct(i) for i in keep], dtype="float32"))
            self._save(updated, [self.chunks[i] for i in keep])

    def document_counts(self):
        with self.lock:
            self._reload()
            counts = {}
            for chunk in self.chunks:
                key = chunk.metadata.document_id
                counts[key] = counts.get(key, 0) + 1
            return counts

    def search(self, vector, top_k: int, threshold: float, allowed_ids: set[str],
               document_ids: set[str] | None = None) -> list[RetrievedChunk]:
        """Filter before top-k so excluded documents cannot crowd out valid matches."""
        with self.lock:
            self._reload()
            if self.index is None or not self.index.ntotal or not allowed_ids:
                return []
            query = normalized([vector])
            if query.shape[1] != self.index.d:
                raise StorageError("Query embedding dimensions differ from the index.")
            # Exact flat search: sorting all IDs allows correct arbitrary metadata filtering.
            scores, ids = self.index.search(query, self.index.ntotal)
            results = []
            for score, idx in zip(scores[0], ids[0]):
                row = self.chunks[int(idx)]
                meta = row.metadata
                if meta.document_id not in allowed_ids:
                    continue
                if document_ids is not None and meta.document_id not in document_ids:
                    continue
                if float(score) < threshold:
                    continue
                results.append(RetrievedChunk(text=row.text, document_id=meta.document_id,
                    document_name=meta.document_name, page_number=meta.page_number,
                    chunk_id=meta.chunk_id, score=max(-1.0, min(1.0, float(score)))))
                if len(results) >= top_k:
                    break
            return results
