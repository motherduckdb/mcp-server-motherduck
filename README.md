# USITC Tariff Data MCP Server

A comprehensive MCP (Model Context Protocol) server implementation for accessing and analyzing United States International Trade Commission (USITC) tariff data. This project provides both automated data collection and powerful MCP server capabilities for querying tariff information through AI assistants and IDEs.

## 🎯 Overview

This project combines two powerful components:

1. **USITC Tariff Data Downloader**: Automatically downloads, extracts, and loads 11 years of US tariff data into a DuckDB database
2. **Unified MCP Server**: Provides specialized tariff analysis tools and SQL capabilities through MCP clients like Claude, Cursor, and VS Code

## ✨ Features

- **Automated Data Collection**: Downloads and processes 11 years of USITC tariff data (2015-2025)
- **DuckDB Integration**: High-performance analytics database with 142K+ rows of tariff information
- **Unified MCP Server**: Query tariff data through AI assistants using natural language
- **Specialized Tariff Tools**: Purpose-built tools for tariff analysis, comparison, and HTS code lookup
- **Plugin Architecture**: Modular design with tariff-specific functionality
- **Local & Cloud Support**: Works with local DuckDB files or MotherDuck cloud databases

## 📁 Project Structure

```
mcp-tarrifs/
├── scripts/                    # Server launcher and utilities
│   └── mcp_server_launcher.py  # MCP-compatible server launcher
├── src/
│   ├── mcp_server/             # Unified MCP server implementation
│   │   ├── core/               # Core server components and configuration
│   │   ├── plugins/            # Dataset-specific plugins
│   │   │   └── tariffs/        # Tariff-specific tools and analysis
│   │   ├── server.py           # Main server implementation
│   │   └── __main__.py         # Entry point for MCP server
│   └── tariffs_db/             # Database build tools for tariff data
├── data/                       # Downloaded and processed tariff data
│   └── usitc_data/
├── logs/                       # Query and request logs
├── start_enhanced_server.py    # Legacy server starter (for development)
├── pyproject.toml             # Project dependencies and configuration
├── MCP_CLIENT_CONFIG.md       # MCP client configuration guide
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- `uv` package manager (install with `pip install uv` or `brew install uv`)

### Option 1: Complete Setup (Recommended for MCP Clients)

Build the database and configure for MCP clients:

```bash
# Clone the repository
git clone <repository-url>
cd mcp-tarrifs

# Install dependencies
uv sync

# Build database (one-time setup)
python scripts/mcp_server_launcher.py --build-only

# Get MCP client configuration
cat MCP_CLIENT_CONFIG.md
```

This will:
- Download 11 years of USITC tariff data (2015-2025)
- Extract and load data into DuckDB
- Provide ready-to-use configuration for MCP clients

⚠️ **Important**: For MCP clients, use the configurations in `MCP_CLIENT_CONFIG.md`, not the interactive scripts below.

### Option 2: Interactive Development Mode

For development and testing:

```bash
# Build database and start interactive server
python scripts/mcp_server_launcher.py

# Or use the enhanced development server
python start_enhanced_server.py
```

### Option 3: Manual Database Building

If you need to rebuild or customize the database:

```bash
# Build database with specific options
uv run python src/tariffs_db/db_build.py --all --years 11

# Or build for specific years
uv run python src/tariffs_db/db_build.py --years 5  # Last 5 years only
```

## 📊 Database Contents

The processed database contains 10 tables with comprehensive tariff information:

- **155,000+ rows** of tariff data across 11 years (2015-2025)
- **Harmonized System (HS) codes** and descriptions
- **Tariff rates** (General, Special, Column 2)
- **Trade statistics** and classifications
- **Annual snapshots** for trend analysis

### Sample Table Structure

Each year's data includes columns like:
- `hts8`: 8-digit Harmonized Tariff Schedule codes
- `brief_description`: Product description
- `mfn_text_rate`: Most Favored Nation tariff rate
- `general_rate_of_duty`: Standard tariff rate
- `special_rate_of_duty`: Preferential rates
- `column_2_rate_of_duty`: Alternative duty rates
- `units_of_quantity`: Measurement units
- `country`: Country-specific information

## 🧩 Plugin Architecture

The server features a modular plugin system for specialized functionality:

### Tariff Plugin Features

- **Smart Product Search**: Search by HTS codes or natural language descriptions
- **Multi-year Comparisons**: Track tariff rate changes over time
- **Country-specific Analysis**: Filter and compare rates by trading partner
- **HTS Code Intelligence**: Understand product classification hierarchy
- **Guided Analysis**: Built-in prompts for common tariff analysis patterns

### Available Analysis Tools

```python
# Example tool usage through MCP clients
get_tariff_rates(
    product_search="automobiles",
    country="china", 
    year=2024
)

