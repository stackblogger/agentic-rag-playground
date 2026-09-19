from pathlib import Path
from types import SimpleNamespace

import litellm
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from agentic_rag.api.main import app
from agentic_rag.core.config import settings
from agentic_rag.db.connection import get_db
from agentic_rag.db.models import EMBEDDING_DIMENSIONS, Chunk, Document

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def test_engine():
    """A separate database (name + _test) is made for the tests, so real data is never touched."""
    real_url = make_url(settings.database_url)
    test_url = real_url.set(database=f"{real_url.database}_test")
    assert test_url.database.endswith("_test")

    admin = create_engine(real_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{test_url.database}" WITH (FORCE)'))
            connection.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    except OperationalError:
        pytest.skip("Postgres is not running. Start it with: docker compose up -d db")

    # run the real migrations on the test database
    real_database_url = settings.database_url
    settings.database_url = test_url.render_as_string(hide_password=False)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    try:
        command.upgrade(config, "head")
    finally:
        settings.database_url = real_database_url

    engine = create_engine(test_url)
    yield engine

    engine.dispose()
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{test_url.database}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(autouse=True)
def clean_tables(test_engine):
    yield
    with test_engine.begin() as connection:
        connection.execute(text("TRUNCATE documents, chunks RESTART IDENTITY CASCADE"))


@pytest.fixture
def db(test_engine):
    session = sessionmaker(bind=test_engine)()
    yield session
    session.close()


@pytest.fixture
def client(test_engine):
    factory = sessionmaker(bind=test_engine)

    def get_test_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def vector_for(value: str) -> list[float]:
    """Fake embedding: text about cats and other text point in different directions."""
    vector = [0.0] * EMBEDDING_DIMENSIONS
    vector[0 if "cat" in value.lower() else 1] = 1.0
    return vector


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch):
    def fake(model, input):
        return SimpleNamespace(data=[{"embedding": vector_for(value)} for value in input])

    monkeypatch.setattr(litellm, "embedding", fake)


@pytest.fixture
def add_document(db):
    def add(filename, chunks, embed=True):
        document = Document(filename=filename, file_path="x", status="processed")
        db.add(document)
        db.flush()
        for index, (page, content) in enumerate(chunks):
            embedding = vector_for(content) if embed else None
            db.add(Chunk(document_id=document.id, chunk_index=index, page_number=page, content=content, embedding=embedding))
        db.commit()
        return document

    return add


@pytest.fixture
def fake_llm(monkeypatch):
    """Call fake_llm(replies) to make the LLM give these replies one by one. It gives back the calls made."""

    def use(replies):
        calls = []

        def fake(model, messages, tools=None):
            calls.append(list(messages))
            return SimpleNamespace(choices=[SimpleNamespace(message=replies.pop(0))])

        monkeypatch.setattr(litellm, "completion", fake)
        return calls

    return use
