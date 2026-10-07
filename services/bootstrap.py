from dataclasses import dataclass

from filelock import FileLock

from config.settings import Settings
from database.connection import create_database
from database.repositories import Repository
from embeddings.embedding_service import HashEmbeddingService
from embeddings.google_embeddings import GoogleEmbeddingService
from llm.gemini_service import ExtractiveDemoService, GeminiService
from retrieval.retriever import Retriever
from security.auth import AuthService
from services.audit_service import AuditService
from services.document_service import DocumentService
from services.query_service import QueryService
from services.statistics_service import StatisticsService
from utils.errors import AppError
from utils.logging_config import configure_logging
from vector_store.faiss_store import FaissStore


@dataclass
class Application:
    settings: Settings
    engine: object
    repository: Repository
    auth: AuthService
    documents: DocumentService
    queries: QueryService
    statistics: StatisticsService


def build_application(settings=None):
    settings = settings or Settings()
    errors = settings.startup_errors()
    if errors:
        raise AppError("\n".join(errors))
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(settings.data_dir)
    engine, sessions = create_database(settings)
    try:
        repository = Repository(sessions)
        embeddings = GoogleEmbeddingService(settings) if settings.embedding_provider == "google" else HashEmbeddingService()
        llm = GeminiService(settings) if settings.app_mode == "google" else ExtractiveDemoService()
        store = FaissStore(settings.faiss_index_path, embeddings.fingerprint)
        lock = FileLock(str(settings.data_dir / "pipeline.lock"), timeout=120)
        documents = DocumentService(settings, repository, embeddings, store, lock)
        documents.recover()
        retriever = Retriever(embeddings, store, repository, settings)
        audit = AuditService(repository, settings.audit_store_text)
        return Application(settings, engine, repository, AuthService(settings), documents,
            QueryService(settings, retriever, llm, audit, lock), StatisticsService(repository, store))
    except Exception:
        engine.dispose()
        raise
