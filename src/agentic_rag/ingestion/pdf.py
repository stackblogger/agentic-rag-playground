from pypdf import PdfReader


def extract_pages(file_path: str) -> list[str]:
    reader = PdfReader(file_path)
    return [page.extract_text() or "" for page in reader.pages]
