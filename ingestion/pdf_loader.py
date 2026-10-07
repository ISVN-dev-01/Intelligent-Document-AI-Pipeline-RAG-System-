from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from pypdf import PdfReader

from ingestion.text_cleaner import clean_text
from utils.errors import ValidationError


def load_pdf(path: Path, max_pages: int, max_chars: int):
    """Extract each PDF page; scans and encrypted PDFs require preprocessing outside this app."""
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValidationError("Password-protected PDFs are not supported. Upload an unencrypted copy.")
        page_count = len(reader.pages)
        if page_count == 0 or page_count > max_pages:
            raise ValidationError(f"Upload a PDF containing between 1 and {max_pages} pages.")
        pages, total = [], 0
        for page in PyPDFLoader(str(path), mode="page").lazy_load():
            page.page_content = clean_text(page.page_content)
            total += len(page.page_content)
            if total > max_chars:
                raise ValidationError("The extracted PDF text exceeds the configured processing limit.")
            if page.page_content:
                pages.append(page)
        if not pages:
            raise ValidationError("No readable text found. Scanned PDFs need OCR before upload.")
        return pages, page_count
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("The PDF could not be read. It may be corrupted or unsupported.") from None
