import logging

from agentic_rag.core.config import settings
from agentic_rag.core.logging import setup_logging


def test_log_level_comes_from_settings(monkeypatch):
    monkeypatch.setattr(settings, "log_level", "debug")
    setup_logging()
    try:
        assert logging.getLogger("agentic_rag").level == logging.DEBUG
    finally:
        monkeypatch.setattr(settings, "log_level", "INFO")
        setup_logging()

    assert logging.getLogger("agentic_rag").level == logging.INFO
