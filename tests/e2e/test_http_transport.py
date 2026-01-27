"""
E2E tests for HTTP transport modes (SSE and stream).

Tests the MCP server with --transport sse and --transport stream.
"""

import os
import subprocess
import time
import pytest
import httpx


def find_free_port():
    """Find a free port to use for the test server."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
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
    
    def __init__(self, transport: str, db_path: str, port: int, extra_args: list = None):
        self.transport = transport
        self.db_path = db_path
        self.port = port
        self.extra_args = extra_args or []
        self.process = None
        self.base_url = f"http://127.0.0.1:{port}"
    
    def __enter__(self):
        env = os.environ.copy()
        env["motherduck_logging"] = "0"
        
        cmd = [
            "uv", "run", "mcp-server-motherduck",
            "--transport", self.transport,
            "--port", str(self.port),
            "--db-path", self.db_path,
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
                        # SSE: check GET /sse endpoint returns 200
                        # Use stream=True to avoid waiting for full response
                        with client.stream("GET", f"{self.base_url}/sse") as response:
                            if response.status_code == 200:
                                return  # Server is up
                    else:
                        # Stream: POST to /mcp/ with proper headers
                        response = client.post(
                            f"{self.base_url}/mcp/",
                            headers=self.MCP_HEADERS,
                            json={"jsonrpc": "2.0", "method": "initialize", "params": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "test", "version": "1.0"}
                            }, "id": 1},
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
# SSE Transport Tests
# =============================================================================

class TestSSETransport:
    """Tests for --transport sse mode.
    
    Note: Full SSE protocol testing is complex because it requires maintaining
    a streaming connection to get session IDs. These tests verify basic
    server functionality.
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
# Stream Transport Tests  
# =============================================================================

class TestStreamTransport:
    """Tests for --transport stream mode."""
    
    def test_stream_server_starts(self, memory_db):
        """Stream server starts and accepts connections."""
        port = find_free_port()
        with MCPHttpServer("stream", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                response = server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"}
                    },
                    "id": 1
                })
                assert response.status_code in [200, 202]
    
    def test_stream_initialize(self, memory_db):
        """Can send initialize request via stream transport."""
        port = find_free_port()
        with MCPHttpServer("stream", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                response = server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"}
                    },
                    "id": 1
                })
                assert response.status_code in [200, 202]
    
    def test_stream_tools_list(self, memory_db):
        """Can list tools via stream transport."""
        port = find_free_port()
        with MCPHttpServer("stream", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                # Initialize first
                init_response = server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"}
                    },
                    "id": 1
                })
                assert init_response.status_code in [200, 202]
                
                # List tools
                response = server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 2
                })
                assert response.status_code in [200, 202]
    
    def test_stream_call_tool(self, memory_db):
        """Can call query tool via stream transport."""
        port = find_free_port()
        with MCPHttpServer("stream", memory_db, port) as server:
            with httpx.Client(follow_redirects=True) as client:
                # Initialize
                server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"}
                    },
                    "id": 1
                })
                
                # Call query tool
                response = server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "query",
                        "arguments": {"query": "SELECT 1 as num"}
                    },
                    "id": 3
                })
                assert response.status_code in [200, 202]


# =============================================================================
# Stream Transport with JSON Response Tests
# =============================================================================

class TestStreamJsonResponse:
    """Tests for --transport stream --json-response mode."""
    
    def test_json_response_server_starts(self, memory_db):
        """Stream server with json-response starts correctly."""
        port = find_free_port()
        with MCPHttpServer("stream", memory_db, port, ["--json-response"]) as server:
            with httpx.Client(follow_redirects=True) as client:
                response = server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"}
                    },
                    "id": 1
                })
                assert response.status_code in [200, 202]
    
    def test_json_response_query(self, memory_db):
        """Can execute queries with json-response mode."""
        port = find_free_port()
        with MCPHttpServer("stream", memory_db, port, ["--json-response"]) as server:
            with httpx.Client(follow_redirects=True) as client:
                # Initialize
                server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"}
                    },
                    "id": 1
                })
                
                # Query
                response = server.post_mcp(client, {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "query",
                        "arguments": {"query": "SELECT 42 as answer"}
                    },
                    "id": 2
                })
                assert response.status_code in [200, 202]
