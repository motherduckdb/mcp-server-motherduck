from mcp_server_motherduck.database import DatabaseClient


def _client_without_init() -> DatabaseClient:
    return DatabaseClient.__new__(DatabaseClient)


def test_env_token_saas_mode_appends_flag(monkeypatch):
    monkeypatch.delenv("motherduck_token", raising=False)
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "env-token")

    path, db_type = _client_without_init()._resolve_db_path_type(
        "md:", motherduck_token=None, saas_mode=True
    )

    assert db_type == "motherduck"
    assert path == "md:?motherduck_token=env-token&saas_mode=true"


def test_env_token_without_saas_mode_does_not_append_flag(monkeypatch):
    monkeypatch.delenv("motherduck_token", raising=False)
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "env-token")

    path, db_type = _client_without_init()._resolve_db_path_type(
        "md:", motherduck_token=None, saas_mode=False
    )

    assert db_type == "motherduck"
    assert path == "md:?motherduck_token=env-token"
