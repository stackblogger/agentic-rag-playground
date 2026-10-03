from agentic_rag.core.logging import setup_logging
from agentic_rag.mcp_server.server import create_server


def main() -> None:
    setup_logging()
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
