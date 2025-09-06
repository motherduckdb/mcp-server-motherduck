# MCP Client Configuration for USITC Tariffs Server

## ⚠️ Important: Do NOT use build_and_serve.py with MCP clients

The `scripts/build_and_serve.py` script is designed for interactive development and testing, not for MCP client integration. It will cause issues with STDIO communication.

## Correct Configuration for MCP Clients

### For Perplexity

Add this configuration to your MCP settings:

```json
### For Perplexity

Add this configuration to your MCP settings:

```json
{
  "name": "usitc-tariffs",
  "command": "uv",
  "args": [
    "run",
    "--project",
    "/Users/jmabry/repos/mcp-tarrifs",
    "mcp-server-motherduck",
    "--db-path",
    "/Users/jmabry/repos/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
    "--read-only"
  ]
}
```

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "usitc-tariffs": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/Users/jmabry/repos/mcp-tarrifs",
        "mcp-server-motherduck",
        "--db-path",
        "/Users/jmabry/repos/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
        "--read-only"
      ]
    }
  }
}
```

### For Cursor/VS Code

Add this to your MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "usitc-tariffs": {
        "command": "uv",
        "args": [
          "run",
          "--project",
          "/Users/jmabry/repos/mcp-tarrifs",
          "mcp-server-motherduck",
          "--db-path",
          "/Users/jmabry/repos/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
          "--read-only"
        ]
      }
    }
  }
}
```
```

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "usitc-tariffs": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "mcp_server_motherduck",
        "--db-path",
        "/Users/jmabry/repos/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
        "--read-only"
      ],
      "cwd": "/Users/jmabry/repos/mcp-tarrifs",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

### For Cursor/VS Code

Add this to your MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "usitc-tariffs": {
        "command": "uv",
        "args": [
          "run",
          "python",
          "-m",
          "mcp_server_motherduck",
          "--db-path",
          "/Users/jmabry/repos/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
          "--read-only"
        ],
        "cwd": "/Users/jmabry/repos/mcp-tarrifs",
        "env": {
          "PYTHONPATH": "src"
        }
      }
    }
  }
}
```

### Alternative: Use the MCP Launcher Script

For a simpler approach that handles database building automatically:

```json
{
  "name": "usitc-tariffs",
  "command": "uv",
  "args": [
    "run",
    "--project",
    "/Users/jmabry/repos/mcp-tarrifs",
    "python",
    "scripts/mcp_server_launcher.py"
  ]
}
```

## Alternative: Use Absolute Python Path

If you prefer not to use `uv`, you can also use the Python executable directly with the module approach:

```json
{
  "command": "python",
  "args": [
    "-m",
    "mcp_server_motherduck",
    "--db-path",
    "/Users/jmabry/repos/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
    "--read-only"
  ],
  "cwd": "/Users/jmabry/repos/mcp-tarrifs",
  "env": {
    "PYTHONPATH": "src"
  }
}
```

Note: The `PYTHONPATH=src` is needed for the module approach because the packages are located in the `src/` directory, not at the project root.

## Setup Requirements

1. **Build the database first** (only needed once):
   ```bash
   cd /Users/jmabry/repos/mcp-tarrifs
   uv run python src/tariffs_db/db_build.py --all --years 10
   ```

2. **Install dependencies**:
   ```bash
   cd /Users/jmabry/repos/mcp-tarrifs
   uv sync
   ```

## Troubleshooting

- **Database not found**: Run the database build command above
- **Module not found**: Ensure you're in the correct working directory and dependencies are installed
- **Permission errors**: Make sure the database file is readable
- **Connection issues**: Check that the STDIO transport is working by testing with a simple MCP client

## What build_and_serve.py is For

Use `build_and_serve.py` only for:
- Local development and testing
- One-time database setup
- Getting configuration examples
- Interactive debugging

Never use it as the command for MCP client configurations.
