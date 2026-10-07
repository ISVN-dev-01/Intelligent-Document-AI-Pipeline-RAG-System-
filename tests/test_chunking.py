from langchain_core.documents import Document

from ingestion.chunker import create_chunks
from ingestion.text_cleaner import clean_text
from utils.hashing import sha256_bytes


def test_chunk_size_and_metadata():
    pages = [Document(page_content="Annual leave entitlement is 24 days. " * 60, metadata={"page": 2})]
    chunks = create_chunks(pages, "doc-id", "policy.pdf", 200, 30)
    assert len(chunks) > 1
    assert all(len(c.page_content) <= 200 for c in chunks)
    assert all(c.metadata["page_number"] == 3 and c.metadata["document_id"] == "doc-id" for c in chunks)
    assert len({c.metadata["chunk_id"] for c in chunks}) == len(chunks)
    assert all(c.metadata["created_at"] and c.metadata["source"] == "policy.pdf" for c in chunks)


def test_cleaning_retains_paragraphs_and_numbers():
    assert clean_text("  24  days\r\n\r\n\r\n Next\x00  ") == "24 days\n\n Next"


def test_hash_deterministic():
    assert sha256_bytes(b"a") == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
    assert sha256_bytes(b"a") != sha256_bytes(b"b")
