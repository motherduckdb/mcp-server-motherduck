import json
from pathlib import Path


def test_manifest_secure_defaults_match_documented_server_defaults() -> None:
    manifest_path = Path(__file__).resolve().parents[1] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    user_config = manifest["user_config"]

    assert user_config["read_write"]["default"] is False
    assert user_config["allow_switch_databases"]["default"] is False
