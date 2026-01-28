# MotherDuck's DuckDB MCP Server

## What is the main difference between MotherDuck's remote MCP and this local MCP?

If you are choosing between MotherDuck's hosted/remote MCP and this local MCP:

- **Remote MCP (hosted by MotherDuck)**: read-only, zero-setup, and the recommended default for most users who just need query access. See the [MotherDuck MCP docs](https://motherduck.com/docs/sql-reference/mcp/).
- **Local MCP (this repo)**: self-hosted and supports write access when you need to create, modify, or manage data in a controlled environment.

A local MCP server implementation that interacts with DuckDB and MotherDuck databases, providing SQL analytics capabilities to AI Assistants and IDEs.

> This repository contains the **self-hosted/local** MCP server implementation.

[<img src="https://cursor.com/deeplink/mcp-install-dark.svg" alt="Install in Cursor">](https://cursor.com/en/install-mcp?name=DuckDB&config=eyJjb21tYW5kIjoidXZ4IG1jcC1zZXJ2ZXItbW90aGVyZHVjayAtLWRiLXBhdGggOm1lbW9yeToiLCJlbnYiOnsibW90aGVyZHVja190b2tlbiI6IiJ9fQ%3D%3D)

## Resources
- [Close the Loop: Faster Data Pipelines with MCP, DuckDB & AI (Blogpost)](https://motherduck.com/blog/faster-data-pipelines-with-mcp-duckdb-ai/)
- [Faster Data Pipelines development with MCP and DuckDB (YouTube)](https://www.youtube.com/watch?v=yG1mv8ZRxcU)

## Important: Read-Only by Default

**The server now runs in read-only mode by default** for local DuckDB files and MotherDuck databases. This protects against accidental data modification by LLMs.

- To enable write access, use the `--read-write` flag
- Read-only mode on local DuckDB files uses temporary connections by default (`--ephemeral-connections`), creating a new connection for each query so other processes can write to the file
- For persistent read-only connections, use `--no-ephemeral-connections`

## Tools

The server provides the following tools:

- `execute_query`: Execute a SQL query on the DuckDB or MotherDuck database
  - **Inputs**:
    - `sql` (string, required): The SQL query to execute
  - **Output**: JSON with columns, columnTypes, rows, and rowCount

- `list_databases`: List all databases available in the connection *(auto-enabled for MotherDuck, requires `--enable-list-databases` flag for local DuckDB)*
  - **Output**: JSON with database names and types

- `list_tables`: List all tables and views in a database
  - **Inputs**:
    - `database` (string, required): Database name
    - `schema` (string, optional): Schema name filter
  - **Output**: JSON with table/view names, types, and comments

- `list_columns`: List all columns of a table or view
  - **Inputs**:
    - `database` (string, required): Database name
    - `table` (string, required): Table or view name
    - `schema` (string, optional): Schema name (defaults to 'main')
  - **Output**: JSON with column names, types, and comments

- `switch_database_connection`: Switch to a different database connection *(requires `--allow-switch-databases` flag)*
  - **Inputs**:
    - `path` (string, required): Database path. For local files, must be an absolute path. Also accepts `:memory:`, `md:database_name`, or `s3://` paths.
  - **Output**: JSON with switch result including previous and current database
  - **Note**: The new connection respects the server's read-only/read-write mode

All tools return structured JSON responses. Query interactions use DuckDB SQL syntax.

**Result Limiting**: Query results are automatically limited to prevent using up too much context:
- Maximum 1024 rows by default (configurable with `--max-rows`)
- Maximum 50,000 characters by default (configurable with `--max-chars`)
- Truncated responses include a note about truncation

## Command Line Parameters

The MCP server supports the following parameters:

| Parameter | Type | Default | Description                                                                                                                                                                                                                                                    |
|-----------|------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--transport` | Choice | `stdio` | Transport type. Options: `stdio`, `http`. (`sse` and `stream` are deprecated aliases)                                                                                                                                                                          |
| `--port` | Integer | `8000` | Port to listen on for HTTP transport mode                                                                                                                                                                                                                      |
| `--host` | String | `127.0.0.1` | Host to bind the MCP server for HTTP transport mode                                                                                                                                                                                                            |
| `--db-path` | String | `:memory:` | Path to local DuckDB database file, MotherDuck database (`md:`), or S3 URL (e.g., `s3://bucket/path/to/db.duckdb`)                                                                                                                                                     |
| `--motherduck-token` | String | `None` | Access token to use for MotherDuck database connections (uses `motherduck_token` env var by default)                                                                                                                                                           |
| `--home-dir` | String | `None` | Home directory for DuckDB (uses `HOME` env var by default)                                                                                                                                                                                                     |
| `--read-write` | Flag | `False` | Enable write access to the database. By default, the server runs in read-only mode for local DuckDB files and MotherDuck.                                                                   |
| `--saas-mode` | Flag | `False` | **For MotherDuck:** Enable [SaaS mode](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-saas-mode) which disables local filesystem access for enhanced security. |
| `--secure-mode` | Flag | `False` | **For local DuckDB:** Enable secure mode which disables local filesystem access, community extensions, and locks configuration. See [DuckDB security docs](https://duckdb.org/docs/stable/operations_manual/securing_duckdb/overview). |
| `--init-sql` | String | `None` | SQL file path or SQL string to execute on startup for database initialization.                                                                                                                                                          |
| `--ephemeral-connections` | Flag | `True` | Use temporary connections for read-only local DuckDB files, creating a new connection for each query. This keeps the file unlocked so other processes can write to it.                                                  |
| `--allow-switch-databases` | Flag | `False` | Enable the `switch_database_connection` tool to change databases at runtime. Disabled by default.                                                                                                          |
| `--enable-list-databases` | Flag | `False` | Enable the `list_databases` tool. Auto-enabled for MotherDuck connections, disabled by default for local DuckDB.                                                                                                          |
| `--max-rows` | Integer | `1024` | Maximum number of rows to return from queries.                                                                                                                                                                    |
| `--max-chars` | Integer | `50000` | Maximum number of characters in query results.                                                                                                                                                          |
| `--query-timeout` | Integer | `-1` | Query execution timeout in seconds. Set to -1 to disable timeout (default).                                                                                                                                                          |

### Configuration Examples

**Local DuckDB (read-only, default):**
```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "/path/to/local.db"]
    }
  }
}
```

**Local DuckDB (dev mode with write access and database switching):**
```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "/path/to/local.db", "--read-write", "--allow-switch-databases"]
    }
  }
}
```

**MotherDuck (production with SaaS mode and HTTP transport):**
```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "md:", "--saas-mode", "--transport", "http", "--port", "8000"],
      "env": {
        "motherduck_token": "<YOUR_READ_SCALING_TOKEN>"
      }
    }
  }
}
```

## Getting Started

### General Prerequisites

- `uv` installed, you can install it using `pip install uv` or `brew install uv`

If you plan to use the MCP with Claude Desktop or any other MCP comptabile client, the client need to be installed.

### Prerequisites for DuckDB

- No prerequisites. The MCP server can create an in-memory database on-the-fly
- Or connect to an existing local DuckDB database file, or one stored on remote object storage (e.g., AWS S3).

See [Connect to local DuckDB](#connect-to-local-duckdb).

### Prerequisites for MotherDuck

- Sign up for a [MotherDuck account](https://app.motherduck.com/?auth_flow=signup)
- Generate an access token via the [MotherDuck UI](https://app.motherduck.com/settings/tokens?auth_flow=signup)
- Store the token securely for use in the configuration

### Usage with Cursor

1. Install Cursor from [cursor.com/downloads](https://www.cursor.com/downloads) if you haven't already

2. Open Cursor:

- To set it up globally for the first time, go to Settings->MCP and click on "+ Add new global MCP server".
- This will open a `mcp.json` file to which you add the following configuration:

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "md:"],
      "env": {
        "motherduck_token": "<YOUR_MOTHERDUCK_TOKEN>"
      }
    }
  }
}
```

### Usage with VS Code

[![Install with UV in VS Code](https://img.shields.io/badge/VS_Code-Install_with_UV-0098FF?style=plastic)](https://insiders.vscode.dev/redirect/mcp/install?name=mcp-server-motherduck&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-motherduck%22%2C%22--db-path%22%2C%22md%3A%22%2C%22--motherduck-token%22%2C%22%24%7Binput%3Amotherduck_token%7D%22%5D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22motherduck_token%22%2C%22description%22%3A%22MotherDuck+Token%22%2C%22password%22%3Atrue%7D%5D) [![Install with UV in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_with_UV-24bfa5?style=plastic&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=mcp-server-motherduck&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-motherduck%22%2C%22--db-path%22%2C%22md%3A%22%2C%22--motherduck-token%22%2C%22%24%7Binput%3Amotherduck_token%7D%22%5D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22motherduck_token%22%2C%22description%22%3A%22MotherDuck+Token%22%2C%22password%22%3Atrue%7D%5D&quality=insiders)

For the quickest installation, click one of the "Install with UV" buttons at the top.

#### Manual Installation

Add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` and typing `Preferences: Open User Settings (JSON)`.

```json
{
  "mcp": {
    "inputs": [
      {
        "type": "promptString",
        "id": "motherduck_token",
        "description": "MotherDuck Token",
        "password": true
      }
    ],
    "servers": {
      "motherduck": {
        "command": "uvx",
        "args": ["mcp-server-motherduck", "--db-path", "md:"],
        "env": {
          "motherduck_token": "${input:motherduck_token}"
        }
      }
    }
  }
}
```

Optionally, you can add it to a file called `.vscode/mcp.json` in your workspace. This will allow you to share the configuration with others.

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "motherduck_token",
      "description": "MotherDuck Token",
      "password": true
    }
  ],
  "servers": {
    "motherduck": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "md:"],
      "env": {
        "motherduck_token": "${input:motherduck_token}"
      }
    }
  }
}
```

### Usage with Claude Desktop

1. Install Claude Desktop from [claude.ai/download](https://claude.ai/download) if you haven't already

2. Open the Claude Desktop configuration file:

- To quickly access it or create it the first time, open the Claude Desktop app, select Settings, and click on the "Developer" tab, finally click on the "Edit Config" button.
- Add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "md:"],
      "env": {
        "motherduck_token": "<YOUR_MOTHERDUCK_TOKEN>"
      }
    }
  }
}
```

