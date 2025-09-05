# MCP STDIO Compatibility Issue Analysis

## Problem Summary

The original `build_and_serve.py` script was not compatible with MCP clients like Perplexity that use STDIO transport because:

### 1. Interactive Input Conflicts
```python
input("\n🎯 Press Enter to start the MCP server (or Ctrl+C to exit)...")
```
This blocks waiting for user input, but MCP clients use stdin for JSON-RPC communication.

### 2. Stdout Pollution
The script prints extensive logging and configuration info to stdout:
```python
print("🦆 USITC Tariff Database Builder & MCP Server")
print("📊 Database contains 10 tables with 142K+ rows of tariff data")
```
MCP STDIO transport requires clean stdout for JSON-RPC protocol messages only.

### 3. Subprocess Isolation
The script launches the server as a subprocess, which can interfere with STDIO handling:
```python
subprocess.run(cmd, cwd=PROJECT_ROOT)
```

## Solution Implemented

### 1. Created MCP-Compatible Launcher
- **File**: `scripts/mcp_server_launcher.py`
- **Features**:
  - No interactive prompts
  - Minimal output (only to stderr)
  - Direct module import instead of subprocess
  - Automatic database building if needed

### 2. Added Module Entry Point
- **File**: `src/mcp_server_motherduck/__main__.py`
- **Purpose**: Allows running the server as `python -m mcp_server_motherduck`

### 3. Updated Documentation
- **File**: `MCP_CLIENT_CONFIG.md`
- **Content**: Correct configuration examples for all major MCP clients
- **Warning**: Clear guidance about not using the interactive script

### 4. Added Warnings
- Updated `build_and_serve.py` with clear warnings about MCP incompatibility

## Correct MCP Client Configuration

### For Perplexity (Recommended):
```json
{
  "name": "usitc-tariffs",
  "command": "uv",
  "args": [
    "run", "mcp-server-motherduck",
    "--db-path", "/Users/jmabry/repos/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
    "--read-only"
  ],
  "cwd": "/Users/jmabry/repos/mcp-tarrifs"
}
```

### Alternative (using module with PYTHONPATH):
```json
{
  "name": "usitc-tariffs",
  "command": "python",
  "args": [
    "-m", "mcp_server_motherduck",
    "--db-path", "/Users/jmabry/repos/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
    "--read-only"
  ],
  "cwd": "/Users/jmabry/repos/mcp-tarrifs",
  "env": { "PYTHONPATH": "src" }
}
```

The first approach is cleaner because it uses the script entry point defined in `pyproject.toml`.

## Key Principles for MCP STDIO Compatibility

1. **Clean STDIO**: Never print to stdout except for MCP protocol messages
2. **No Interactive Prompts**: Never call `input()` or wait for user interaction
3. **Direct Execution**: Import and run server code directly, don't use subprocess
4. **Error Handling**: Log errors to stderr, not stdout
5. **Module Structure**: Ensure packages are properly structured for `-m` execution

## Testing

The launcher has been tested and verified to:
- ✅ Build database when missing
- ✅ Start server without interactive prompts
- ✅ Maintain clean stdout for MCP communication
- ✅ Handle command line arguments properly
- ✅ Work with both direct Python and uv execution
