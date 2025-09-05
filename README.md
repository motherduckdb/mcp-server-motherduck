# USITC Tariff Data MCP Server

A comprehensive MCP (Model Context Protocol) server implementation for accessing and analyzing United States International Trade Commission (USITC) tariff data. This project provides both automated data collection and powerful MCP server capabilities for querying tariff information through AI assistants and IDEs.

## 🎯 Overview

This project combines two powerful components:

1. **USITC Tariff Data Downloader**: Automatically downloads, extracts, and loads 10 years of US tariff data into a DuckDB database
2. **MotherDuck MCP Server**: Provides SQL analytics capabilities through MCP clients like Claude, Cursor, and VS Code

## ✨ Features

- **Automated Data Collection**: Downloads and processes 10 years of USITC tariff data (2015-2024)
- **DuckDB Integration**: High-performance analytics database with 142K+ rows of tariff information
- **MCP Server**: Query tariff data through AI assistants using natural language
- **Enhanced Tools**: Specialized tools for tariff data exploration and analysis
- **Local & Cloud Support**: Works with local DuckDB files or MotherDuck cloud databases

## 📁 Project Structure

```
mcp-tarrifs/
├── scripts/                    # Main user scripts
│   ├── build_and_serve.py     # End-to-end setup and server startup
│   └── test_enhanced_client.py # Test MCP server functionality
├── src/
│   ├── mcp_server_motherduck/  # Core MCP server implementation
│   └── tariffs_mcp/           # Enhanced MCP server with tariff-specific tools
├── data/                       # Downloaded and processed tariff data
│   └── usitc_data/
├── pyproject.toml             # Project dependencies and configuration
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- `uv` package manager (install with `pip install uv` or `brew install uv`)

### Option 1: Complete Setup (Recommended)

Run the all-in-one script that downloads data and starts the MCP server:

```bash
# Clone the repository
git clone <repository-url>
cd mcp-tarrifs

# Install dependencies
uv sync

# Build database and start MCP server
python scripts/build_and_serve.py
```

This script will:
- Download 10 years of USITC tariff data (2015-2024)
- Extract and load data into DuckDB
- Start the MCP server on `http://127.0.0.1:8000/mcp`
- Provide a read-only interface to the tariff database

### Option 2: Test Existing Setup

If you already have the database built, test the MCP server functionality:

```bash
# Test the enhanced MCP server
python scripts/test_enhanced_client.py
```

## 📊 Database Contents

The processed database contains 10 tables with comprehensive tariff information:

- **142,000+ rows** of tariff data across 10 years (2015-2024)
- **Harmonized System (HS) codes** and descriptions
- **Tariff rates** (General, Special, Column 2)
- **Trade statistics** and classifications
- **Annual snapshots** for trend analysis

### Sample Table Structure

Each year's data includes columns like:
- `HS_Number`: Harmonized System classification code
- `Brief_Description`: Product description
- `General_Rate_of_Duty`: Standard tariff rate
- `Special_Rate_of_Duty`: Preferential rates
- `Column_2_Rate_of_Duty`: Alternative duty rates
- `Units_of_Quantity`: Measurement units

## 🛠️ Available Scripts

### `scripts/build_and_serve.py`

**Purpose**: Complete end-to-end setup and server launch

**Features**:
- Checks for existing database
- Downloads and processes USITC data if needed
- Starts MCP server with appropriate configuration
- Provides status updates and server information

**Usage**:
```bash
python scripts/build_and_serve.py
```

**Output**:
- Database at: `data/usitc_data/usitc_trade_data.db`
- MCP Server at: `http://127.0.0.1:8000/mcp`
- Read-only access for safe querying

### `scripts/test_enhanced_client.py`

**Purpose**: Comprehensive testing of MCP server functionality

**Features**:
- Tests MCP server initialization
- Validates all available tools
- Demonstrates query capabilities
- Shows data structure and content

**Usage**:
```bash
python scripts/test_enhanced_client.py
```

**Tests Include**:
- Server connectivity and initialization
- Tool discovery (`list_tables`, `get_schema`, `get_sample_data`)
- Query safety and validation
- Data exploration capabilities

## 🔧 MCP Server Tools

The enhanced MCP server provides specialized tools for tariff data analysis:

### Core Tools

- **`list_tables`**: Show all available tariff tables
- **`get_schema`**: Get column information for tables
- **`get_sample_data`**: Preview table contents
- **`query`**: Execute SQL queries on tariff data

### Example Queries

Once the server is running, you can ask AI assistants questions like:

- "Show me the tariff rates for steel products in 2024"
- "Compare tariff rates between 2015 and 2024 for electronics"
- "What are the most common tariff rates for agricultural products?"
- "Find all products with special duty rates"

## 💻 Integration with AI Clients

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "usitc-tariffs": {
      "command": "python",
      "args": [
        "-m", "mcp_server_motherduck.server",
        "--transport", "stream",
        "--db-path", "/path/to/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
        "--read-only"
      ],
      "cwd": "/path/to/mcp-tarrifs/src"
    }
  }
}
```

### Cursor / VS Code

Add to your MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "usitc-tariffs": {
        "command": "python",
        "args": [
          "-m", "mcp_server_motherduck.server",
          "--transport", "stream", 
          "--db-path", "/path/to/mcp-tarrifs/data/usitc_data/usitc_trade_data.db",
          "--read-only"
        ],
        "cwd": "/path/to/mcp-tarrifs/src"
      }
    }
  }
}
```

## 🗂️ Data Sources

This project uses official USITC (United States International Trade Commission) tariff data:

- **Source**: [USITC DataWeb](https://dataweb.usitc.gov/)
- **Coverage**: 2015-2024 (10 years)
- **Format**: Annual tariff databases in Excel and text formats
- **Update Frequency**: Updated when new annual data is released

## 🔍 Development

### Project Components

1. **Core MCP Server** (`src/mcp_server_motherduck/`):
   - Basic MotherDuck/DuckDB MCP implementation
   - Standard SQL query capabilities
   - See [dedicated README](src/mcp_server_motherduck/README.md)

2. **Enhanced Tariff Server** (`src/tariffs_mcp/`):
   - Specialized tools for tariff data
   - Data download and processing utilities
   - Enhanced query capabilities

### Running Tests

```bash
# Test basic functionality
python scripts/test_enhanced_client.py

# Test data download (without building full database)
uv run python src/tariffs_mcp/db_build.py --help
```

### Rebuilding Database

To rebuild the database from scratch:

```bash
# Remove existing database
rm data/usitc_data/usitc_trade_data.db

# Run build script again
python scripts/build_and_serve.py
```

## 📈 Performance

- **Database Size**: ~50MB for 10 years of data
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

**"Database not found"**: Run `python scripts/build_and_serve.py` to build the database

**"Server not responding"**: Check that port 8000 is available and server started successfully

**"Permission denied"**: Ensure you have write access to the `data/` directory

**"Module not found"**: Run `uv sync` to install dependencies

### Getting Help

1. Check the server logs when running `build_and_serve.py`
2. Run the test client to verify functionality
3. Ensure all dependencies are installed with `uv sync`
4. Check that the database file exists at `data/usitc_data/usitc_trade_data.db`

---

**🎉 Happy Analyzing!** This project brings 10 years of US tariff data to your fingertips through the power of MCP and AI assistants.
