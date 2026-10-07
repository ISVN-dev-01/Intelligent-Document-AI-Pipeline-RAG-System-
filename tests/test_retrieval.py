import json

import pytest
from langchain_core.documents import Document

from ingestion.chunker import create_chunks
from utils.errors import StorageError
from vector_store.faiss_store import FaissStore


def chunks(text, doc):
    return create_chunks([Document(page_content=text, metadata={"page": 0})], doc, f"{doc}.pdf", 1000, 150)


def test_cosine_persistence_filter_and_threshold(tmp_path):
    store = FaissStore(tmp_path, "fixture")
    assert store.search([1, 0], 5, 0, {"a"}) == []
    store.add(chunks("First document passage.", "a") + chunks("Second document passage.", "b"), [[10, 0], [0, 3]])
    reloaded = FaissStore(tmp_path, "fixture")
    hits = reloaded.search([2, 0], 5, 0.35, {"a", "b"})
    assert len(hits) == 1 and hits[0].document_id == "a"
    assert hits[0].score == pytest.approx(1)
    assert reloaded.search([1, 0], 5, 0.35, {"a", "b"}, {"b"}) == []
    assert reloaded.search([1, 0], 1, -1, {"b"})[0].document_id == "b"
    store.remove_document("a")
    assert reloaded.document_counts() == {"b": 1}  # observes other instance's publication


def test_corruption_and_model_mismatch(tmp_path):
    store = FaissStore(tmp_path, "fixture")
    store.add(chunks("A source passage.", "a"), [[1, 0]])
    with pytest.raises(StorageError, match="Embedding model differs"):
        FaissStore(tmp_path, "different-model")
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    (tmp_path / f"{manifest['generation']}.json").write_text("[]")
    with pytest.raises(StorageError, match="unreadable"):
        FaissStore(tmp_path, "fixture")


@pytest.mark.parametrize("vectors", [[[0, 0]], [[float("nan"), 1]], [[float("inf"), 0]], []])
def test_invalid_vectors(tmp_path, vectors):
    with pytest.raises(StorageError):
        FaissStore(tmp_path, "fixture").add(chunks("A source passage.", "a"), vectors)


def test_failed_publication_preserves_previous_snapshot(tmp_path, monkeypatch):
    import vector_store.faiss_store as module
    store = FaissStore(tmp_path, "fixture")
    store.add(chunks("A source passage.", "a"), [[1, 0]])
    def fail(*args):
        raise OSError("simulated disk failure")
    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(StorageError):
        store.add(chunks("Another passage.", "b"), [[0, 1]])
    assert FaissStore(tmp_path, "fixture").document_counts() == {"a": 1}
