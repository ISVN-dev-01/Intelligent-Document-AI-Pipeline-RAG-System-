"""Relational metadata only; vectors and chunk text live in the local vector store."""
from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("file_hash", name="uq_document_hash"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(180))
    file_hash: Mapped[str] = mapped_column(String(64))
    file_size: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(default=utcnow)
    processing_status: Mapped[str] = mapped_column(String(20), default="processing")
    embedding_ms: Mapped[float] = mapped_column(Float, default=0)
    indexing_ms: Mapped[float] = mapped_column(Float, default=0)


class QueryRecord(Base):
    __tablename__ = "queries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_role: Mapped[str] = mapped_column(String(10))
    query_text: Mapped[str] = mapped_column(Text)
    response_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    retrieval_count: Mapped[int] = mapped_column(Integer)
    retrieval_ms: Mapped[float] = mapped_column(Float)
    embedding_ms: Mapped[float] = mapped_column(Float)
    llm_ms: Mapped[float] = mapped_column(Float)
    duration_ms: Mapped[float] = mapped_column(Float)
    outcome: Mapped[str] = mapped_column(String(30))


class QuerySource(Base):
    __tablename__ = "query_sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[str] = mapped_column(ForeignKey("queries.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    chunk_id: Mapped[str] = mapped_column(String(36))
    similarity_score: Mapped[float] = mapped_column(Float)
