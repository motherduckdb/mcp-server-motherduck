#!/usr/bin/env python3
"""
USITC Annual Tariff Data Downloader and DuckDB Loader

This script downloads annual tariff data zip files from USITC,
extracts them, and loads the data into a DuckDB database.

Usage examples:
    python usitc_downloader.py --download --years 5
    python usitc_downloader.py --load
    python usitc_downloader.py --query
    python usitc_downloader.py --all --years 11
"""

import os
import requests
import zipfile
import duckdb
import time
import argparse
from pathlib import Path
from urllib.parse import urljoin
import logging
from datetime import datetime
import threading

# Check for pandas availability
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not installed. Excel file support disabled.")

# Setup logging
def setup_logging(log_level='INFO'):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('usitc_download.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class USITCDataManager:
    def __init__(self, base_dir="./data/usitc_data", db_name="usitc_trade_data.db"):
        self.base_url = "https://www.usitc.gov/tariff_affairs/documents/tariff_data/"
        self.base_dir = Path(base_dir)
        self.download_dir = self.base_dir / "downloads"
        self.extract_dir = self.base_dir / "extracted"
        self.db_path = self.base_dir / db_name
        
        # Create directories
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.extract_dir.mkdir(parents=True, exist_ok=True)
        
        # DuckDB connection (initialized when needed)
        self._conn = None
        self._conn_lock = threading.Lock()
        
        # Updated file naming patterns for USITC tariff_affairs URL structure
        self.url_patterns = [
            "tariff_data_{year}.zip",
            "tariff_{year}.zip",
            "{year}_tariff_data.zip",
            "hts_{year}.zip",
            "{year}_annual_tariff.zip",
            "annual_tariff_{year}.zip",
            "annual_{year}.zip",
            "{year}.zip"
        ]
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized USITC manager with base directory: {self.base_dir}")

    @property
    def conn(self):
        """Thread-safe lazy initialization of DuckDB connection"""
        with self._conn_lock:
            if self._conn is None:
                self._conn = duckdb.connect(str(self.db_path))
                self.logger.info(f"Connected to database: {self.db_path}")
            return self._conn

    def get_years_to_download(self, num_years=11):
        """Get list of years to download (last N years including current year)"""
        current_year = datetime.now().year
        # Include 2025 data if available
        start_year = current_year
        years = list(range(start_year - num_years + 1, start_year + 1))
        self.logger.info(f"Target years for download: {years}")
        return years

    def download_file(self, url, local_path, timeout=30):
        """Download a file using curl (more reliable than requests for this site)"""
        import subprocess
        
        try:
            self.logger.info(f"Attempting to download: {url}")
            
            # Use curl to download the file (simplified to match working command)
            cmd = [
                'curl',
                '-L',  # Follow redirects
                '-o', str(local_path),  # Output file
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 3)
            
            if result.returncode == 0:
                file_size = os.path.getsize(local_path)
                self.logger.info(f"Downloaded {local_path.name} ({file_size:,} bytes)")
                
                # Verify it's a valid zip file
                if not self.is_valid_zip(local_path):
                    self.logger.warning(f"Downloaded file {local_path.name} is not a valid zip")
                    os.remove(local_path)
                    return False
                
                return True
            else:
                self.logger.error(f"curl failed with exit code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"curl error: {result.stderr.strip()}")
                
                # Clean up failed download
                if local_path.exists():
                    os.remove(local_path)
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Download timed out after {timeout * 3} seconds")
            if local_path.exists():
                os.remove(local_path)
            return False
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {e}")
            # Clean up partial download
            if local_path.exists():
                try:
                    os.remove(local_path)
                except:
                    pass
            return False

    def download_file_with_retry(self, url, local_path, max_retries=3, timeout=30):
        """Download with retry logic"""
        for attempt in range(max_retries):
            if self.download_file(url, local_path, timeout):
                return True
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                self.logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        return False

    def try_download_year(self, year):
        """Try different URL patterns for a given year"""
        self.logger.info(f"Attempting to download data for year {year}")
        
        for i, pattern in enumerate(self.url_patterns):
            filename = pattern.format(year=year)
            url = urljoin(self.base_url, filename)
            local_path = self.download_dir / filename
            
            self.logger.debug(f"  Trying pattern {i+1}/{len(self.url_patterns)}: {filename}")
            
            # Skip if already downloaded and valid
            if local_path.exists() and self.is_valid_zip(local_path):
                self.logger.info(f"File {filename} already exists and is valid")
                return str(local_path)
            
            # Try to download with retry
            if self.download_file_with_retry(url, local_path):
                self.logger.info(f"Successfully downloaded {filename}")
                return str(local_path)
            
            # Add small delay between attempts
            time.sleep(1)
        
        self.logger.error(f"Could not download data for year {year} with any URL pattern")
        return None

    def is_valid_zip(self, file_path):
        """Check if a file is a valid zip archive"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Try to read the file list
                file_list = zip_ref.namelist()
                self.logger.debug(f"Zip contains {len(file_list)} files")
            return True
        except (zipfile.BadZipFile, FileNotFoundError) as e:
            self.logger.debug(f"Invalid zip file {file_path}: {e}")
            return False

    def extract_zip_file(self, zip_path, year):
        """Extract a zip file to the appropriate directory"""
        year_dir = self.extract_dir / str(year)
        year_dir.mkdir(exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                self.logger.info(f"Extracting {len(file_list)} files from {Path(zip_path).name}")
                
                zip_ref.extractall(year_dir)
                
                # Log extracted files
                extracted_files = []
                for file in file_list:
                    extracted_path = year_dir / file
                    if extracted_path.exists():
                        extracted_files.append(str(extracted_path))
                
                self.logger.info(f"Extracted {len(extracted_files)} files to {year_dir}")
                return extracted_files
                
        except Exception as e:
            self.logger.error(f"Failed to extract {zip_path}: {e}")
            return []

    def find_data_files(self, directory):
        """Recursively find all data files, preferring xlsx over txt"""
        data_files = []
        extensions = ['.csv', '.txt', '.tsv', '.xlsx', '.xls']
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    data_files.append(os.path.join(root, file))
        
        # Simple preference: if there are both .xlsx and .txt files, only keep .xlsx files
        xlsx_files = [f for f in data_files if f.lower().endswith('.xlsx')]
        other_files = [f for f in data_files if not f.lower().endswith(('.txt', '.xlsx'))]
        
        if xlsx_files:
            # If xlsx files exist, skip all txt files
            txt_files = [f for f in data_files if f.lower().endswith('.txt')]
            if txt_files:
                self.logger.info(f"Found {len(xlsx_files)} xlsx and {len(txt_files)} txt files. Using only xlsx files.")
            filtered_files = xlsx_files + other_files
        else:
            # No xlsx files, use everything
            filtered_files = data_files
        
        self.logger.debug(f"Found {len(data_files)} total files, filtered to {len(filtered_files)} files")
        return filtered_files

    def get_table_name(self, file_path, year):
        """Generate a clean and valid table name from file path"""
        filename = Path(file_path).stem
        # Clean filename for SQL table name
        table_name = f"tariff_{year}_{filename}"
        table_name = table_name.replace('-', '_').replace(' ', '_').replace('.', '_')
        # Remove any non-alphanumeric characters except underscore
        table_name = ''.join(c for c in table_name if c.isalnum() or c == '_')
        table_name = table_name.lower()
        
        # Additional validation
        if not table_name or table_name[0].isdigit():
            table_name = f"table_{table_name}"  # Ensure valid SQL identifier
        if len(table_name) > 63:  # Common DB identifier limit
            table_name = table_name[:63]
        
        return table_name

    def load_file_to_duckdb(self, file_path, table_name):
        """Load a data file into DuckDB with error handling"""
        try:
            file_ext = Path(file_path).suffix.lower()
            self.logger.info(f"Loading {Path(file_path).name} into table {table_name}")
            
            if file_ext in ['.csv', '.txt', '.tsv']:
                # Use DuckDB's CSV auto-detection
                self.conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} AS 
                    SELECT * FROM read_csv_auto('{file_path}')
                """)
            elif file_ext in ['.xlsx', '.xls']:
                if not PANDAS_AVAILABLE:
                    self.logger.error("pandas required for Excel files but not installed")
                    return False
                # For Excel files, use pandas to read and then insert
                df = pd.read_excel(file_path)
                # FIXED: Properly register DataFrame with DuckDB
                self.conn.register('temp_df', df)
                self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM temp_df")
                self.conn.unregister('temp_df')
            else:
                self.logger.warning(f"Unsupported file type: {file_ext}")
                return False
            
            # Get row count
            result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            row_count = result[0] if result else 0
            
            self.logger.info(f"Successfully loaded {row_count:,} rows into {table_name}")
            
            # Validate the table was created properly
            if not self.validate_loaded_table(table_name):
                self.logger.warning(f"Table {table_name} validation failed")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load {file_path} into DuckDB: {e}")
            self.logger.debug(f"File details - Size: {os.path.getsize(file_path)} bytes, Type: {Path(file_path).suffix}")
            return False

    def validate_loaded_table(self, table_name):
        """Validate that table was loaded correctly"""
        try:
            # Check if table exists
            result = self.conn.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            """).fetchone()
            
            if not result or result[0] == 0:
                return False
                
            # Check if table has data
            row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            return row_count > 0
            
        except Exception as e:
            self.logger.error(f"Validation failed for {table_name}: {e}")
            return False

    def create_summary_table(self):
        """Create a summary table of all loaded data"""
        try:
            # Get list of all tables
            tables = self.conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main' 
                AND table_name LIKE 'tariff_%'
                ORDER BY table_name
            """).fetchall()
            
            if not tables:
                self.logger.warning("No tariff tables found")
                return
            
            # Create summary
            summary_data = []
            for table in tables:
                table_name = table[0]
                try:
                    # Get table info
                    count_result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                    cols_result = self.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                    
                    summary_data.append({
                        'table_name': table_name,
                        'row_count': count_result[0] if count_result else 0,
                        'column_count': len(cols_result)
                    })
                except Exception as e:
                    self.logger.error(f"Error getting info for table {table_name}: {e}")
            
            # Create summary table
            if summary_data:
                df = pd.DataFrame(summary_data) if PANDAS_AVAILABLE else None
                if df is not None:
                    self.conn.register('summary_df', df)
                    self.conn.execute("DROP TABLE IF EXISTS data_summary")
                    self.conn.execute("CREATE TABLE data_summary AS SELECT * FROM summary_df")
                    self.conn.unregister('summary_df')
                self.logger.info("Created data_summary table")
                
                # Display summary
                self.logger.info("\n=== Data Summary ===")
                total_rows = sum(row['row_count'] for row in summary_data)
                self.logger.info(f"Total tables: {len(summary_data)}")
                self.logger.info(f"Total rows across all tables: {total_rows:,}")
                self.logger.info("\nIndividual tables:")
                for row in summary_data:
                    self.logger.info(f"  {row['table_name']}: {row['row_count']:,} rows, {row['column_count']} columns")
                    
        except Exception as e:
            self.logger.error(f"Failed to create summary table: {e}")

    def run_sample_queries(self):
        """Run some sample analytical queries"""
        try:
            self.logger.info("\n=== Running Sample Queries ===")
            
            # List all tables
            tables = self.conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main' 
                AND table_name LIKE 'tariff_%'
                ORDER BY table_name
            """).fetchall()
            
            if not tables:
                self.logger.warning("No data tables found to query")
                return
            
            self.logger.info(f"Available tables: {len(tables)} total")
            for table in tables[:5]:  # Show first 5
                self.logger.info(f"  - {table[0]}")
            if len(tables) > 5:
                self.logger.info(f"  ... and {len(tables) - 5} more")
            
            # Examine sample table structure
            sample_table = tables[0][0]
            self.logger.info(f"\nExamining structure of: {sample_table}")
            
            columns = self.conn.execute(f"PRAGMA table_info({sample_table})").fetchall()
            self.logger.info(f"Columns ({len(columns)} total):")
            for col in columns[:10]:  # Show first 10 columns
                self.logger.info(f"  {col[1]}: {col[2]}")
            if len(columns) > 10:
                self.logger.info(f"  ... and {len(columns) - 10} more columns")
            
            # Sample data
            self.logger.info(f"\nSample data from {sample_table}:")
            try:
                sample_data = self.conn.execute(f"SELECT * FROM {sample_table} LIMIT 3").fetchall()
                if sample_data:
                    # Show just first few columns to avoid overwhelming output
                    col_names = [col[1] for col in columns[:5]]
                    for i, row in enumerate(sample_data):
                        row_data = {col_names[j]: row[j] for j in range(min(len(col_names), len(row)))}
                        self.logger.info(f"  Row {i+1}: {row_data}")
                else:
                    self.logger.info("  No data found")
            except Exception as e:
                self.logger.error(f"  Error fetching sample data: {e}")
                
        except Exception as e:
            self.logger.error(f"Error running sample queries: {e}")

    # Main operation methods
    def download_data(self, num_years=11):
        """Download zip files for specified years"""
        self.logger.info(f"=== DOWNLOAD OPERATION: {num_years} years ===")
        
        years = self.get_years_to_download(num_years)
        successful_downloads = 0
        
        for year in years:
            self.logger.info(f"\n--- Downloading year {year} ---")
            
            zip_path = self.try_download_year(year)
            if zip_path:
                successful_downloads += 1
                self.logger.info(f"[SUCCESS] Downloaded data for {year}")  # Fixed unicode
            else:
                self.logger.error(f"[FAILED] Failed to download data for {year}")  # Fixed unicode
        
        self.logger.info(f"\n=== DOWNLOAD SUMMARY ===")
        self.logger.info(f"Successfully downloaded: {successful_downloads}/{len(years)} years")
        self.logger.info(f"Downloaded files location: {self.download_dir}")
        
        return successful_downloads

    def load_data(self):
        """Extract downloaded files and load into database"""
        self.logger.info("=== LOAD OPERATION ===")
        
        # Find all downloaded zip files
        zip_files = list(self.download_dir.glob("*.zip"))
        if not zip_files:
            self.logger.error("No zip files found to extract. Run download operation first.")
            return 0
        
        self.logger.info(f"Found {len(zip_files)} zip files to process")
        
        successful_loads = 0
        
        for zip_path in zip_files:
            # Try to extract year from filename
            year = None
            for y in range(1990, 2030):
                if str(y) in zip_path.name:
                    year = y
                    break
            
            if not year:
                self.logger.warning(f"Could not determine year from {zip_path.name}, using 'unknown'")
                year = "unknown"
            
            self.logger.info(f"\n--- Processing {zip_path.name} (year: {year}) ---")
            
            # Extract zip file
            extracted_files = self.extract_zip_file(zip_path, year)
            if not extracted_files:
                continue
            
            # Find and load data files
            year_dir = self.extract_dir / str(year)
            data_files = self.find_data_files(year_dir)
            
            self.logger.info(f"Found {len(data_files)} data files for year {year}")
            
            for data_file in data_files:
                table_name = self.get_table_name(data_file, year)
                if self.load_file_to_duckdb(data_file, table_name):
                    successful_loads += 1
        
        self.logger.info(f"\n=== LOAD SUMMARY ===")
        self.logger.info(f"Successfully loaded: {successful_loads} files")
        self.logger.info(f"Database location: {self.db_path}")
        
        # Create summary
        self.create_summary_table()
        
        return successful_loads

    def query_data(self):
        """Run sample queries on the database"""
        self.logger.info("=== QUERY OPERATION ===")
        
        if not self.db_path.exists():
            self.logger.error("Database not found. Run load operation first.")
            return
        
        self.create_summary_table()
        self.run_sample_queries()

    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self.logger.info("Database connection closed")


def main():
    """Main execution function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="USITC Annual Tariff Data Downloader and DuckDB Loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --download --years 5           # Download last 5 years only
  %(prog)s --load                         # Extract and load downloaded files
  %(prog)s --query                        # Run sample queries on database
  %(prog)s --all --years 11               # Do everything for 2015-2025 (default)
  %(prog)s --download --load --years 3    # Download and load last 3 years
        """
    )
    
    # Operation arguments
    parser.add_argument('--download', action='store_true',
                       help='Download zip files from USITC')
    parser.add_argument('--load', action='store_true',
                       help='Extract zip files and load data into database')
    parser.add_argument('--query', action='store_true',
                       help='Run sample queries on the database')
    parser.add_argument('--all', action='store_true',
                       help='Perform all operations (download, load, query)')
    
    # Configuration arguments
    parser.add_argument('--years', type=int, default=11,
                       help='Number of years to download (default: 11, includes 2015-2025)')
    parser.add_argument('--base-dir', default='./data/usitc_data',
                       help='Base directory for data storage (default: ./data/usitc_data)')
    parser.add_argument('--db-name', default='usitc_trade_data.db',
                       help='Database filename (default: usitc_trade_data.db)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    # Validate arguments
    if not any([args.download, args.load, args.query, args.all]):
        parser.error("Must specify at least one operation: --download, --load, --query, or --all")
    
    # Initialize manager
    try:
        manager = USITCDataManager(base_dir=args.base_dir, db_name=args.db_name)
        
        logger.info("=== USITC Data Manager Started ===")
        logger.info(f"Base directory: {args.base_dir}")
        logger.info(f"Database: {args.db_name}")
        logger.info(f"Years to process: {args.years}")
        
        # Perform operations
        if args.all:
            logger.info("Performing all operations...")
            downloads = manager.download_data(args.years)
            loads = manager.load_data()
            manager.query_data()
        else:
            if args.download:
                downloads = manager.download_data(args.years)
            
            if args.load:
                loads = manager.load_data()
            
            if args.query:
                manager.query_data()
        
        logger.info("\n=== PROCESS COMPLETED ===")
        logger.info(f"Files are in: {manager.base_dir}")
        logger.info(f"Database: {manager.db_path}")
        logger.info("You can now connect to the database and run your own queries!")
        
        # Example usage
        logger.info(f"\nTo connect manually:")
        logger.info(f"  import duckdb")
        logger.info(f"  conn = duckdb.connect('{manager.db_path}')")
        logger.info(f"  conn.execute('SHOW TABLES').fetchall()")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if 'manager' in locals():
            manager.close()


if __name__ == "__main__":
    main()