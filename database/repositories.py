"""Transaction-scoped access; ORM records are detached after every call."""
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.models import DocumentRecord, QueryRecord, QuerySource
from utils.errors import DuplicateDocument, StorageError


class Repository:
    def __init__(self, sessions):
        self.sessions = sessions

    def documents(self):
        with self.sessions() as session:
            return list(session.scalars(select(DocumentRecord).order_by(DocumentRecord.uploaded_at.desc())))

    def get_document(self, document_id):
        with self.sessions() as session:
            return session.get(DocumentRecord, document_id)

    def by_hash(self, digest):
        with self.sessions() as session:
            return session.scalar(select(DocumentRecord).where(DocumentRecord.file_hash == digest))

    def create_document(self, **values):
        try:
            with self.sessions.begin() as session:
                row = DocumentRecord(**values)
                session.add(row)
            return row
        except IntegrityError:
            raise DuplicateDocument("This PDF is already registered. Check the document library.") from None

    def update_document(self, document_id, **values):
        with self.sessions.begin() as session:
            row = session.get(DocumentRecord, document_id)
            if row is None:
                raise StorageError("The document record was not found.")
            for key, value in values.items():
                setattr(row, key, value)

    def ready_ids(self) -> set[str]:
        with self.sessions() as session:
            return set(session.scalars(select(DocumentRecord.id).where(DocumentRecord.processing_status == "ready")))

    def record_query(self, values, sources):
        try:
            with self.sessions.begin() as session:
                session.add(QueryRecord(**values))
                session.flush()
                session.add_all([QuerySource(query_id=values["id"], document_id=s.document_id,
                                            page_number=s.page_number, chunk_id=s.chunk_id,
                                            similarity_score=s.score) for s in sources])
        except SQLAlchemyError:
            raise StorageError("The answer could not be recorded in the audit database. Please retry.") from None

    def history(self, limit=50):
        with self.sessions() as session:
            return list(session.scalars(select(QueryRecord).order_by(QueryRecord.created_at.desc()).limit(limit)))

    def query_sources(self, query_id):
        with self.sessions() as session:
            return list(session.execute(select(QuerySource, DocumentRecord.filename).join(DocumentRecord)
                                        .where(QuerySource.query_id == query_id)))

    def statistics(self):
        with self.sessions() as session:
            count, chunks = session.execute(select(func.count(DocumentRecord.id), func.sum(DocumentRecord.chunk_count))
                .where(DocumentRecord.processing_status == "ready")).one()
            queries, latency, last = session.execute(select(func.count(QueryRecord.id),
                func.avg(QueryRecord.retrieval_ms), func.max(QueryRecord.created_at))).one()
            return {"documents": count, "chunks": chunks or 0, "queries": queries,
                    "avg_retrieval_ms": latency or 0.0, "last_query": last}
