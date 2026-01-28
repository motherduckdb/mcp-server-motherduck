"""
E2E tests for HTTP transport modes.

Tests the MCP server with --transport http.
Also includes tests for deprecated --transport sse.
"""

import os
import subprocess
import time

import httpx
import pytest


def find_free_port():
    """Find a free port to use for the test server."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture
def memory_db():
    """Use in-memory database to avoid file locking issues in HTTP tests."""
    return ":memory:"


class MCPHttpServer:
    """Context manager to start/stop an MCP server with HTTP transport."""

    # MCP StreamableHTTP requires client to accept both JSON and SSE
    MCP_HEADERS = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    def __init__(
        self,
        transport: str,
        db_path: str,
        port: int,
        host: str = "127.0.0.1",
        extra_args: list = None,
    ):
        self.transport = transport
        self.db_path = db_path
        self.port = port
        self.host = host
        self.extra_args = extra_args or []
        self.process = None
        # Use 127.0.0.1 to connect even if binding to 0.0.0.0
        connect_host = "127.0.0.1" if host == "0.0.0.0" else host
        self.base_url = f"http://{connect_host}:{port}"

    def __enter__(self):
        env = os.environ.copy()
        env["motherduck_logging"] = "0"

        cmd = [
            "uv",
            "run",
            "mcp-server-motherduck",
            "--transport",
            self.transport,
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--db-path",
            self.db_path,
        ] + self.extra_args

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        # Wait for server to start
        self._wait_for_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def _wait_for_server(self, timeout: float = 10.0):
        """Wait for the server to be ready."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                with httpx.Client(follow_redirects=True, timeout=2.0) as client:
                    if self.transport == "sse":
                        # SSE (deprecated): check GET /sse endpoint returns 200
                        # Use stream=True to avoid waiting for full response
                        with client.stream("GET", f"{self.base_url}/sse") as response:
                            if response.status_code == 200:
                                return  # Server is up
                    else:
                        # HTTP: POST to /mcp/ with proper headers
                        response = client.post(
                            f"{self.base_url}/mcp/",
                            headers=self.MCP_HEADERS,
                            json={
                                "jsonrpc": "2.0",
                                "method": "initialize",
                                "params": {
                                    "protocolVersion": "2024-11-05",
                                    "capabilities": {},
                                    "clientInfo": {"name": "test", "version": "1.0"},
                                },
                                "id": 1,
                            },
                        )
                        if response.status_code in [200, 202]:
                            return  # Server is up
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ReadError):
                pass
            time.sleep(0.3)
        raise RuntimeError(f"Server did not start within {timeout} seconds")

    def post_mcp(self, client: httpx.Client, json_data: dict, timeout: float = 10.0):
        """Make a properly-formatted MCP request."""
        return client.post(
            f"{self.base_url}/mcp/",
            headers=self.MCP_HEADERS,
            json=json_data,
            timeout=timeout,
        )


# =============================================================================
# HTTP Transport Tests
# =============================================================================


class TestHttpTransport:
    """Tests for --transport http mode (MCP Streamable HTTP)."""

    def test_http_server_starts(self, memory_db):
        """HTTP server starts and accepts connections."""
        port = find_free_port()
        with MCPHttpServer("http", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                response = server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                        "id": 1,
                    },
                )
                assert response.status_code in [200, 202]

    def test_http_initialize(self, memory_db):
        """Can send initialize request via HTTP transport."""
        port = find_free_port()
        with MCPHttpServer("http", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                response = server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                        "id": 1,
                    },
                )
                assert response.status_code in [200, 202]

    def test_http_tools_list(self, memory_db):
        """Can list tools via HTTP transport."""
        port = find_free_port()
        with MCPHttpServer("http", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                # Initialize first
                init_response = server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                        "id": 1,
                    },
                )
                assert init_response.status_code in [200, 202]

                # List tools
                response = server.post_mcp(
                    client, {"jsonrpc": "2.0", "method": "tools/list", "id": 2}
                )
                assert response.status_code in [200, 202]

    def test_http_call_tool(self, memory_db):
        """Can call query tool via HTTP transport."""
        port = find_free_port()
        with MCPHttpServer("http", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                # Initialize
                server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                        "id": 1,
                    },
                )

                # Call query tool
                response = server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "execute_query",
                            "arguments": {"sql": "SELECT 1 as num"},
                        },
                        "id": 3,
                    },
                )
                assert response.status_code in [200, 202]

    def test_http_returns_json(self, memory_db):
        """HTTP transport always returns JSON responses."""
        port = find_free_port()
        with MCPHttpServer("http", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                # Initialize
                server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                        "id": 1,
                    },
                )

                # Query and verify JSON response
                response = server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "execute_query",
                            "arguments": {"sql": "SELECT 42 as answer"},
                        },
                        "id": 2,
                    },
                )
                assert response.status_code in [200, 202]
                # Verify it's valid JSON (will raise if not)
                response.json()