### Usage with Claude Code

Claude Code supports MCP servers through CLI commands or JSON configuration. Here are two ways to set it up:

#### Option 1: Using CLI Commands

Add the MotherDuck MCP server directly using the Claude Code CLI:

```bash
claude mcp add mcp-server-motherduck uvx mcp-server-motherduck -- --db-path md: -e motherduck_token=<YOUR_MOTHERDUCK_TOKEN>
```

#### Option 2: Using JSON Configuration

Add the server using a JSON configuration:

```bash
claude mcp add-json mcp-server-motherduck '{
  "command": "uvx",
  "args": ["mcp-server-motherduck", "--db-path", "md:"],
  "env": {
    "motherduck_token": "<YOUR_MOTHERDUCK_TOKEN>"
  }
}'
```

**Scoping Options**:
- Use `--local` (default) for project-specific configuration
- Use `--project` to share the configuration with your team via `.mcp.json`
- Use `--user` to make the server available across all your projects

## Read-Only Mode

By default, the server runs in **read-only mode** to prevent AI agents from accidentally modifying your data. This is a safety feature, not a security feature—it protects against well-meaning agents making unintended changes.

- Use `--read-write` only when you explicitly want agents to create tables, insert data, etc.
- Switching databases is also disabled by default; to enable it, use `--allow-switch-databases`

