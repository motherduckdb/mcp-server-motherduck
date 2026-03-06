# Installing MCP Server MotherDuck for Claude Desktop

This guide walks you through installing the MotherDuck MCP server for use with the Claude Desktop app.

## Prerequisites

- **`uv`** installed — `pip install uv` or `brew install uv`
- **Claude Desktop app** installed ([download here](https://claude.ai/download))
- **MotherDuck account** with an access token (for cloud databases — not needed for local DuckDB)

### Verify uv Installation

```bash
uv --version
```

---

## Step 1: Get Your MotherDuck Token (if using MotherDuck)

1. Log in to [MotherDuck](https://app.motherduck.com/)
2. Click your profile icon (top right) → **Settings**
3. Go to **Access Tokens**
4. Click **Create Token**
5. Copy the token (you'll need it for the next step)

For local DuckDB use, skip this step.

---

## Step 2: Configure Claude Desktop

### Find the Config File

| Platform | Location |
|----------|----------|
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |

### Windows Quick Access

Press `Win + R`, type `%APPDATA%\Claude`, and press Enter.

### macOS Quick Access

In Finder, press `Cmd + Shift + G` and paste `~/Library/Application Support/Claude/`

---

### Edit the Config File

Open `claude_desktop_config.json` in a text editor. If it doesn't exist, create it.

#### Connecting to MotherDuck (cloud)

```json
{
  "mcpServers": {
    "motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
        "--db-path", "md:",
        "--read-write",
        "--motherduck-token", "YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

**Replace `YOUR_TOKEN_HERE` with your actual MotherDuck token.**

#### Connecting to a Local DuckDB File (read-only)

```json
{
  "mcpServers": {
    "duckdb": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
        "--db-path", "/absolute/path/to/your/database.db"
      ]
    }
  }
}
```

#### In-Memory DuckDB (dev/scratch)

```json
{
  "mcpServers": {
    "duckdb": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
        "--db-path", ":memory:",
        "--read-write",
        "--allow-switch-databases"
      ]
    }
  }
}
```

---

## Step 3: Restart Claude Desktop

1. Fully quit Claude Desktop (not just close the window)
   - **Windows**: Right-click the system tray icon → Quit
   - **macOS**: Claude → Quit Claude (or `Cmd + Q`)
2. Reopen Claude Desktop
3. Check the MCP server status in Settings → Developer

You should see `motherduck` (or `duckdb`) listed as connected.

---

## Step 4: Test the Connection

In a new Claude conversation, try:

> "List all available databases"

or

> "Run this query: SELECT 42 AS answer"

---

## Available Tools

Once connected, Claude has access to these tools:

| Tool | Description |
|------|-------------|
| `execute_query` | Execute SQL queries against DuckDB/MotherDuck |
| `list_databases` | List all available databases |
| `list_tables` | List tables and views in a database |
| `list_columns` | List columns of a table or view |
| `switch_database_connection` | Switch to a different database (requires `--allow-switch-databases`) |

### Identifier Quoting

When working with tables or columns that have special characters (hyphens, colons, spaces), they must be double-quoted in SQL:

```sql
-- This FAILS:
SELECT * FROM ACSDT5Y2023_B19080-Data;

-- This WORKS:
SELECT * FROM "ACSDT5Y2023_B19080-Data";

-- Column with colon:
SELECT "Unnamed: 12" FROM "my-table";
```

Use `list_tables` and `list_columns` to discover the exact table and column names before writing queries.

---

## Troubleshooting

### "Command not found" / `uvx` not found

Install `uv`:
```bash
pip install uv
# or on macOS
brew install uv
```

### MCP Server Shows "Failed" in Claude Desktop

1. Check your token is correct (for MotherDuck)
2. Verify the database path exists (for local files)
3. Try running the command manually in terminal:
   ```bash
   uvx mcp-server-motherduck --db-path :memory: --read-write
   ```
4. Check for error messages

### "Server disconnected" Error

Run the command manually to see the actual error. Common causes:
- Invalid or expired MotherDuck token
- Database file path does not exist
- Network connectivity issues (for MotherDuck)

### Updating to Latest Version

`uvx` always fetches the latest published version. To force a refresh:
```bash
uv cache clean
```

### Read-Only Mode Note

The server runs **read-only by default**. Add `--read-write` to enable INSERT, UPDATE, DELETE, CREATE, and DROP operations.

MotherDuck connections in read-only mode require a [read-scaling token](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#read-scaling-tokens). Regular tokens require `--read-write`.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/motherduckdb/mcp-server-motherduck/issues)
- **MotherDuck documentation**: [docs.motherduck.com](https://docs.motherduck.com/)
- **MotherDuck Remote MCP** (zero-setup alternative): [motherduck.com/docs/sql-reference/mcp/](https://motherduck.com/docs/sql-reference/mcp/)
