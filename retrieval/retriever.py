from dataclasses import dataclass
from time import perf_counter

from vector_store.faiss_store import RetrievedChunk


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    embedding_ms: float
    retrieval_ms: float


class Retriever:
    def __init__(self, embeddings, store, repository, settings):
        self.embeddings, self.store, self.repository, self.settings = embeddings, store, repository, settings

    def retrieve(self, question: str, document_ids=None, top_k=None, threshold=None):
        allowed = self.repository.ready_ids()
        if not allowed or document_ids == set():
            return RetrievalResult([], 0, 0)
        started = perf_counter()
        vector = self.embeddings.embed_query(question)
        embedding_ms = (perf_counter() - started) * 1000
        started = perf_counter()
        chunks = self.store.search(vector, top_k if top_k is not None else self.settings.top_k,
            threshold if threshold is not None else self.settings.similarity_threshold, allowed, document_ids)
        return RetrievalResult(chunks, embedding_ms, (perf_counter() - started) * 1000)