# =============================================================================
# Host Configuration Tests
# =============================================================================


class TestHostConfiguration:
    """Tests for --host configuration."""

    def test_host_binding(self, memory_db):
        """Server binds to specified host."""
        port = find_free_port()
        # Use 0.0.0.0 to bind to all interfaces, connect via 127.0.0.1
        with MCPHttpServer("http", memory_db, port, host="0.0.0.0") as _server:
            # Override base_url to connect via localhost since 0.0.0.0 is not routable
            with httpx.Client(follow_redirects=True) as client:
                response = client.post(
                    f"http://127.0.0.1:{port}/mcp/",
                    headers=MCPHttpServer.MCP_HEADERS,
                    json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                        "id": 1,
                    },
                )
                assert response.status_code in [200, 202]

    def test_localhost_binding(self, memory_db):
        """Server binds to localhost (127.0.0.1)."""
        port = find_free_port()
        with MCPHttpServer("http", memory_db, port, host="127.0.0.1") as server:
            with httpx.Client(follow_redirects=True) as client:
                response = server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                        "id": 1,
                    },
                )
                assert response.status_code in [200, 202]


# =============================================================================
# Deprecated SSE Transport Tests
# =============================================================================


class TestSSETransport:
    """Tests for deprecated --transport sse mode.

    Note: SSE transport is deprecated. Use --transport http instead.
    These tests ensure backward compatibility during the deprecation period.
    """

    def test_sse_server_starts(self, memory_db):
        """SSE server starts and returns SSE stream on GET /sse."""
        port = find_free_port()
        with MCPHttpServer("sse", memory_db, port) as server:
            with httpx.Client(timeout=5.0) as client:
                # SSE endpoint should be available and return streaming response
                # Use stream=True to avoid blocking on infinite SSE stream
                with client.stream("GET", f"{server.base_url}/sse") as response:
                    assert response.status_code == 200
                    # Should be SSE content type
                    content_type = response.headers.get("content-type", "")
                    assert "text/event-stream" in content_type

    def test_sse_messages_endpoint_exists(self, memory_db):
        """SSE /messages/ endpoint exists (even without session ID)."""
        port = find_free_port()
        with MCPHttpServer("sse", memory_db, port) as server:
            with httpx.Client() as client:
                # POST without session_id will fail, but endpoint exists
                response = client.post(
                    f"{server.base_url}/messages/",
                    json={"jsonrpc": "2.0", "method": "ping", "id": 1},
                    timeout=5.0,
                )
                # 400 is expected (missing session_id), but not 404
                assert response.status_code != 404


# =============================================================================
# Deprecated Stream Transport Alias Tests
# =============================================================================


class TestStreamTransportAlias:
    """Tests that deprecated --transport stream still works as alias for http."""

    def test_stream_alias_works(self, memory_db):
        """--transport stream still works (mapped to http)."""
        port = find_free_port()
        with MCPHttpServer("stream", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                response = server.post_mcp(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"},
                        },
                        "id": 1,
                    },
                )
                assert response.status_code in [200, 202]
