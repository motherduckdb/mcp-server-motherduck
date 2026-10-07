"""E2E tests for the 2026-07-28 protocol revision over stdio."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError

import pytest

ENVELOPE = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {"name": "e2e", "version": "1"},
    "io.modelcontextprotocol/clientCapabilities": {},
}


def _exchange(*requests: dict) -> list[dict]:
    """Send requests to a fresh server and return its JSON-RPC responses."""
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
        stderr=subprocess.PIPE,
        text=True,
    )
    responses = []
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            for request in requests:
                proc.stdin.write(json.dumps(request) + "\n")
                proc.stdin.flush()
                future = executor.submit(proc.stdout.readline)
                try:
                    line = future.result(timeout=10)
                except TimeoutError:
                    proc.kill()
                    pytest.fail("MCP server did not respond within 10 seconds")
                assert line, proc.stderr.read()
                responses.append(json.loads(line))
        return responses
    finally:
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def _request(id_: int, method: str, **params) -> dict:
    params["_meta"] = ENVELOPE
    return {"jsonrpc": "2.0", "id": id_, "method": method, "params": params}


def test_server_discover_answers_without_handshake():
    """server/discover succeeds first and advertises the requested revision."""
    [response] = _exchange(_request(1, "server/discover"))
    assert "error" not in response, response
    assert "2026-07-28" in json.dumps(response["result"])


def test_tools_work_on_2026_07_28_without_handshake():
    """Versioned requests work without an initialize handshake."""
    _, tools, call = _exchange(
        _request(1, "server/discover"),
        _request(2, "tools/list"),
        _request(3, "tools/call", name="execute_query", arguments={"sql": "SELECT 42 AS x"}),
    )
    assert "error" not in tools, tools
    assert "execute_query" in {tool["name"] for tool in tools["result"]["tools"]}
    assert "error" not in call, call
    assert call["result"].get("isError") is False
    assert "42" in json.dumps(call["result"]["content"])
