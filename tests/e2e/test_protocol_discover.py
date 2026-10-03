"""
E2E tests for the 2026-07-28 protocol revision over stdio.

Talks raw JSON-RPC to the server process so the check doesn't depend on a
client library's version negotiation. Regression test for #110.
"""

import json
import subprocess
import sys

ENVELOPE = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {"name": "e2e", "version": "1"},
    "io.modelcontextprotocol/clientCapabilities": {},
}


def _exchange(*requests: dict) -> list[dict]:
    """Send requests to a fresh in-memory server over stdio and return the responses."""
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from mcp_server_motherduck import main; main()",
            "--db-path",
            ":memory:",
            "--read-write",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        for req in requests:
            proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        return [json.loads(proc.stdout.readline()) for _ in requests]
    finally:
        proc.kill()
        proc.wait()


def _request(id_: int, method: str, **params) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "method": method, "params": {**params, "_meta": ENVELOPE}}


def test_server_discover_answers_without_handshake():
    """server/discover succeeds as the first message and advertises 2026-07-28."""
    [resp] = _exchange(_request(1, "server/discover"))
    assert "error" not in resp, resp
    assert "2026-07-28" in json.dumps(resp["result"])


def test_tools_work_on_2026_07_28_without_handshake():
    """Requests carrying the 2026-07-28 envelope are served with no initialize."""
    _, tools, call = _exchange(
        _request(1, "server/discover"),
        _request(2, "tools/list"),
        _request(3, "tools/call", name="execute_query", arguments={"sql": "SELECT 42 AS x"}),
    )
    assert "error" not in tools, tools
    assert "execute_query" in {t["name"] for t in tools["result"]["tools"]}
    assert "error" not in call, call
    assert call["result"].get("isError") is False
    assert "42" in json.dumps(call["result"]["content"])
