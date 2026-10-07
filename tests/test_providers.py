from types import SimpleNamespace

import pytest

from embeddings.google_embeddings import GoogleEmbeddingService
from llm.gemini_service import GeminiService
from llm.guardrails import GroundedAnswer
from utils.errors import ProviderError


def test_google_batch_and_task_types(settings, monkeypatch):
    calls = []
    def documents(texts, **kwargs):
        calls.append((len(texts), kwargs))
        return [[1.0, 0.0] for _ in texts]
    fake = SimpleNamespace(embed_documents=documents, embed_query=lambda text, **kw: [0, 1])
    def factory(**kwargs):
        assert kwargs["client_args"]["timeout"] == settings.api_timeout_seconds
        return fake
    monkeypatch.setattr("embeddings.google_embeddings.GoogleGenerativeAIEmbeddings", factory)
    service = GoogleEmbeddingService(settings)
    assert len(service.embed_documents(["text"] * 65)) == 65
    assert [n for n, _ in calls] == [32, 32, 1]
    assert all(opts["task_type"] == "RETRIEVAL_DOCUMENT" for _, opts in calls)
    assert service.embed_query("question") == [0, 1]


def test_embedding_error_is_sanitized(settings, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("Secret value must not appear")
    monkeypatch.setattr("embeddings.google_embeddings.GoogleGenerativeAIEmbeddings", lambda **kw: SimpleNamespace(embed_query=fail))
    with pytest.raises(ProviderError) as caught:
        GoogleEmbeddingService(settings).embed_query("question")
    assert "Secret" not in str(caught.value)


def test_gemini_structured_invocation(settings, monkeypatch):
    def invoke(messages):
        assert messages[0].type == "system"
        return GroundedAnswer(answerable=False)
    def structured(schema, method):
        assert schema is GroundedAnswer and method == "json_schema"
        return SimpleNamespace(invoke=invoke)
    monkeypatch.setattr("llm.gemini_service.ChatGoogleGenerativeAI",
                        lambda **kw: SimpleNamespace(with_structured_output=structured))
    assert GeminiService(settings).answer("Question?", [], []).answerable is False
