"""Measured retrieval metrics and explicitly labeled answer proxies; no LLM judge."""
from datetime import datetime, timezone
from statistics import mean


def evaluate(app, principal, dataset):
    results = []
    for case in dataset:
        response = app.queries.ask(principal, case["question"])
        matches = [c for c in response.evidence if c.document_name == case["expected_source"]
                   and c.page_number == case["expected_page"]]
        answerable = case["answerable"]
        results.append({"question": case["question"], "answerable": answerable,
            "retrieval_hit": bool(matches) if answerable else None,
            "source_precision_proxy": len(matches) / len(response.evidence) if response.evidence and answerable else (0 if answerable else None),
            "answer_keyword_proxy": all(term.lower() in response.answer.lower() for term in case["expected_terms"]) if answerable else None,
            "unsupported_answer_on_unanswerable": response.outcome == "answered" if not answerable else None,
            "answer": response.answer, "outcome": response.outcome,
            "retrieval_ms": response.retrieval_ms, "duration_ms": response.duration_ms,
            "sources": [{"name": c.document_name, "page": c.page_number, "score": c.score} for c in response.evidence]})
    def average(key):
        values = [row[key] for row in results if row[key] is not None]
        return mean(values) if values else None
    return {"run_at_utc": datetime.now(timezone.utc).isoformat(), "mode": app.settings.app_mode,
            "embedding_model": app.queries.retriever.embeddings.fingerprint,
            "llm_model": app.settings.llm_model if app.settings.app_mode == "google" else "extractive-demo",
            "top_k": app.settings.top_k, "threshold": app.settings.similarity_threshold,
            "retrieval_hit_rate": average("retrieval_hit"),
            "source_precision_proxy": average("source_precision_proxy"),
            "answer_keyword_proxy": average("answer_keyword_proxy"),
            "unsupported_answer_rate_on_unanswerable": average("unsupported_answer_on_unanswerable"),
            "mean_retrieval_ms": average("retrieval_ms"), "cases": results}
