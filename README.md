<p align="center">
  <img src="src/mcp_server_motherduck/assets/duck_feet_square.png" alt="MotherDuck / DuckDB Local MCP Server" width="120">
</p>

<h1 align="center">MotherDuck / DuckDB Local MCP Server</h1>

<p align="center">
  SQL analytics and data engineering for AI Assistants and IDEs.
</p>

---

Connect AI assistants to your data using DuckDB's powerful analytical SQL engine. Supports connecting to local DuckDB files, in-memory databases, S3-hosted databases, and MotherDuck. Allows executing SQL read- and write-queries, browsing database catalogs, and switching between different database connections on-the-fly.

**Looking for a fully-managed remote MCP server for MotherDuck?** → [Go to the MotherDuck Remote MCP docs](https://motherduck.com/docs/sql-reference/mcp/)

### Remote vs Local MCP

| | **[Remote MCP](https://motherduck.com/docs/sql-reference/mcp/)** | **Local MCP** (this repo) |
|---|---|---|
| **Hosting** | Hosted by MotherDuck | Runs locally/self-hosted |
| **Setup** | Zero-setup | Requires local installation |
| **Access** | Read-only | Read-write supported |
| **Local filesystem** | - | Query across local and remote databases, ingest data from / export data to local filesystem |

> ⚠️ **Read-Only by Default (since v1.0.0)**: The local MCP server runs in read-only mode by default to protect against accidental data modification. Add `--read-write` to enable write access. See [Securing for Production](#securing-for-production) for more details.

## Quick Start

**Prerequisites**: Install `uv` via `pip install uv` or `brew install uv`

### Connecting to In-Memory DuckDB (Dev Mode)

```json
{
  "mcpServers": {
    "DuckDB (in-memory, r/w)": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", ":memory:", "--read-write", "--allow-switch-databases"]
    }
  }
}
```

Full flexibility with no guardrails — read-write access and the ability to switch to any database (local files, S3, or MotherDuck) at runtime.

### Connecting to a Local DuckDB File in Read-Only Mode

```json
{
  "mcpServers": {
    "DuckDB (read-only)": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "/absolute/path/to/your.duckdb"]
    }
  }
}
```

Connects to a specific DuckDB file in read-only mode. Won't hold on to the file lock, so convenient to use alongside a write connection to the same DuckDB file. You can also connect to remote DuckDB files on S3 using `s3://bucket/path.duckdb` — see [Environment Variables](#environment-variables) for S3 authentication. If you're considering third-party access to the MCP, see [Securing for Production](#securing-for-production).

### Connecting to MotherDuck in Read-Write Mode

```json
{
  "mcpServers": {
    "MotherDuck (local, r/w)": {
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

| Client | Config Location | One-Click Install |
|--------|-----------------|-------------------|
| **Claude Desktop** | Settings → Developer → Edit Config, or install [MCPB package](https://github.com/motherduckdb/mcp-server-motherduck/releases) | - |
| **Claude Code** | Use CLI commands below | - |
| **Cursor** | Settings → MCP → Add new global MCP server | [<img src="https://cursor.com/deeplink/mcp-install-dark.svg" alt="Install in Cursor" height="20">](https://cursor.com/en/install-mcp?name=DuckDB&config=eyJjb21tYW5kIjoidXZ4IG1jcC1zZXJ2ZXItbW90aGVyZHVjayAtLWRiLXBhdGggOm1lbW9yeTogLS1yZWFkLXdyaXRlIC0tYWxsb3ctc3dpdGNoLWRhdGFiYXNlcyIsImVudiI6e319) |
| **VS Code** | `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)" | [![Install with UV in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square)](https://insiders.vscode.dev/redirect/mcp/install?name=mcp-server-motherduck&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-motherduck%22%2C%22--db-path%22%2C%22md%3A%22%2C%22--motherduck-token%22%2C%22%24%7Binput%3Amotherduck_token%7D%22%5D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22motherduck_token%22%2C%22description%22%3A%22MotherDuck+Token%22%2C%22password%22%3Atrue%7D%5D) |

Any MCP-compatible client can use this server. Add the JSON configuration from [Quick Start](#quick-start) to your client's MCP config file. Consult your client's documentation for the config file location.

<details>
<summary><b>Claude Code CLI commands</b></summary>

**In-Memory DuckDB (Dev Mode):**
```bash
claude mcp add duckdb --transport stdio -- uvx mcp-server-motherduck --db-path :memory: --read-write --allow-switch-databases
```

**Local DuckDB (Read-Only):**
```bash
claude mcp add duckdb --transport stdio -- uvx mcp-server-motherduck --db-path /absolute/path/to/db.duckdb
```

**MotherDuck (Read-Write):**
```bash
claude mcp add motherduck --transport stdio --env motherduck_token=YOUR_TOKEN -- uvx mcp-server-motherduck --db-path md: --read-write
```

</details>

## Tools

| Tool | Description | Required Inputs | Optional Inputs |
|------|-------------|-----------------|-----------------|
| `execute_query` | Execute SQL query (DuckDB dialect) | `sql` | - |
| `list_databases` | List all databases (useful for MotherDuck or multiple attached DBs) | - | - |
| `list_tables` | List tables and views | - | `database`, `schema` |
| `list_columns` | List columns of a table/view | `table` | `database`, `schema` |
| `switch_database_connection`* | Switch to different database | `path` | `create_if_not_exists` |

*Requires `--allow-switch-databases` flag

All tools return JSON. Results are limited to 1024 rows / 50,000 chars by default (configurable via `--max-rows`, `--max-chars`).

## Securing for Production

When giving third parties access to a self-hosted MCP server, **read-only mode alone is not sufficient** — it still allows access to the local filesystem, changing DuckDB settings, and other potentially sensitive operations.

For production deployments with third-party access, we recommend **[MotherDuck Remote MCP](https://motherduck.com/docs/sql-reference/mcp/)** — zero-setup, read-only, and hosted by MotherDuck.

**Self-hosting MotherDuck MCP:** Fork this repo and customize as needed. Use a **[service account](https://motherduck.com/docs/key-tasks/service-accounts-guide/)** with **[read-scaling tokens](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/read-scaling/#creating-a-read-scaling-token)** and enable **[SaaS mode](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-saas-mode)** to restrict local file access.

**Self-hosting DuckDB MCP:** Use `--init-sql` to apply security settings. See the [Securing DuckDB guide](https://duckdb.org/docs/stable/operations_manual/securing_duckdb/overview) for available options.

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

## Environment Variables

| Variable | Description |
|----------|-------------|
| `motherduck_token` or `MOTHERDUCK_TOKEN` | MotherDuck access token (alternative to `--motherduck-token`) |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 database connections |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 database connections |
| `AWS_SESSION_TOKEN` | AWS session token for temporary credentials (IAM roles, SSO, EC2 instance profiles) |
| `AWS_DEFAULT_REGION` | AWS region for S3 connections |

## Troubleshooting

- **`spawn uvx ENOENT`**: Specify full path to `uvx` (run `which uvx` to find it)
- **File locked**: Make sure `--ephemeral-connections` is turned on (default: true) and that you're not connected in read-write mode

## Resources

- [MotherDuck MCP Documentation](https://motherduck.com/docs/sql-reference/mcp/)
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