compare_tariff_rates(
    product_code="8703.23.00",
    years=[2020, 2021, 2022, 2023, 2024]
)
```

## 🛠️ Available Scripts

### `scripts/mcp_server_launcher.py`

**Purpose**: MCP-compatible server launcher with automated database setup

**Features**:
- Automatic database building if needed
- MCP STDIO-compatible output
- DuckDB query logging setup
- Read-only server mode by default
- Creates and manages logs directory

**Usage**:
```bash
# Build database and start MCP server (STDIO mode)
python scripts/mcp_server_launcher.py

# Only build database, don't start server
python scripts/mcp_server_launcher.py --build-only

# Disable automatic logging setup
python scripts/mcp_server_launcher.py --no-logging
```

**Output**:
- Database at: `data/usitc_data/usitc_trade_data.db`
- Logs at: `logs/queries.log` and `logs/mcp_requests.log`
- STDIO transport for MCP client communication

### `start_enhanced_server.py`

**Purpose**: Development server with enhanced logging and HTTP mode

**Features**:
- HTTP server mode for web clients
- Enhanced request logging
- Development-friendly output
- Status monitoring

**Usage**:
```bash
# Start development server
python start_enhanced_server.py
```

**Note**: This script is for development only. Use `mcp_server_launcher.py` for MCP clients.

## 🔧 MCP Server Tools

The unified MCP server provides both core database tools and specialized tariff analysis capabilities:

### Core Database Tools

- **`list_tables`**: Show all available tariff tables
- **`get_schema`**: Get column information for tables
- **`get_sample_data`**: Preview table contents
- **`query`**: Execute SQL queries on tariff data

### Specialized Tariff Tools

- **`get_tariff_rates`**: Get tariff rates for specific products by HTS code or description search
  - Search by HTS code (e.g., `'0101.21.00'`)
  - Search by product description (e.g., `'horses'`, `'automobiles'`)
  - Filter by country and year
  
- **`compare_tariff_rates`**: Compare tariff rates across years or for different products
  - Compare specific HTS codes across multiple years
  - Analyze rate changes over time
  - Compare rates for different countries

### Tariff Analysis Prompts

- **`tariff-analysis-guide`**: Comprehensive guide for analyzing tariff data and understanding trade patterns
- **`hts-code-lookup`**: Help with HTS (Harmonized Tariff Schedule) code lookups and product classification

### Example Queries

Once the server is running, you can ask AI assistants questions like:

- "Show me the tariff rates for steel products in 2024"
- "Compare tariff rates between 2015 and 2024 for electronics"
- "What are the most common tariff rates for agricultural products?"
- "Find all products with special duty rates"
- "Get tariff rates for HTS code 8703.23.00 across all years"
- "Search for tariff rates on textile products"

## 💻 Integration with MCP Clients

⚠️ **Important**: Use the configurations in `MCP_CLIENT_CONFIG.md` for proper MCP client setup.

The server uses STDIO transport for direct integration with MCP clients. **Do not use the development scripts** (`start_enhanced_server.py`) with MCP clients.

### Quick Configuration Summary

For MCP clients, use this pattern:

```json
{
  "command": "uv",
  "args": [
    "run",
    "--project", "/path/to/mcp-tarrifs",
    "python", "-m", "mcp_server",
    "--db-path", "/path/to/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
    "--read-only"
  ]
}
```

### Supported Clients

- **Claude Desktop**: Full configuration in `MCP_CLIENT_CONFIG.md`
- **Cursor/VS Code**: MCP extension configuration included
- **Perplexity**: JSON configuration provided
- **Other MCP clients**: Use the STDIO transport pattern above

### Configuration Files

- `MCP_CLIENT_CONFIG.md`: Complete setup instructions for all major MCP clients
- Includes copy-paste ready configurations
- Contains troubleshooting for common issues

## 🗂️ Data Sources

This project uses official USITC (United States International Trade Commission) tariff data:

- **Source**: [USITC DataWeb](https://dataweb.usitc.gov/)
- **Coverage**: 2015-2025 (11 years)
- **Format**: Annual tariff databases in Excel and text formats
- **Update Frequency**: Updated when new annual data is released

## 🔍 Development

### Project Components

1. **Unified MCP Server** (`src/mcp_server/`):
   - Plugin-based architecture for modular functionality
   - Core database operations and SQL query capabilities
   - Specialized tariff analysis tools and prompts

2. **Tariff Plugin** (`src/mcp_server/plugins/tariffs/`):
   - Tariff-specific tools (`get_tariff_rates`, `compare_tariff_rates`)
   - HTS code analysis and product search capabilities
   - Guided prompts for tariff analysis

3. **Database Build Tools** (`src/tariffs_db/`):
   - USITC data download and processing utilities
   - Database schema creation and data loading
   - Data validation and cleanup tools

4. **Core Configuration** (`src/mcp_server/core/`):
   - Server configuration and logging setup
   - Database client management
   - Reusable components for plugins

### Plugin Architecture

The server uses a plugin system for dataset-specific functionality:

```python
# Example plugin structure
class TariffsPlugin(DatasetPlugin):
    def get_specialized_tools(self) -> list[types.Tool]:
        # Return tariff-specific tools
    
    def get_prompts(self) -> list[types.Prompt]:
        # Return analysis guidance prompts
    
    async def handle_tool_call(self, name: str, arguments: dict, db_client):
        # Handle tool execution