## Securing your MCP Server for Production

**Important**: Read-only mode alone is not sufficient for production security. The only secure configuration for production is to use **MotherDuck with SaaS mode and read-scaling tokens**. Without SaaS mode, the server can access local files on the host machine.

**Read Scaling Tokens** are special access tokens that enable scalable read operations by allowing up to 4 concurrent read replicas, improving performance for multiple end users while *restricting write capabilities*.
Refer to the [Read Scaling documentation](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/read-scaling/#creating-a-read-scaling-token) to learn how to create a read-scaling token.

**SaaS Mode** in MotherDuck enhances security by restricting access to local files, databases, extensions, and configurations, making it ideal for third-party tools that require stricter environment protection. Learn more about it in the [SaaS Mode documentation](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-saas-mode).

**Production Configuration**

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", "md:", "--saas-mode"],
      "env": {
        "motherduck_token": "<YOUR_READ_SCALING_TOKEN>"
      }
    }
  }
}
```

## Connect to local DuckDB

To connect to a local DuckDB, instead of using the MotherDuck token, specify the path to your local DuckDB database file or use `:memory:` for an in-memory database.

In-memory database (requires `--read-write` since data doesn't persist):

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
        "--db-path",
        ":memory:",
        "--read-write"
      ]
    }
  }
}
```

