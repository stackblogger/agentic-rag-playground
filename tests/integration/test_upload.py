import hashlib

import pytest

from agentic_rag.core.config import settings
from agentic_rag.db.models import Document


@pytest.fixture(autouse=True)
def uploads_in_tmp_path(monkeypatch, tmp_path):
    """Test uploads are kept in a temp folder, not in the real upload folder."""
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))


def post_pdf(client, path, name="cats.pdf"):
    with open(path, "rb") as pdf:
        return client.post("/documents", files={"file": (name, pdf, "application/pdf")})


def test_same_file_twice_is_rejected(client, make_pdf):
    pdf = make_pdf(["Cats sleep a lot"])

    first = post_pdf(client, pdf)
    second = post_pdf(client, pdf)

    assert first.status_code == 201
    assert second.status_code == 409
    assert str(first.json()["id"]) in second.json()["detail"]
    assert len(client.get("/documents").json()) == 1


def test_same_file_with_another_name_is_also_rejected(client, make_pdf):
    pdf = make_pdf(["Cats sleep a lot"])

    post_pdf(client, pdf, name="cats.pdf")
    second = post_pdf(client, pdf, name="cats-copy.pdf")

    assert second.status_code == 409


def test_different_file_is_accepted(client, make_pdf):
    post_pdf(client, make_pdf(["Cats sleep a lot"]))
    second = post_pdf(client, make_pdf(["Dogs run a lot"], name="dogs.pdf"), name="dogs.pdf")

    assert second.status_code == 201
    assert len(client.get("/documents").json()) == 2


def test_failed_document_does_not_block_the_same_file(client, db, make_pdf):
    pdf = make_pdf(["Cats sleep a lot"])
    file_hash = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
    db.add(Document(filename="cats.pdf", file_path="x", file_hash=file_hash, status="failed"))
    db.commit()

    assert post_pdf(client, pdf).status_code == 201
