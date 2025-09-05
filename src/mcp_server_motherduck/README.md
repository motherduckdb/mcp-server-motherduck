# MotherDuck's DuckDB MCP Server

An MCP server implementation that interacts with DuckDB and MotherDuck databases, providing SQL analytics capabilities to AI Assistants and IDEs.

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=DuckDB&config=eyJjb21tYW5kIjoidXZ4IG1jcC1zZXJ2ZXItbW90aGVyZHVjayAtLWRiLXBhdGggbWQ6IiwiZW52Ijp7Im1vdGhlcmR1Y2tfdG9rZW4iOiIifX0%3D)

## Resources
- [Close the Loop: Faster Data Pipelines with MCP, DuckDB & AI (Blogpost)](https://motherduck.com/blog/faster-data-pipelines-with-mcp-duckdb-ai/)
- [Faster Data Pipelines development with MCP and DuckDB (YouTube)](https://www.youtube.com/watch?v=yG1mv8ZRxcU)

## Features

- **Hybrid execution**: query data from local DuckDB or/and cloud-based MotherDuck databases
- **Cloud storage integration**: access data stored in Amazon S3 or other cloud storage thanks to MotherDuck's integrations
- **Data sharing**: create and share databases
- **SQL analytics**: use DuckDB's SQL dialect to query any size of data directly from your AI Assistant or IDE
- **Serverless architecture**: run analytics without needing to configure instances or clusters

## Components

### Prompts

The server provides one prompt:

- `duckdb-motherduck-initial-prompt`: A prompt to initialize a connection to DuckDB or MotherDuck and start working with it

### Tools

The server offers one tool:

- `query`: Execute a SQL query on the DuckDB or MotherDuck database
  - **Inputs**:
    - `query` (string, required): The SQL query to execute

All interactions with both DuckDB and MotherDuck are done through writing SQL queries.

## Command Line Parameters

The MCP server supports the following parameters:

| Parameter | Type | Default | Description                                                                                                                                                                                                                                                    |
|-----------|------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--transport` | Choice | `stdio` | Transport type. Options: `stdio`, `sse`, `stream`                                                                                                                                                                                                              |
| `--port` | Integer | `8000` | Port to listen on for sse and stream transport mode                                                                                                                                                                                                            |
| `--db-path` | String | `md:` | Path to local DuckDB database file or MotherDuck database                                                                                                                                                                                                      |
| `--motherduck-token` | String | `None` | Access token to use for MotherDuck database connections (uses `motherduck_token` env var by default)                                                                                                                                                           |
| `--read-only` | Flag | `False` | Flag for connecting to DuckDB or MotherDuck in read-only mode. For DuckDB it uses short-lived connections to enable concurrent access                                                                                                                          |
| `--home-dir` | String | `None` | Home directory for DuckDB (uses `HOME` env var by default)                                                                                                                                                                                                     |
| `--saas-mode` | Flag | `False` | Flag for connecting to MotherDuck in [SaaS mode](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-saas-mode). (disables filesystem and write permissions for local DuckDB) |
| `--json-response` | Flag | `False` | Enable JSON responses for HTTP stream. Only supported for `stream` transport                                                                                                                                                                                   |

### Quick Usage Examples

```bash
# Connect to local DuckDB file in read-only mode with stream transport mode
python -m mcp_server_motherduck.server --transport stream --db-path /path/to/local.db --read-only

# Connect to MotherDuck with token with stream transport mode
python -m mcp_server_motherduck.server --transport stream --db-path md: --motherduck-token YOUR_TOKEN

# Connect to MotherDuck in SaaS mode for enhanced security with stream transport mode
python -m mcp_server_motherduck.server --transport stream --db-path md: --motherduck-token YOUR_TOKEN --saas-mode
```

## Getting Started

### General Prerequisites

- Python 3.8 or higher
- Required Python packages (install via `pip install -r requirements.txt`)

If you plan to use the MCP with Claude Desktop or any other MCP compatible client, the client needs to be installed.

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
      "command": "python",
      "args": [
        "-m",
        "mcp_server_motherduck.server",
        "--db-path",
        "md:",
        "--motherduck-token",
        "<YOUR_MOTHERDUCK_TOKEN_HERE>"
      ]
    }
  }
}
```

### Usage with VS Code

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
        "command": "python",
        "args": [
          "-m",
          "mcp_server_motherduck.server",
          "--db-path",
          "md:",
          "--motherduck-token",
          "${input:motherduck_token}"
        ]
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
      "command": "python",
      "args": [
        "-m",
        "mcp_server_motherduck.server",
        "--db-path",
        "md:",
        "--motherduck-token",
        "${input:motherduck_token}"
      ]
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
      "command": "python",
      "args": [
        "-m",
        "mcp_server_motherduck.server",
        "--db-path",
        "md:",
        "--motherduck-token",
        "<YOUR_MOTHERDUCK_TOKEN_HERE>"
      ]
    }
  }
}
```

**Important Notes**:

- Replace `YOUR_MOTHERDUCK_TOKEN_HERE` with your actual MotherDuck token

### Usage with Claude Code

Claude Code supports MCP servers through CLI commands or JSON configuration. Here are two ways to set it up:

#### Option 1: Using CLI Commands

Add the MotherDuck MCP server directly using the Claude Code CLI:

```bash
claude mcp add mcp-server-motherduck python -m mcp_server_motherduck.server -- --db-path md: --motherduck-token <YOUR_MOTHERDUCK_TOKEN_HERE>
```

#### Option 2: Using JSON Configuration

Add the server using a JSON configuration:

```bash
claude mcp add-json mcp-server-motherduck '{
  "command": "python",
  "args": [
    "-m",
    "mcp_server_motherduck.server",
    "--db-path",
    "md:",
    "--motherduck-token",
    "<YOUR_MOTHERDUCK_TOKEN_HERE>"
  ]
}'
```

**Scoping Options**:
- Use `--local` (default) for project-specific configuration
- Use `--project` to share the configuration with your team via `.mcp.json`
- Use `--user` to make the server available across all your projects

**Important Notes**:
- Replace `YOUR_MOTHERDUCK_TOKEN_HERE` with your actual MotherDuck token
- Claude Code also supports environment variable expansion, so you can use `${MOTHERDUCK_TOKEN}` if you've set the environment variable

## Securing your MCP Server when querying MotherDuck

If the MCP server is exposed to third parties and should only have read access to data, we recommend using a read scaling token and running the MCP server in SaaS mode.

**Read Scaling Tokens** are special access tokens that enable scalable read operations by allowing up to 4 concurrent read replicas, improving performance for multiple end users while *restricting write capabilities*.
Refer to the [Read Scaling documentation](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/read-scaling/#creating-a-read-scaling-token) to learn how to create a read-scaling token.

**SaaS Mode** in MotherDuck enhances security by restricting its access to local files, databases, extensions, and configurations, making it ideal for third-party tools that require stricter environment protection. Learn more about it in the [SaaS Mode documentation](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-saas-mode).

**Secure Configuration**

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server_motherduck.server",
        "--db-path",
        "md:",
        "--motherduck-token",
        "<YOUR_READ_SCALING_TOKEN_HERE>",
        "--saas-mode"
      ]
    }
  }
}
```