Local DuckDB file:

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
        "--db-path",
        "/path/to/your/local.db"
      ]
    }
  }
}
```

Local DuckDB file in [readonly mode](https://duckdb.org/docs/stable/connect/concurrency.html):

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
        "--db-path",
        "/path/to/your/local.db"
      ]
    }
  }
}
```

**Note**:Read-only mode for local file-backed DuckDB connections also makes use of
short-lived connections. Each time the query MCP tool is used, a temporary
read-only connection is created, the query is executed, and the connection is closed. This
feature was motivated by a workflow where [DBT](https://www.getdbt.com) was used for
modeling data within DuckDB and then an MCP client (Windsurf/Cline/Claude/Cursor)
was used for exploring the database. The short-lived connections allow each tool
to run and then release their connection, allowing the next tool to connect.

To disable this and use a persistent connection, use `--no-ephemeral-connections`.

## Connect to DuckDB on S3

You can connect to DuckDB databases stored on Amazon S3 by providing an S3 URL as the database path. The server will automatically configure the necessary S3 credentials from your environment variables.

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
        "--db-path",
        "s3://your-bucket/path/to/database.duckdb"
      ],
      "env": {
        "AWS_ACCESS_KEY_ID": "<your_key>",
        "AWS_SECRET_ACCESS_KEY": "<your_secret>",
        "AWS_DEFAULT_REGION": "<your_region>"
      }
    }
  }
}
```


**Note**: For S3 connections:
- AWS credentials must be provided via environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_DEFAULT_REGION`)
- For temporary credentials (AWS SSO), set the `AWS_SESSION_TOKEN` environment variable (and optionally `AWS_DEFAULT_REGION`) to automatically use DuckDB's `credential_chain` provider.
- The S3 database is attached to an in-memory DuckDB instance
- The httpfs extension is automatically installed and configured for S3 access
- Both read and write operations are supported

## Example Queries

Once configured, you can e.g. ask Claude to run queries like:

- "Create a new database and table in MotherDuck"
- "Query data from my local CSV file"
- "Join data from my local DuckDB database with a table in MotherDuck"
- "Analyze data stored in Amazon S3"

## Troubleshooting

- If you encounter connection issues, verify your MotherDuck token is correct
- For local file access problems, ensure the `--home-dir` parameter is set correctly
- Check that the `uvx` command is available in your PATH
- If you encounter [`spawn uvx ENOENT`](https://github.com/motherduckdb/mcp-server-motherduck/issues/6) errors, try specifying the full path to `uvx` (output of `which uvx`)

## Development configuration

To run the server from a local development environment, use the following configuration:

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "uv",
      "args": ["--directory", "/path/to/your/local/mcp-server-motherduck", "run", "mcp-server-motherduck", "--db-path", "md:"],
      "env": {
        "motherduck_token": "<YOUR_MOTHERDUCK_TOKEN>"
      }
    }
  }
}
```

## Release process

This repo uses a GitHub Actions workflow to bump, tag, publish, and create a release.

1. Use the Github action `Release New Version`
2. Enter the new version in `MAJOR.MINOR.PATCH` format (for example: `0.8.1`)
3. Run the workflow

The workflow will update all versioned files, commit and tag `vX.Y.Z`, publish to PyPI and the MCP registry, then create the GitHub release.

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.

##
mcp-name: io.github.motherduckdb/mcp-server-motherduck
