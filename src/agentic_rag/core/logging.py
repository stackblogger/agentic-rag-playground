import logging.config

from agentic_rag.core.config import settings


def setup_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            # keep the loggers of uvicorn and other libraries as they are
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
            # libraries only show warnings and errors, our code shows LOG_LEVEL
            "root": {"level": "WARNING", "handlers": ["console"]},
            "loggers": {"agentic_rag": {"level": settings.log_level.upper()}},
        }
    )

    try:
        import litellm

        # litellm prints extra help text on every error, the log line is enough
        litellm.suppress_debug_info = True
    except ImportError:
        pass
