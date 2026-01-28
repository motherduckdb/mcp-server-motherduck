<p align="center">
  <img src="src/mcp_server_motherduck/assets/duck_feet_square.png" alt="DuckDB MCP Server" width="120">
</p>

<h1 align="center">DuckDB MCP Server</h1>

<p align="center">
  SQL analytics and data engineering for AI Assistants and IDEs.
</p>

<p align="center">
  <em>by <a href="https://motherduck.com">MotherDuck</a></em>
</p>

---

A local MCP server for DuckDB and MotherDuck databases, providing **read-write capabilities** to AI Assistants and IDEs.

> **Note**: This is a **local** MCP server. For zero-setup read-only access, see [MotherDuck's hosted MCP](https://motherduck.com/docs/sql-reference/mcp/).

> ⚠️ **Read-Only by Default (since v1.0.0)**: The server runs in read-only mode by default to protect against accidental data modification. Add `--read-write` to enable write access. See [Securing for Production](#securing-for-production) for more details.

## Quick Start

**Prerequisites**: Install `uv` via `pip install uv` or `brew install uv`

### Connecting to a Local DuckDB File

```json
{
  "mcpServers": {
    "Local DuckDB": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "/absolute/path/to/your.duckdb"]
    }
  }
}
```

The connection will be read-only by default. For write access, add `"--read-write"` to the args. Add `"--allow-switch-databases"` to enable switching between databases.

### Connecting to MotherDuck in Read-Write Mode

```json
{
  "mcpServers": {
    "MotherDuck (Read/Write)": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "md:", "--read-write"],
      "env": {
        "motherduck_token": "<YOUR_MOTHERDUCK_TOKEN>"
      }
    }
  }
}
```

See [Command Line Parameters](#command-line-parameters) for more options, [Securing for Production](#securing-for-production) for deployment guidance, and [Troubleshooting](#troubleshooting) if you encounter issues.

## Client Setup

| Client | Config Location |
|--------|-----------------|
| **Claude Desktop** | Settings → Developer → Edit Config, or install [MCPB package](https://github.com/motherduckdb/mcp-server-motherduck/releases) |
| **Claude Code** | Use CLI commands below |
| **Cursor** | Settings → MCP → Add new global MCP server |
| **VS Code** | `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)" |

<details>
<summary><b>Claude Code setup</b></summary>

**Local DuckDB:**
```bash
claude mcp add duckdb --transport stdio -- uvx mcp-server-motherduck --db-path /absolute/path/to/db.duckdb
```

**Local DuckDB (read-write):**
```bash
claude mcp add duckdb --transport stdio -- uvx mcp-server-motherduck --db-path /absolute/path/to/db.duckdb --read-write
```

**MotherDuck:**
```bash
claude mcp add motherduck --transport stdio --env motherduck_token=YOUR_TOKEN -- uvx mcp-server-motherduck --db-path md:
```

**Scoping options:**
- `--scope local` (default): Only available in current project
- `--scope project`: Shared with team via `.mcp.json`
- `--scope user`: Available across all your projects

**Manage servers:**
```bash
claude mcp list          # List configured servers
claude mcp remove duckdb # Remove a server
```

</details>

<details>
<summary><b>One-click install options</b></summary>

**VS Code:**

[![Install with UV in VS Code](https://img.shields.io/badge/VS_Code-Install_with_UV-0098FF?style=plastic)](https://insiders.vscode.dev/redirect/mcp/install?name=mcp-server-motherduck&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-motherduck%22%2C%22--db-path%22%2C%22md%3A%22%2C%22--motherduck-token%22%2C%22%24%7Binput%3Amotherduck_token%7D%22%5D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22motherduck_token%22%2C%22description%22%3A%22MotherDuck+Token%22%2C%22password%22%3Atrue%7D%5D) [![Install with UV in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_with_UV-24bfa5?style=plastic&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=mcp-server-motherduck&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-motherduck%22%2C%22--db-path%22%2C%22md%3A%22%2C%22--motherduck-token%22%2C%22%24%7Binput%3Amotherduck_token%7D%22%5D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22motherduck_token%22%2C%22description%22%3A%22MotherDuck+Token%22%2C%22password%22%3Atrue%7D%5D&quality=insiders)

**Cursor:**

[<img src="https://cursor.com/deeplink/mcp-install-dark.svg" alt="Install in Cursor">](https://cursor.com/en/install-mcp?name=DuckDB&config=eyJjb21tYW5kIjoidXZ4IG1jcC1zZXJ2ZXItbW90aGVyZHVjayAtLWRiLXBhdGggOm1lbW9yeToiLCJlbnYiOnsibW90aGVyZHVja190b2tlbiI6IiJ9fQ%3D%3D)

</details>

<details>
<summary><b>Other clients (Windsurf, etc.)</b></summary>

Any MCP-compatible client can use this server. Add the JSON configuration from Quick Start to your client's MCP config file. Consult your client's documentation for the config file location.

</details>

## Tools

| Tool | Description | Required Inputs | Optional Inputs |
|------|-------------|-----------------|-----------------|
| `execute_query` | Execute SQL query (DuckDB dialect) | `sql` | - |
| `list_databases` | List all databases (useful for MotherDuck or multiple attached DBs) | - | - |
| `list_tables` | List tables and views | - | `database`, `schema` |
| `list_columns` | List columns of a table/view | `table` | `database`, `schema` |
| `switch_database_connection`* | Switch to different database | `path` | `create_if_missing` |

*Requires `--allow-switch-databases` flag

All tools return JSON. Results are limited to 1024 rows / 50,000 chars by default (configurable via `--max-rows`, `--max-chars`).

## Securing for Production

**Read-only mode alone is not sufficient for production security.**

For production deployments, we recommend **MotherDuck with SaaS mode and read-scaling tokens**:

- [Read Scaling documentation](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/read-scaling/#creating-a-read-scaling-token) - tokens that restrict write capabilities
- [SaaS Mode documentation](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-saas-mode) - restricts local file access

For local DuckDB, use `--init-sql` to apply security settings like `SET enable_external_access=false` or `SET lock_configuration=true`. See the [Securing DuckDB guide](https://duckdb.org/docs/stable/operations_manual/securing_duckdb/overview) for all available options.

## Command Line Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--db-path` | `:memory:` | Database path: local file (absolute), `md:` (MotherDuck), or `s3://` URL |
| `--motherduck-token` | `motherduck_token` env var | MotherDuck access token |
| `--read-write` | `False` | Enable write access |
| `--motherduck-saas-mode` | `False` | MotherDuck SaaS mode (restricts local access) |
| `--allow-switch-databases` | `False` | Enable `switch_database_connection` tool |
| `--max-rows` | `1024` | Max rows returned |
| `--max-chars` | `50000` | Max characters returned |
| `--query-timeout` | `-1` | Query timeout in seconds (-1 = disabled) |
| `--init-sql` | `None` | SQL to execute on startup |
| `--ephemeral-connections` | `True` | Use temporary connections for read-only local files |
| `--transport` | `stdio` | Transport type: `stdio` or `http` |
| `--port` | `8000` | Port for HTTP transport |
| `--host` | `127.0.0.1` | Host for HTTP transport |

## Troubleshooting

- **`spawn uvx ENOENT`**: Specify full path to `uvx` (run `which uvx` to find it)
- **File locked**: Make sure `--ephemeral-connections` is turned on (default: true) and that you're not connected in read-write mode

## Resources

- [Close the Loop: Faster Data Pipelines with MCP, DuckDB & AI (Blog)](https://motherduck.com/blog/faster-data-pipelines-with-mcp-duckdb-ai/)
- [Faster Data Pipelines with MCP and DuckDB (YouTube)](https://www.youtube.com/watch?v=yG1mv8ZRxcU)

## Development

To run from source:

```json
{
  "mcpServers": {
    "Local DuckDB (Dev)": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-server-motherduck", "run", "mcp-server-motherduck", "--db-path", "md:"],
      "env": {
        "motherduck_token": "<YOUR_MOTHERDUCK_TOKEN>"
      }
    }
  }
}
```

## Release Process

1. Run the `Release New Version` GitHub Action
2. Enter version in `MAJOR.MINOR.PATCH` format
3. The workflow bumps version, publishes to PyPI/MCP registry, and creates the GitHub release with MCPB package

## License

MIT License - see [LICENSE](LICENSE) file.

##
mcp-name: io.github.motherduckdb/mcp-server-motherduck
