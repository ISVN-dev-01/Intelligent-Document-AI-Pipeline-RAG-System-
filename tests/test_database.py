import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.models import QuerySource
from utils.errors import AppError


def test_role_permissions_and_auth(app, user, sample):
    with pytest.raises(AppError, match="administrator"):
        app.documents.ingest(user, *sample)
    with pytest.raises(AppError, match="incorrect"):
        app.auth.login("admin", "wrong")
    assert app.auth.login("admin", "test-only-password-123").role == "admin"


def test_audit_transaction_and_history(app, admin, sample):
    app.documents.ingest(admin, *sample)
    result = app.queries.ask(admin, "What is the annual leave entitlement?")
    row = app.repository.history()[0]
    assert row.query_text and row.response_text == result.answer
    assert row.retrieval_count == len(result.evidence)
    assert row.duration_ms > 0
    assert app.repository.query_sources(row.id)
    with app.repository.sessions.begin() as session:
        count_before = len(list(session.scalars(select(QuerySource))))
    with pytest.raises(IntegrityError), app.repository.sessions.begin() as session:
        session.add(QuerySource(query_id="missing", document_id="missing", page_number=1, chunk_id="bad", similarity_score=1))
    with app.repository.sessions() as session:
        assert len(list(session.scalars(select(QuerySource)))) == count_before


def test_redaction(app, admin):
    app.queries.audit.store_text = False
    app.queries.ask(admin, "A question without documents?")
    row = app.repository.history()[0]
    assert row.query_text == row.response_text == "[redacted]"