## Connect to local DuckDB

To connect to a local DuckDB, instead of using the MotherDuck token, specify the path to your local DuckDB database file or use `:memory:` for an in-memory database.

In-memory database:

```json
{
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server_motherduck.server",
        "--db-path",
        ":memory:"
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
      "command": "python",
      "args": [
        "-m",
        "mcp_server_motherduck.server",
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
      "command": "python",
      "args": [
        "-m",
        "mcp_server_motherduck.server",
        "--db-path",
        "/path/to/your/local.db",
        "--read-only"
      ]
    }
  }
}
```

**Note**: readonly mode for local file-backed DuckDB connections also makes use of
short lived connections. Each time the query MCP tool is used a temporary,
readonly connection is created + query is executed + connection is closed. This
feature was motivated by a workflow where [DBT](https://www.getdbt.com) was for
modeling data within duckdb and then an MCP client (Windsurf/Cline/Claude/Cursor)
was used for exploring the database. The short lived connections allow each tool
to run and then release their connection, allowing the next tool to connect.

## Example Queries

Once configured, you can e.g. ask Claude to run queries like:

- "Create a new database and table in MotherDuck"
- "Query data from my local CSV file"
- "Join data from my local DuckDB database with a table in MotherDuck"
- "Analyze data stored in Amazon S3"

## Running in SSE mode

The server can run in SSE mode using the `--transport sse` flag:

```bash
python -m mcp_server_motherduck.server --transport sse --port 8000 --db-path md: --motherduck-token <your_motherduck_token>
```

This will start the server listening on the specified port (default 8000) and you can point your clients directly to this endpoint.

## Development configuration

To run the server from a local development environment, use the following configuration:

```json
 {
  "mcpServers": {
    "mcp-server-motherduck": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server_motherduck.server",
        "--db-path",
        "md:",
        "--motherduck-token",
        "<YOUR_MOTHERDUCK_TOKEN_HERE>"
      ],
      "cwd": "/path/to/your/local/mcp-tarrifs/src"
    }
  }
}
```

## Troubleshooting

- If you encounter connection issues, verify your MotherDuck token is correct
- For local file access problems, ensure the `--home-dir` parameter is set correctly
- Check that Python is available in your PATH
- Ensure all required dependencies are installed in your Python environment
- If you encounter module import errors, make sure you're running from the correct directory or using the proper Python path

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
