from typing import Protocol

from langchain_google_genai import ChatGoogleGenerativeAI

from embeddings.embedding_service import terms
from llm.guardrails import EvidenceClaim, GroundedAnswer
from llm.prompt import build_messages
from utils.errors import ProviderError
from utils.logging_config import event


class LLMService(Protocol):
    def answer(self, question, chunks, previous_questions) -> GroundedAnswer: ...


class GeminiService:
    def __init__(self, settings):
        client = ChatGoogleGenerativeAI(model=settings.llm_model,
            google_api_key=settings.google_api_key, temperature=settings.llm_temperature,
            timeout=settings.api_timeout_seconds, max_retries=2, max_tokens=3000, vertexai=False)
        self.client = client.with_structured_output(GroundedAnswer, method="json_schema")

    def answer(self, question, chunks, previous_questions):
        event("llm_request", context_chunks=len(chunks))
        try:
            answer = self.client.invoke(build_messages(question, chunks, previous_questions))
            return GroundedAnswer.model_validate(answer)
        except Exception as exc:
            event("llm_failure", error_type=type(exc).__name__)
            raise ProviderError("Gemini could not produce an answer. Check model access, API quota and connectivity.") from None


class ExtractiveDemoService:
    """Offline passage quoting for demonstrations; never presented as Gemini generation."""
    def answer(self, question, chunks, previous_questions):
        keywords = terms(question)
        claims = []
        for chunk in chunks:
            overlap = len(keywords & terms(chunk.text)) / max(1, len(keywords))
            if overlap >= 0.6:
                claims.append(EvidenceClaim(statement=chunk.text, source_label=chunk.label,
                                            supporting_quote=chunk.text))
        return GroundedAnswer(answerable=bool(claims), claims=claims[:3])
