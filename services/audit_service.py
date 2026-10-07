from utils.logging_config import event


class AuditService:
    def __init__(self, repository, store_text):
        self.repository, self.store_text = repository, store_text

    def record(self, principal, question, result):
        self.repository.record_query({"id": result.query_id, "actor_role": principal.role,
            "query_text": question if self.store_text else "[redacted]",
            "response_text": result.answer if self.store_text else "[redacted]",
            "retrieval_count": len(result.evidence), "retrieval_ms": result.retrieval_ms,
            "embedding_ms": result.embedding_ms, "llm_ms": result.llm_ms,
            "duration_ms": result.duration_ms, "outcome": result.outcome}, result.evidence)
        event("query_completed", query_id=result.query_id, outcome=result.outcome,
              retrieved=len(result.evidence), duration_ms=round(result.duration_ms, 2))
