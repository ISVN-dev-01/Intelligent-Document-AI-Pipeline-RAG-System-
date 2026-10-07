from datetime import datetime, timezone
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_chunks(pages, document_id: str, filename: str, size: int, overlap: int):
    """Split pages separately so citations never cross a page boundary."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap,
                                              separators=["\n\n", "\n", ". ", " ", ""])
    chunks = splitter.split_documents(pages)
    created_at = datetime.now(timezone.utc).isoformat()
    for chunk in chunks:
        chunk.metadata = {"document_id": document_id, "document_name": filename,
                          "page_number": int(chunk.metadata.get("page", 0)) + 1,
                          "chunk_id": str(uuid4()), "source": filename, "created_at": created_at}
    return chunks
