# USITC Annual Tariff Data Downloader

A Python tool for downloading, extracting, and loading United States International Trade Commission (USITC) annual tariff data into a DuckDB database for analysis.

## 🎯 Overview

This script automates the process of:
- Downloading annual tariff data ZIP files from USITC's public data repository
- Extracting the compressed data files
- Loading CSV, TSV, and Excel files into a DuckDB database
- Providing a structured, queryable database of US tariff information

## ✨ Features

- **Automatic Data Discovery**: Tries multiple URL patterns to find available tariff data
- **Multi-Format Support**: Handles CSV, TSV, TXT, XLS, and XLSX files
- **Robust Error Handling**: Includes retry logic with exponential backoff for downloads
- **Progress Logging**: Detailed logging to file and console
- **Database Management**: Creates organized tables in DuckDB with automatic schema detection
- **Data Validation**: Validates ZIP files and loaded tables
- **Thread-Safe**: Database connections are thread-safe for concurrent operations
- **Resume Capability**: Skips already downloaded files when re-running

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## 🚀 Installation

1. Clone or download the script files:
```bash
# Create a project directory
mkdir usitc_tariff_downloader
cd usitc_tariff_downloader

# Save the script as usitc_downloader.py
# Save the requirements file as requirements.txt
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `duckdb` - Database engine
- `pandas` - Excel file handling
- `requests` - HTTP downloads
- `openpyxl` - Modern Excel file support (.xlsx)
- `xlrd` - Legacy Excel file support (.xls)

## 📖 Usage

### Basic Commands

```bash
# Download last 5 years of data
python usitc_downloader.py --download --years 5

# Load downloaded files into database
python usitc_downloader.py --load

# Run sample queries to verify data
python usitc_downloader.py --query

# Do everything in one command (download, load, query)
python usitc_downloader.py --all --years 10
```

### Advanced Usage

```bash
# Download and load in a single operation
python usitc_downloader.py --download --load --years 3

# Use custom directory and database name
python usitc_downloader.py --all --base-dir ./my_data --db-name tariffs.db

# Enable debug logging for troubleshooting
python usitc_downloader.py --download --log-level DEBUG
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--download` | Download ZIP files from USITC | - |
| `--load` | Extract ZIPs and load data into database | - |
| `--query` | Run sample queries on the database | - |
| `--all` | Perform all operations (download, load, query) | - |
| `--years N` | Number of years to download (counting backwards from current year) | 10 |
| `--base-dir PATH` | Base directory for data storage | ./usitc_data |
| `--db-name NAME` | Database filename | usitc_trade_data.db |
| `--log-level LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | INFO |

## 📁 Project Structure

After running the script, your directory structure will look like:

```
usitc_data/
├── downloads/           # Downloaded ZIP files
│   ├── 2024_annual_tariff.zip
│   ├── 2023_annual_tariff.zip
│   └── ...
├── extracted/           # Extracted data files
│   ├── 2024/
│   │   ├── tariff_data.csv
│   │   └── ...
│   ├── 2023/
│   │   └── ...
│   └── ...
├── usitc_trade_data.db # DuckDB database
└── usitc_download.log   # Log file
```

## 🔍 Accessing the Data

### Using Python

```python
import duckdb

# Connect to the database
conn = duckdb.connect('./usitc_data/usitc_trade_data.db')

# List all tables
tables = conn.execute("SHOW TABLES").fetchall()
print(f"Available tables: {tables}")

# Query specific table
result = conn.execute("""
    SELECT * 
    FROM tariff_2024_annual_data 
    LIMIT 10
""").fetchall()

# Get table information
conn.execute("DESCRIBE tariff_2024_annual_data").fetchall()

# View summary statistics
conn.execute("SELECT * FROM data_summary").fetchall()

conn.close()
```

### Using DuckDB CLI

```bash
# Install DuckDB CLI
pip install duckdb

# Connect to database
duckdb ./usitc_data/usitc_trade_data.db

# In DuckDB prompt:
.tables                    -- List all tables
.schema tariff_2024_data   -- Show table structure
SELECT * FROM data_summary; -- View summary
```

### Using pandas

```python
import duckdb
import pandas as pd

conn = duckdb.connect('./usitc_data/usitc_trade_data.db')

# Load table into pandas DataFrame
df = conn.execute("SELECT * FROM tariff_2024_annual_data").fetchdf()

# Now use pandas for analysis
print(df.head())
print(df.info())
print(df.describe())

conn.close()
```

## 📊 Database Schema

The script creates tables with the naming convention: `tariff_YYYY_filename`

Each table preserves the original structure of the source file with:
- Automatic type detection
- Column names from headers
- All data from the source file

A special `data_summary` table is created containing:
- `table_name`: Name of each loaded table
- `row_count`: Number of rows in the table  
- `column_count`: Number of columns in the table

## 🔧 Troubleshooting

### Common Issues

1. **"No ZIP files found to extract"**
   - Run with `--download` flag first
   - Check internet connection
   - Verify USITC website is accessible

2. **"pandas required for Excel files but not installed"**
   - Install pandas: `pip install pandas openpyxl`
   - Or skip Excel files (CSV files usually contain same data)

3. **Download failures**
   - Script automatically retries 3 times
   - Check `usitc_download.log` for detailed error messages
   - Try `--log-level DEBUG` for more information
   - USITC server may be temporarily unavailable

4. **Database connection errors**
   - Ensure write permissions in the base directory
   - Check disk space availability
   - Close other connections to the database

### Debug Mode

Enable detailed logging to troubleshoot issues:
```bash
python usitc_downloader.py --download --log-level DEBUG
```

Check the log file:
```bash
tail -f usitc_download.log
```

## 📈 Data Analysis Examples

### Find Tables by Year
```sql
SELECT table_name, row_count 
FROM data_summary 
WHERE table_name LIKE '%2024%'
ORDER BY row_count DESC;
```

### Export to CSV
```python
import duckdb

conn = duckdb.connect('./usitc_data/usitc_trade_data.db')
conn.execute("""
    COPY tariff_2024_data 
    TO 'tariff_2024_export.csv' 
    WITH (HEADER, DELIMITER ',')
""")
```

### Combine Multiple Years
```sql
CREATE TABLE tariff_combined AS
SELECT *, 2024 as year FROM tariff_2024_data
UNION ALL
SELECT *, 2023 as year FROM tariff_2023_data;
```

## ⚠️ Important Notes

- **Data Size**: Each year's data can be several hundred MB when extracted
- **Processing Time**: Initial download and load of 10 years may take 30-60 minutes
- **Disk Space**: Ensure at least 5-10 GB free space for 10 years of data
- **Network**: Requires stable internet connection for downloads
- **Updates**: USITC typically releases annual data after year-end

## 🐛 Known Limitations

1. URL patterns may change if USITC restructures their website
2. Some older years may use different file formats
3. Very large files (>2GB) may require additional memory
4. Excel files require pandas; without it, only CSV/TSV files are processed


## 📚 Additional Resources

- [USITC DataWeb](https://dataweb.usitc.gov/) - Official USITC trade data portal
- [DuckDB Documentation](https://duckdb.org/docs/) - Database documentation
- [Harmonized Tariff Schedule](https://hts.usitc.gov/) - Current HTS c