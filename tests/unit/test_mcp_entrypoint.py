from agentic_rag.mcp_server import __main__ as entrypoint


def test_main_runs_the_server_on_stdio(monkeypatch, capsys):
    runs = []

    class FakeServer:
        def run(self, transport):
            runs.append(transport)

    monkeypatch.setattr(entrypoint, "setup_logging", lambda: None)
    monkeypatch.setattr(entrypoint, "create_server", lambda: FakeServer())

    entrypoint.main()

    assert runs == ["stdio"]
    # stdout belongs to the MCP protocol, so nothing else may be printed there
    assert capsys.readouterr().out == ""
