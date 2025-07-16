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
uvx mcp-server-motherduck --transport stream --db-path /path/to/local.db --read-only

# Connect to MotherDuck with token with stream transport mode
uvx mcp-server-motherduck --transport stream --db-path md: --motherduck-token YOUR_TOKEN

# Connect to local DuckDB file in read-only mode with stream transport mode
uvx mcp-server-motherduck --transport stream --db-path /path/to/local.db --read-only

# Connect to MotherDuck in SaaS mode for enhanced security with stream transport mode
uvx mcp-server-motherduck --transport stream --db-path md: --motherduck-token YOUR_TOKEN --saas-mode
```

## Getting Started

### General Prerequisites

- `uv` installed, you can install it using `pip install uv` or `brew install uv`

If you plan to use the MCP with Claude Desktop or any other MCP comptabile client, the client need to be installed.

### Prerequisites for DuckDB

- No prerequisites. The MCP server can create an in-memory database on-the-fly
- Or connect to an existing local DuckDB database file , or one stored on remote object storage (e.g., AWS S3).

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
  "servers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
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
        "args": [
          "mcp-server-motherduck",
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
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
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
  "servers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
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

## Securing your MCP Server when querying MotherDuck

If the MCP server is exposed to third parties and should only have read access to data, we recommend using a read scaling token and running the MCP server in SaaS mode.

**Read Scaling Tokens** are special access tokens that enable scalable read operations by allowing up to 4 concurrent read replicas, improving performance for multiple end users while *restricting write capabilities*.
Refer to the [Read Scaling documentation](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/read-scaling/#creating-a-read-scaling-token) to learn how to create a read-scaling token.

**SaaS Mode** in MotherDuck enhances security by restricting it's access to local files, databases, extensions, and configurations, making it ideal for third-party tools that require stricter environment protection. Learn more about it in the [SaaS Mode documentation](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-saas-mode).

**Secure Configuration**

```json
{
  "servers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
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
  "servers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
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
  "servers": {
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
  "servers": {
    "mcp-server-motherduck": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
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
reaodnly connection is created + query is executed + connection is closed. This
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

The server can run in SSE mode in two ways:

### Direct SSE mode

Run the server directly in SSE mode using the `--transport sse` flag:

```bash
uvx mcp-server-motherduck --transport sse --port 8000 --db-path md: --motherduck-token <your_motherduck_token>
```

This will start the server listening on the specified port (default 8000) and you can point your clients directly to this endpoint.

### Using supergateway

Alternatively, you can run SSE mode using `supergateway`:

```bash
npx -y supergateway --stdio "uvx mcp-server-motherduck --db-path md: --motherduck-token <your_motherduck_token>"
```

Both methods allow you to point your clients such as Claude Desktop, Cursor to the SSE endpoint.

## Development configuration

To run the server from a local development environment, use the following configuration:

```json
 {
  "servers": {
    "mcp-server-motherduck": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/local/mcp-server-motherduck",
        "run",
        "mcp-server-motherduck",
        "--db-path",
        "md:",
        "--motherduck-token",
        "<YOUR_MOTHERDUCK_TOKEN_HERE>"
      ]
    }
  }
}
```

## Troubleshooting

- If you encounter connection issues, verify your MotherDuck token is correct
- For local file access problems, ensure the `--home-dir` parameter is set correctly
- Check that the `uvx` command is available in your PATH
- If you encounter [`spawn uvx ENOENT`](https://github.com/motherduckdb/mcp-server-motherduck/issues/6) errors, try specifying the full path to `uvx` (output of `which uvx`)
- In version previous for v0.4.0 we used environment variables, now we use parameters

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
