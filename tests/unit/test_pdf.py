import pytest

from agentic_rag.ingestion.pdf import extract_pages


def test_text_is_read_page_by_page(make_pdf):
    assert extract_pages(make_pdf(["First page", "Second page"])) == ["First page", "Second page"]


def test_file_that_is_not_a_pdf_raises_error(tmp_path):
    bad_file = tmp_path / "bad.pdf"
    bad_file.write_bytes(b"not a pdf")
    with pytest.raises(Exception):
        extract_pages(str(bad_file))