```

### Running Tests

```bash
# Test server functionality (requires database)
uv run python -m pytest tests/

# Test basic server startup
python scripts/mcp_server_launcher.py --build-only

# Test with development server
python start_enhanced_server.py
```

### Rebuilding Database

To rebuild the database from scratch:

```bash
# Remove existing database
rm data/usitc_data/usitc_trade_data.db

# Rebuild with full dataset
python scripts/mcp_server_launcher.py --build-only

# Or rebuild manually with options
uv run python src/tariffs_db/db_build.py --all --years 11
```

## 📈 Performance

- **Database Size**: ~55MB for 11 years of data
- **Query Performance**: Sub-second response for most queries
- **Memory Usage**: Minimal - DuckDB is highly efficient
- **Concurrent Access**: Read-only mode supports multiple connections

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both scripts
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**"Database not found"**: Run `python scripts/mcp_server_launcher.py --build-only` to build the database

**"Server not responding in MCP client"**: 
- Check that you're using the configuration from `MCP_CLIENT_CONFIG.md`
- Ensure the database path is correct in your MCP client configuration
- Don't use `start_enhanced_server.py` with MCP clients

**"Permission denied"**: Ensure you have write access to the `data/` and `logs/` directories

**"Module not found"**: Run `uv sync` to install dependencies

**"MCP client can't connect"**:
- Verify the server command in your MCP client configuration
- Check that the database file exists at the specified path
- Use absolute paths in MCP client configurations

### Getting Help

1. Check the server startup logs when running `mcp_server_launcher.py`
2. Review configurations in `MCP_CLIENT_CONFIG.md`
3. Ensure all dependencies are installed with `uv sync`
4. Check that the database file exists at `data/usitc_data/usitc_trade_data.db`
5. For MCP client issues, verify STDIO transport is working correctly

### Development vs Production

- **For MCP Clients**: Use `scripts/mcp_server_launcher.py` with configurations from `MCP_CLIENT_CONFIG.md`
- **For Development**: Use `start_enhanced_server.py` for HTTP mode and enhanced logging
- **For Testing**: Both scripts support the same database but have different transport modes

---

**🎉 Happy Analyzing!** This project brings 11 years of US tariff data to your fingertips through the power of MCP and AI assistants.
