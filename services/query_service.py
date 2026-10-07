from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from llm.guardrails import LOW_RELEVANCE, NO_ANSWER, safe_context, validate_answer
from utils.logging_config import event
from utils.validators import validate_question
from vector_store.faiss_store import RetrievedChunk


@dataclass
class QueryResult:
    query_id: str
    answer: str
    sources: list[RetrievedChunk]
    evidence: list[RetrievedChunk]
    outcome: str
    embedding_ms: float
    retrieval_ms: float
    llm_ms: float
    duration_ms: float


class QueryService:
    def __init__(self, settings, retriever, llm, audit, lock):
        self.settings, self.retriever, self.llm, self.audit, self.lock = settings, retriever, llm, audit, lock

    def ask(self, principal, question: str, previous_questions=None, document_ids=None):
        started = perf_counter()
        question = validate_question(question, self.settings.max_question_chars)
        prior = list(previous_questions or [])[-self.settings.memory_turns:] if self.settings.memory_turns else []
        prior = [validate_question(q, self.settings.max_question_chars) for q in prior]
        # Bound memory; only short ambiguous follow-ups expand retrieval with the last question.
        followup = len(question.split()) < 10 and any(
            word in question.lower().split() for word in ("it", "they", "that", "those", "them", "many"))
        search_question = f"{prior[-1]}\n{question}" if prior and followup else question
        event("query_received")
        # Serializes queries/deletes/ingestion to keep SQL, evidence and citations consistent.
        with self.lock:
            retrieved = self.retriever.retrieve(search_question, document_ids=document_ids)
            evidence = safe_context(retrieved.chunks, self.settings.max_context_chars)
            event("retrieval_completed", chunks=len(evidence), retrieval_ms=round(retrieved.retrieval_ms, 2))
            llm_ms, sources = 0.0, []
            if not evidence:
                answer, outcome = LOW_RELEVANCE, "low_relevance"
            else:
                llm_start = perf_counter()
                generated = self.llm.answer(question, evidence, prior)
                llm_ms = (perf_counter() - llm_start) * 1000
                answer, sources = validate_answer(generated, evidence)
                outcome = "no_answer" if answer == NO_ANSWER else "answered"
            result = QueryResult(str(uuid4()), answer, sources, evidence, outcome,
                retrieved.embedding_ms, retrieved.retrieval_ms, llm_ms, (perf_counter() - started) * 1000)
            # Fail closed if mandatory audit persistence fails; no unrecorded answer reaches the UI.
            self.audit.record(principal, question, result)
            result.duration_ms = (perf_counter() - started) * 1000
            return result
