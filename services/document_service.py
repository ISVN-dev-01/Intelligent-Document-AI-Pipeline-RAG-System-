from pathlib import Path
from time import perf_counter
from uuid import uuid4

from ingestion.chunker import create_chunks
from ingestion.pdf_loader import load_pdf
from utils.errors import AppError, DuplicateDocument, StorageError
from utils.hashing import sha256_bytes
from utils.logging_config import event
from utils.validators import validate_pdf


class DocumentService:
    def __init__(self, settings, repository, embeddings, store, lock):
        self.settings, self.repository, self.embeddings = settings, repository, embeddings
        self.store, self.lock = store, lock
        settings.upload_dir.mkdir(parents=True, exist_ok=True)

    def ingest(self, principal, filename: str, data: bytes):
        principal.require_admin()
        filename = validate_pdf(filename, data, self.settings.max_upload_mb)
        digest = sha256_bytes(data)
        event("document_upload", bytes=len(data))
        with self.lock:
            existing = self.repository.by_hash(digest)
            if existing and existing.processing_status in {"ready", "processing"}:
                raise DuplicateDocument("This PDF has already been uploaded, even if its filename has changed.")
            document_id = existing.id if existing else str(uuid4())
            path: Path = self.settings.upload_dir / f"{document_id}.pdf"
            if existing:
                self.store.remove_document(document_id)
                self.repository.update_document(document_id, processing_status="processing",
                    filename=filename, page_count=0, chunk_count=0)
            else:
                self.repository.create_document(id=document_id, filename=filename, file_hash=digest,
                                                file_size=len(data), processing_status="processing")
            try:
                event("document_processing_start", document_id=document_id)
                path.write_bytes(data)
                pages, page_count = load_pdf(path, self.settings.max_pdf_pages,
                                             self.settings.max_extracted_chars)
                chunks = create_chunks(pages, document_id, filename, self.settings.chunk_size,
                                       self.settings.chunk_overlap)
                started = perf_counter()
                vectors = self.embeddings.embed_documents([chunk.page_content for chunk in chunks])
                embedding_ms = (perf_counter() - started) * 1000
                started = perf_counter()
                self.store.add(chunks, vectors)
                indexing_ms = (perf_counter() - started) * 1000
                self.repository.update_document(document_id, processing_status="ready", page_count=page_count,
                    chunk_count=len(chunks), embedding_ms=embedding_ms, indexing_ms=indexing_ms)
                event("document_processing_success", document_id=document_id, pages=page_count, chunks=len(chunks))
                return self.repository.get_document(document_id)
            except Exception as exc:
                # A failed SQL commit after index publish must never expose uncommitted chunks.
                try:
                    self.repository.update_document(document_id, processing_status="failed", chunk_count=0)
                    self.store.remove_document(document_id)
                    path.unlink(missing_ok=True)
                except Exception as cleanup:
                    event("document_cleanup_failure", document_id=document_id, error_type=type(cleanup).__name__)
                event("document_processing_failure", document_id=document_id, error_type=type(exc).__name__)
                if isinstance(exc, AppError):
                    raise
                raise StorageError("Document processing failed. Check storage and database availability, then retry.") from None

    def delete(self, principal, document_id):
        principal.require_admin()
        with self.lock:
            record = self.repository.get_document(document_id)
            if record is None:
                raise AppError("Document not found.")
            # Preserve a tombstone for historical foreign keys, but exclude immediately from retrieval.
            self.repository.update_document(document_id, processing_status="deleted", chunk_count=0)
            self.store.remove_document(document_id)
            (self.settings.upload_dir / f"{record.id}.pdf").unlink(missing_ok=True)
            event("document_deleted", document_id=document_id)

    def recover(self):
        """Called at startup under the shared lock; interrupted uploads become retryable."""
        with self.lock:
            documents = self.repository.documents()
            counts = self.store.document_counts()
            for row in documents:
                if row.processing_status == "ready" and counts.get(row.id, 0) != row.chunk_count:
                    raise StorageError("Ready documents do not match the vector index. Restore the database and index from the same backup.")
                if row.processing_status != "ready":
                    self.store.remove_document(row.id)
                    (self.settings.upload_dir / f"{row.id}.pdf").unlink(missing_ok=True)
                    if row.processing_status == "processing":
                        self.repository.update_document(row.id, processing_status="failed", chunk_count=0)
            known_ids = {row.id for row in documents}
            for unknown in set(counts) - known_ids:
                self.store.remove_document(unknown)
