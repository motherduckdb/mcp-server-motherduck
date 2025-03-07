# mcp-server-motherduck MCP server
[![smithery badge](https://smithery.ai/badge/mcp-server-motherduck)](https://smithery.ai/server/mcp-server-motherduck)

An [MCP server](https://modelcontextprotocol.io/introduction) for MotherDuck and local DuckDB.

## Components

### Prompts

The server provides one prompt:

- duckdb-motherduck-prompt: A prompt to initialize a connection to duckdb or motherduck and start working with it

### Tools

The server offers one tool:

- query: Execute a query on the MotherDuck (DuckDB) database
  - Takes "query" as required string arguments

This is because all the interactions with both the DuckDB and MotherDuck are done through writing SQL queries.

## Usage with Claude Desktop

Add the snippet below to your Claude Desktop config and make sure to set the HOME var to your home folder (needed by DuckDB).

When using MotherDuck, you also need to set a [MotherDuck token](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#storing-the-access-token-as-an-environment-variable) env var.

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

### Servers Configuration

```
"mcpServers": {
  "mcp-server-motherduck": {
    "command": "uvx",
    "args": [
      "mcp-server-motherduck"
    ],
    "env": {
      "motherduck_token": "<your-motherduck-token>",
      "HOME": "<your-home-folder-for-project-files>"
    }
  }
}
```

### Installing via Smithery

To install MotherDuck for Claude Desktop automatically via [Smithery](https://smithery.ai/server/mcp-server-motherduck):

```bash
npx -y @smithery/cli install mcp-server-motherduck --client claude
```

### Installing Manually
## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
