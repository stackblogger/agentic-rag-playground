import litellm
import pytest


@pytest.fixture(autouse=True)
def block_real_llm_calls(monkeypatch):
    # tests must never call a real LLM provider
    def blocked(*args, **kwargs):
        raise AssertionError("A test tried to call the real LLM provider")

    monkeypatch.setattr(litellm, "embedding", blocked)
    monkeypatch.setattr(litellm, "completion", blocked)


@pytest.fixture
def make_pdf(tmp_path):
    """Makes a small PDF file with one line of text on each page."""

    def build(pages: list[str], name: str = "test.pdf") -> str:
        count = len(pages)
        kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(count))
        bodies = [
            b"<</Type/Catalog/Pages 2 0 R>>",
            f"<</Type/Pages/Kids[{kids}]/Count {count}>>".encode(),
            b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
        ]
        for i, text in enumerate(pages):
            page = (
                f"<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]/Contents {5 + 2 * i} 0 R"
                "/Resources<</Font<</F1 3 0 R>>>>>>"
            )
            bodies.append(page.encode())
            stream = f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode()
            bodies.append(f"<</Length {len(stream)}>>\nstream\n".encode() + stream + b"\nendstream")

        data = b"%PDF-1.4\n"
        offsets = []
        for number, body in enumerate(bodies, start=1):
            offsets.append(len(data))
            data += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"

        xref_start = len(data)
        data += f"xref\n0 {len(bodies) + 1}\n0000000000 65535 f \n".encode()
        for offset in offsets:
            data += f"{offset:010d} 00000 n \n".encode()
        data += f"trailer<</Size {len(bodies) + 1}/Root 1 0 R>>\nstartxref\n{xref_start}\n%%EOF".encode()

        path = tmp_path / name
        path.write_bytes(data)
        return str(path)

    return build
