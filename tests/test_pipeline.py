from concurrent.futures import ThreadPoolExecutor

import pytest

from llm.guardrails import LOW_RELEVANCE, NO_ANSWER, GroundedAnswer
from services.bootstrap import build_application
from utils.errors import DuplicateDocument, ProviderError, StorageError


def test_ingest_query_restart_delete(app, admin, user, sample, settings):
    document = app.documents.ingest(admin, *sample)
    assert document.page_count == 2 and document.chunk_count >= 2
    with pytest.raises(DuplicateDocument):
        app.documents.ingest(admin, "renamed.pdf", sample[1])
    answer = app.queries.ask(user, "What is the annual leave entitlement?")
    assert "24" in answer.answer and answer.sources[0].page_number == 1
    restarted = build_application(settings)
    try:
        assert "24" in restarted.queries.ask(user, "What is the annual leave entitlement?").answer
        restarted.documents.delete(admin, document.id)
        assert not restarted.queries.ask(user, "What is the annual leave entitlement?").evidence
        assert not (settings.upload_dir / f"{document.id}.pdf").exists()
        assert restarted.repository.query_sources(answer.query_id)  # retained FK tombstone
    finally:
        restarted.engine.dispose()


def test_no_answer_does_not_call_llm(app, user, monkeypatch):
    def forbidden(*args):
        pytest.fail("LLM must not run without evidence")
    monkeypatch.setattr(app.queries.llm, "answer", forbidden)
    assert app.queries.ask(user, "What is the annual leave entitlement?").answer == LOW_RELEVANCE


def test_model_no_answer_and_threshold(app, admin, sample, monkeypatch):
    app.documents.ingest(admin, *sample)
    monkeypatch.setattr(app.queries.llm, "answer", lambda *args: GroundedAnswer(answerable=False))
    assert app.queries.ask(admin, "What is the annual leave entitlement?").answer == NO_ANSWER
    app.settings.similarity_threshold = 1.0
    assert app.queries.ask(admin, "What are the moons of Neptune?").answer == LOW_RELEVANCE


def test_demo_abstains_on_unsupported_specifics(app, admin, sample):
    app.documents.ingest(admin, *sample)
    for question in ["What is the company's revenue in 2041?", "What is the CEO's favorite pizza topping?"]:
        assert app.queries.ask(admin, question).outcome != "answered"


def test_failed_embedding_retry(app, admin, sample, monkeypatch):
    embed = app.documents.embeddings.embed_documents
    def fail(*args):
        raise ProviderError("Embedding service unavailable.")
    monkeypatch.setattr(app.documents.embeddings, "embed_documents", fail)
    with pytest.raises(ProviderError):
        app.documents.ingest(admin, *sample)
    assert app.repository.documents()[0].processing_status == "failed"
    assert not app.documents.store.document_counts()
    monkeypatch.setattr(app.documents.embeddings, "embed_documents", embed)
    assert app.documents.ingest(admin, *sample).processing_status == "ready"


def test_audit_failure_withholds_answer(app, admin, monkeypatch):
    def fail(*args):
        raise StorageError("Audit unavailable")
    monkeypatch.setattr(app.repository, "record_query", fail)
    with pytest.raises(StorageError):
        app.queries.ask(admin, "What is the annual leave entitlement?")


def test_interrupted_upload_recovered(app, admin, sample, settings):
    row = app.documents.ingest(admin, *sample)
    app.repository.update_document(row.id, processing_status="processing")
    restarted = build_application(settings)
    try:
        assert restarted.repository.get_document(row.id).processing_status == "failed"
        assert restarted.documents.store.document_counts() == {}
    finally:
        restarted.engine.dispose()


def test_missing_index_fails_closed(app, admin, sample, settings):
    app.documents.ingest(admin, *sample)
    (settings.faiss_index_path / "manifest.json").unlink()
    with pytest.raises(StorageError, match="do not match"):
        build_application(settings)


def test_concurrent_duplicate_serialized(app, admin, sample):
    def upload():
        try:
            return app.documents.ingest(admin, *sample).processing_status
        except DuplicateDocument:
            return "duplicate"
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: upload(), range(2)))
    assert sorted(outcomes) == ["duplicate", "ready"]
