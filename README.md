# MotherDuck MCP Server

An MCP server implementation that integrates MotherDuck and local DuckDB, providing SQL analytics capabilities to Claude.

## Features

- **Hybrid execution**: query data from both cloud-based MotherDuck and local DuckDB
- **Cloud storage integration**: access data stored in Amazon S3 or other cloud storage thanks to MotherDuck's integrations
- **Data sharing**: create and share databases
- **SQL analytics**: use DuckDB's SQL dialect to query any size of data directly from Claude
- **Serverless architecture**: run analytics without needing to configure instances or clusters

<a href="https://glama.ai/mcp/servers/15mdwrzibz"><img width="380" height="200" src="https://glama.ai/mcp/servers/15mdwrzibz/badge" alt="mcp-server-motherduck MCP server" /></a>

## Components

### Prompts

The server provides one prompt:

- `duckdb-motherduck-initial-prompt`: A prompt to initialize a connection to DuckDB or MotherDuck and start working with it

### Tools

The server offers one tool:

- `query`: Execute a SQL query on the MotherDuck/DuckDB database
  - **Inputs**:
    - `query` (string, required): The SQL query to execute

All interactions with both DuckDB and MotherDuck are done through writing SQL queries.

## Getting Started

### Prerequisites

- A MotherDuck account (sign up at [motherduck.com](https://motherduck.com))
- A MotherDuck access token
- `uv` installed, you can install it using `pip install uv` or `brew install uv`

If you plan to use MotherDuck MCP with Claude Desktop, you will also need Claude Desktop installed.

### Setting up your MotherDuck token

1. Sign up for a [MotherDuck account](https://app.motherduck.com/?auth_flow=signup)
2. Generate an access token via the [MotherDuck UI](https://app.motherduck.com/settings/tokens?auth_flow=signup)
3. Store the token securely for use in the configuration

### Usage with Claude Desktop

1. Install Claude Desktop from [claude.ai/download](https://claude.ai/download) if you haven't already

2. Open the Claude Desktop configuration file:

- To quickly access it or create it the first time, open the Claude Desktop app, select Settings, and click on the "Developer" tab, finally click on the "Edit Config" button.
- Add the following configuration to your `claude_desktop_config.json`:

```json
"mcpServers": {
  "mcp-server-motherduck": {
    "command": "uvx",
    "args": [
      "mcp-server-motherduck",
      "--db-path",
      "md:",
      "--motherduck-token",
      "<YOUR_MOTHERDUCK_TOKEN_HERE>",
    ],
  }
}
```

**Important Notes**:

- Replace `YOUR_MOTHERDUCK_TOKEN_HERE` with your actual MotherDuck token
- Replace `YOUR_HOME_FOLDER_PATH` with the path to your home directory (needed by DuckDB for file operations). For example, on macOS, it would be `/Users/your_username`
- The `HOME` environment variable is required for DuckDB to function properly.

## Example Queries

Once configured, you can ask Claude to run queries like:

- "Create a new database and table in MotherDuck"
- "Query data from my local CSV file"
- "Join data from my local DuckDB database with a table in MotherDuck"
- "Analyze data stored in Amazon S3"

## Testing

The server is designed to be run by tools like Claude Desktop and Cursor, but you can start it manually for testing purposes. When testing the server manually, you can specify which database to connect to using the `--db-path` parameter:

1. **Default MotherDuck database**:

   - To connect to the default MotherDuck database, you will need to pass the auth token using the `--motherduck-token` parameter.

   ```bash
   uvx mcp-server-motherduck --db-path md: --motherduck-token <your_motherduck_token>
   ```

2. **Specific MotherDuck database**:

   ```bash
   uvx mcp-server-motherduck --db-path md:your_database_name --motherduck-token <your_motherduck_token>
   ```

3. **Local DuckDB database**:

   ```bash
   uvx mcp-server-motherduck --db-path /path/to/your/local.db
   ```

4. **In-memory database**:

   ```bash
   uvx mcp-server-motherduck --db-path :memory:
   ```

If you don't specify a database path but have set the `motherduck_token` environment variable, the server will automatically connect to the default MotherDuck database (`md:`).

## Running in SSE mode

The server could also be run ing SSE mode using `supergateway` by running the following command:

```bash
npx -y supergateway --stdio "uvx mcp-server-motherduck --db-path md: --motherduck-token <your_motherduck_token>"
```

And you can point your clients such as Claude Desktop, Cursor to this endpoint.

## Troubleshooting

- If you encounter connection issues, verify your MotherDuck token is correct
- For local file access problems, ensure the `--home-dir` parameter is set correctly
- Check that the `uvx` command is available in your PATH
- In version previous for v0.4.0 we used environment variables, now we use parameters

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.