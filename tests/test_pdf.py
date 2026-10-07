import io

import pytest
from pypdf import PdfReader, PdfWriter

from ingestion.pdf_loader import load_pdf
from utils.errors import ValidationError
from utils.validators import validate_pdf


def test_pdf_pages(sample, tmp_path):
    path = tmp_path / sample[0]
    path.write_bytes(sample[1])
    pages, count = load_pdf(path, 20, 100000)
    assert count == 2
    assert "24 days" in pages[0].page_content
    assert pages[1].metadata["page"] == 1


@pytest.mark.parametrize("name,data", [("../x.pdf", b"%PDF-abc"), ("x.txt", b"%PDF-abc"),
    ("CON.pdf", b"%PDF-abc"), ("a.pdf", b""), ("a.pdf", b"not a PDF"), ("C:\\x.pdf", b"%PDF-abc")])
def test_invalid_upload(name, data):
    with pytest.raises(ValidationError):
        validate_pdf(name, data, 1)


def test_size_limit():
    with pytest.raises(ValidationError):
        validate_pdf("big.pdf", b"%PDF-" + b"x" * 1024 * 1024, 1)


def test_empty_encrypted_and_corrupt(tmp_path, sample):
    path = tmp_path / "empty.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=600, height=800)
    writer.write(path)
    with pytest.raises(ValidationError, match="No readable text"):
        load_pdf(path, 20, 100000)
    writer = PdfWriter()
    writer.append(PdfReader(io.BytesIO(sample[1])))
    writer.encrypt("test-password")
    writer.write(path)
    with pytest.raises(ValidationError, match="Password-protected"):
        load_pdf(path, 20, 100000)
    path.write_bytes(b"%PDF-garbage")
    with pytest.raises(ValidationError, match="could not be read"):
        load_pdf(path, 20, 100000)


def test_extraction_limits(sample, tmp_path):
    path = tmp_path / sample[0]
    path.write_bytes(sample[1])
    with pytest.raises(ValidationError):
        load_pdf(path, 1, 100000)
    with pytest.raises(ValidationError):
        load_pdf(path, 20, 10)
