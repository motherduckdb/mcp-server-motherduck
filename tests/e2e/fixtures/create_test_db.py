#!/usr/bin/env python3
"""
Create a local test DuckDB database with sample data from MotherDuck.

This script connects to MotherDuck's sample_data database and creates a local
copy with a subset of the data for testing purposes.

Usage:
    python tests/e2e/fixtures/create_test_db.py

Requires MOTHERDUCK_TOKEN or MOTHERDUCK_TOKEN_READ_SCALING environment variable.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on environment variables

import duckdb


def create_test_database():
    """Create test database with sample data."""
    # Get token from environment
    token = os.environ.get("MOTHERDUCK_TOKEN_READ_SCALING") or os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        print("Error: Set MOTHERDUCK_TOKEN or MOTHERDUCK_TOKEN_READ_SCALING environment variable")
        sys.exit(1)

    # Paths
    script_dir = Path(__file__).parent
    test_db_path = script_dir / "test.duckdb"

    # Remove existing test database
    if test_db_path.exists():
        test_db_path.unlink()
        print(f"Removed existing {test_db_path}")

    print(f"Creating test database at {test_db_path}")

    # Connect to MotherDuck to fetch sample data
    md_conn = duckdb.connect(f"md:?motherduck_token={token}")

    # Connect to local database
    local_conn = duckdb.connect(str(test_db_path))

    try:
        # Create tables with sample data from MotherDuck sample_data database
        print("Fetching sample data from MotherDuck...")

        # 1. Movies table (small, good for basic tests)
        print("  - Creating movies table...")
        movies_data = md_conn.execute("""
            SELECT * FROM sample_data.kaggle.movies LIMIT 100
        """).fetchall()
        movies_cols = md_conn.execute("""
            SELECT * FROM sample_data.kaggle.movies LIMIT 0
        """).description

        # Create movies table locally
        col_defs = ", ".join([f'"{col[0]}" VARCHAR' for col in movies_cols])
        local_conn.execute(f"CREATE TABLE movies ({col_defs})")

        # Insert data
        placeholders = ", ".join(["?" for _ in movies_cols])
        local_conn.executemany(f"INSERT INTO movies VALUES ({placeholders})", movies_data)
        print(f"    Inserted {len(movies_data)} rows")

        # 2. Create a simple users table for write tests
        print("  - Creating users table...")
        local_conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name VARCHAR,
                email VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        local_conn.execute("""
            INSERT INTO users (id, name, email) VALUES
            (1, 'Alice', 'alice@example.com'),
            (2, 'Bob', 'bob@example.com'),
            (3, 'Charlie', 'charlie@example.com')
        """)
        print("    Inserted 3 rows")

        # 3. Create a large table for limit/pagination tests
        print("  - Creating large_table for limit tests...")
        local_conn.execute("""
            CREATE TABLE large_table AS
            SELECT
                range as id,
                'row_' || range as data,
                random() as random_value
            FROM range(10000)
        """)
        print("    Created 10,000 rows")

        # 4. Create a table with wide rows for char limit tests
        print("  - Creating wide_table for char limit tests...")
        local_conn.execute("""
            CREATE TABLE wide_table AS
            SELECT
                range as id,
                repeat('x', 1000) as wide_column_1,
                repeat('y', 1000) as wide_column_2,
                repeat('z', 1000) as wide_column_3
            FROM range(100)
        """)
        print("    Created 100 rows with wide columns")

        # Verify tables
        print("\nVerifying tables:")
        tables = local_conn.execute("SHOW TABLES").fetchall()
        for table in tables:
            count = local_conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
            print(f"  - {table[0]}: {count} rows")

        print(f"\nTest database created successfully at {test_db_path}")

    finally:
        md_conn.close()
        local_conn.close()


if __name__ == "__main__":
    create_test_database()
