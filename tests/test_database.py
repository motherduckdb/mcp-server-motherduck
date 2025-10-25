import os
import tempfile
from typing import cast
from duckdb import DuckDBPyConnection
import pytest
from unittest.mock import patch, MagicMock
from mcp_server_motherduck.database import DatabaseClient


class TestDatabaseClient:

    @pytest.fixture
    def clean_env(self):
        """Clean environment variables before each test"""
        env_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_DEFAULT_REGION',
            'motherduck_token',
        ]
        old_values = {}
        for var in env_vars:
            old_values[var] = os.environ.pop(var, None)

        yield

        # Restore old values
        for var, value in old_values.items():
            if value is not None:
                os.environ[var] = value

    @pytest.fixture
    def temp_db_file(self):
        """Create a temporary database file path (file doesn't exist yet)"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=True) as f:
            db_path = f.name
        # File is deleted, but we have the path
        yield db_path
        # Clean up in case test created it
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass

    def test_local_duckdb_connection(self, temp_db_file, clean_env):
        """Test connecting to a local DuckDB file with real connection"""
        db_client = DatabaseClient(db_path=temp_db_file)

        # Verify connection exists and works
        assert db_client.conn is not None
        assert db_client.db_type == 'duckdb'
        assert db_client.db_path == temp_db_file

        # Test we can actually execute a query
        result = db_client.conn.execute("SELECT 1 as test").fetchall()
        assert result == [(1,)]

    def test_memory_database_connection(self, clean_env):
        """Test connecting to an in-memory database with real connection"""
        db_client = DatabaseClient(db_path=':memory:')

        assert db_client.conn is not None
        assert db_client.db_type == 'duckdb'
        assert db_client.db_path == ':memory:'

        # Test we can create a table and query it
        db_client.conn.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")
        db_client.conn.execute("INSERT INTO test VALUES (1, 'hello')")
        result = db_client.conn.execute("SELECT * FROM test").fetchall()
        assert result == [(1, 'hello')]

    def test_read_only_local_connection(self, temp_db_file, clean_env):
        """Test read-only mode for local DuckDB with real connection"""
        # First create a database with some data
        db_client = DatabaseClient(db_path=temp_db_file)
        connection = cast(DuckDBPyConnection, db_client.conn)
        connection.execute("CREATE TABLE test (id INTEGER)")
        connection.execute("INSERT INTO test VALUES (1)")
        connection.close()

        # Now open in read-only mode
        ro_client = DatabaseClient(db_path=temp_db_file, read_only=True)

        # Connection should be None in read-only mode (uses short-lived connections)
        assert ro_client.conn is None
        assert ro_client.db_type == 'duckdb'
        assert ro_client._read_only is True

    def test_read_only_connection_check_failure(self, clean_env):
        """Test that read-only connection check failure raises exception"""
        # Try to open non-existent file in read-only mode
        with pytest.raises(Exception):
            DatabaseClient(db_path='/nonexistent/path/to/database.db', read_only=True)

    def test_query_execution(self, clean_env):
        """Test query execution with real data and formatting"""
        db_client = DatabaseClient(db_path=':memory:')

        # Create test data
        connection = cast(DuckDBPyConnection, db_client.conn)
        connection.execute("CREATE TABLE users (id INTEGER, name VARCHAR, age INTEGER)")
        connection.execute("INSERT INTO users VALUES (1, 'Alice', 30), (2, 'Bob', 25)")

        # Execute query and verify formatted output
        result = db_client.query('SELECT * FROM users ORDER BY id')

        # Verify it's a formatted table string
        assert isinstance(result, str)
        assert 'Alice' in result
        assert 'Bob' in result
        assert '30' in result
        assert '25' in result

    def test_query_execution_error(self, clean_env):
        """Test that query execution errors are properly wrapped"""
        db_client = DatabaseClient(db_path=':memory:')

        # Try to query non-existent table
        with pytest.raises(ValueError, match="Error executing query"):
            db_client.query('SELECT * FROM nonexistent_table')

    def test_query_with_short_lived_connection(self, temp_db_file, clean_env):
        """Test query execution with short-lived read-only connection"""
        # First create a database with data
        db_client = DatabaseClient(db_path=temp_db_file)
        connection = cast(DuckDBPyConnection, db_client.conn)
        connection.execute("CREATE TABLE test (value VARCHAR)")
        connection.execute("INSERT INTO test VALUES ('data')")
        connection.close()

        # Open in read-only mode (conn is None, uses short-lived connections)
        ro_client = DatabaseClient(db_path=temp_db_file, read_only=True)

        # Execute query - should create and close connection automatically
        result = ro_client.query('SELECT * FROM test')

        assert isinstance(result, str)
        assert 'data' in result

    def test_db_path_type_resolution_local(self, temp_db_file, clean_env):
        """Test that local paths are correctly identified"""
        db_client = DatabaseClient(db_path=temp_db_file)

        assert db_client.db_path == temp_db_file
        assert db_client.db_type == 'duckdb'

    def test_db_path_type_resolution_memory(self, clean_env):
        """Test that :memory: paths are correctly identified"""
        db_client = DatabaseClient(db_path=':memory:')

        assert db_client.db_path == ':memory:'
        assert db_client.db_type == 'duckdb'

    def test_home_dir_override(self, clean_env):
        """Test that HOME environment variable is set when home_dir is provided"""
        original_home = os.environ.get('HOME')

        DatabaseClient(db_path=':memory:', home_dir='/custom/home')

        # Verify HOME was set
        assert os.environ['HOME'] == '/custom/home'

        # Restore original HOME
        if original_home:
            os.environ['HOME'] = original_home

    def test_multiple_queries_with_persistent_connection(self, clean_env):
        """Test multiple queries with persistent connection"""
        db_client = DatabaseClient(db_path=':memory:')

        # Create table
        connection = cast(DuckDBPyConnection, db_client.conn)
        connection.execute("CREATE TABLE numbers (n INTEGER)")

        # Insert multiple times
        for i in range(5):
            connection.execute(f"INSERT INTO numbers VALUES ({i})")

        # Query and verify
        result = db_client.query('SELECT COUNT(*) as count FROM numbers')
        assert '5' in result

    def test_result_formatting_with_types(self, clean_env):
        """Test that result formatting includes column types"""
        db_client = DatabaseClient(db_path=':memory:')
        connection = cast(DuckDBPyConnection, db_client.conn)
        connection.execute("""
            CREATE TABLE mixed_types (
                id INTEGER,
                name VARCHAR,
                price DOUBLE,
                active BOOLEAN
            )
        """)
        connection.execute("""
            INSERT INTO mixed_types VALUES (1, 'Product', 19.99, true)
        """)

        result = db_client.query('SELECT * FROM mixed_types')

        # Verify column types are included in output (tabulate format)
        assert isinstance(result, str)
        assert 'INTEGER' in result or 'BIGINT' in result  # DuckDB may use BIGINT
        assert 'VARCHAR' in result
        assert 'DOUBLE' in result
        assert 'BOOLEAN' in result

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_s3_database_initialization_with_credentials(self, mock_connect, clean_env):
        """Test S3 initialization logic with credentials"""
        # Set up AWS credentials
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key_id'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret_key'
        os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db_client = DatabaseClient(db_path='s3://my-bucket/my-database.db')

        # Verify S3 path was recognized
        assert db_client.db_type == 's3'
        assert db_client.db_path == 's3://my-bucket/my-database.db'

        # Verify in-memory connection was created for S3
        mock_connect.assert_called_once_with(':memory:')

        # Verify httpfs extension was loaded
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        assert any('INSTALL httpfs' in call for call in execute_calls)
        assert any('LOAD httpfs' in call for call in execute_calls)

        # Verify SECRET was created with credentials
        secret_calls = [call for call in execute_calls if 'CREATE SECRET' in call]
        assert len(secret_calls) == 1
        secret_sql = secret_calls[0]
        assert 'TYPE S3' in secret_sql
        assert 'KEY_ID' in secret_sql
        assert 'test_key_id' in secret_sql
        assert 'test_secret_key' in secret_sql
        assert 'us-west-2' in secret_sql

        # Verify database was attached
        attach_calls = [call for call in execute_calls if 'ATTACH' in call]
        assert len(attach_calls) >= 1
        assert 's3://my-bucket/my-database.db' in attach_calls[0]
        assert 'READ_ONLY' in attach_calls[0]

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_s3_database_without_credentials(self, mock_connect, clean_env):
        """Test S3 connection without credentials (no SECRET created)"""
        # No AWS credentials in environment
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        DatabaseClient(db_path='s3://my-bucket/my-database.db')

        # Verify in-memory connection was created
        mock_connect.assert_called_once_with(':memory:')

        # Verify httpfs was loaded but no SECRET was created
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        secret_calls = [call for call in execute_calls if 'CREATE SECRET' in call]
        assert len(secret_calls) == 0

        # Database should still be attached
        attach_calls = [call for call in execute_calls if 'ATTACH' in call]
        assert len(attach_calls) >= 1

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_s3_database_default_region(self, mock_connect, clean_env):
        """Test S3 connection uses default region when not specified"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'
        # Don't set AWS_DEFAULT_REGION

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        DatabaseClient(db_path='s3://my-bucket/my-database.db')

        # Verify default region (us-east-1) is used
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        secret_calls = [call for call in execute_calls if 'CREATE SECRET' in call]
        assert len(secret_calls) == 1
        assert 'us-east-1' in secret_calls[0]

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_s3_database_attachment_failure_and_creation(self, mock_connect, clean_env):
        """Test S3 database creation when attachment fails due to non-existent database"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # First ATTACH fails with "database does not exist", second ATTACH succeeds
        mock_conn.execute.side_effect = [
            None,  # INSTALL httpfs
            None,  # LOAD httpfs
            Exception("database does not exist"),  # First ATTACH fails
            None,  # Second ATTACH (creation) succeeds
            None,  # USE s3db
        ]

        DatabaseClient(db_path='s3://my-bucket/new-database.db', read_only=False)

        # Verify ATTACH was called twice (once failed, once succeeded)
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        attach_calls = [call for call in execute_calls if 'ATTACH' in call]
        assert len(attach_calls) == 2

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_s3_database_creation_failure(self, mock_connect, clean_env):
        """Test that S3 database creation failure raises exception"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # First ATTACH fails, second ATTACH also fails
        mock_conn.execute.side_effect = [
            None,  # INSTALL httpfs
            None,  # LOAD httpfs
            Exception("database does not exist"),  # First ATTACH fails
            Exception("Permission denied"),  # Second ATTACH (creation) fails
        ]

        with pytest.raises(Exception, match="Permission denied"):
            DatabaseClient(db_path='s3://my-bucket/new-database.db', read_only=False)

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_s3_database_attachment_failure_other_error(self, mock_connect, clean_env):
        """Test that S3 database attachment failure with other error raises exception"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # ATTACH fails with a different error (not "database does not exist")
        mock_conn.execute.side_effect = [
            None,  # INSTALL httpfs
            None,  # LOAD httpfs
            Exception("Network error"),  # ATTACH fails
        ]

        with pytest.raises(Exception, match="Network error"):
            DatabaseClient(db_path='s3://my-bucket/database.db', read_only=False)

    def test_s3_read_only_mode_rejected(self, clean_env):
        """Test that read-only mode is rejected for S3 databases"""
        with pytest.raises(ValueError, match="Read-only mode is not supported for S3 databases"):
            DatabaseClient(
                db_path='s3://my-bucket/my-database.db',
                read_only=True
            )

    def test_db_path_type_resolution_s3(self, clean_env):
        """Test that S3 paths are correctly identified"""
        # Just test path resolution, not actual connection
        with patch('mcp_server_motherduck.database.duckdb.connect'):
            db_client = DatabaseClient(db_path='s3://bucket/file.db')

            assert db_client.db_path == 's3://bucket/file.db'
            assert db_client.db_type == 's3'


    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_motherduck_with_token(self, mock_connect, clean_env):
        """Test MotherDuck connection with token (mocked - requires cloud credentials)"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db_client = DatabaseClient(
            db_path='md:my_database',
            motherduck_token='test_token'
        )

        assert db_client.db_type == 'motherduck'
        assert 'motherduck_token=test_token' in db_client.db_path

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_motherduck_requires_token(self, mock_connect, clean_env):
        """Test that MotherDuck paths require a token"""
        with pytest.raises(ValueError, match="motherduck_token"):
            DatabaseClient(db_path='md:my_database')

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_motherduck_with_saas_mode(self, mock_connect, clean_env):
        """Test MotherDuck connection with SaaS mode enabled"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db_client = DatabaseClient(
            db_path='md:my_database',
            motherduck_token='test_token',
            saas_mode=True
        )

        assert db_client.db_type == 'motherduck'
        assert 'motherduck_token=test_token' in db_client.db_path
        assert 'saas_mode=true' in db_client.db_path

    @patch('mcp_server_motherduck.database.duckdb.connect')
    def test_motherduck_token_from_environment(self, mock_connect, clean_env):
        """Test MotherDuck connection using token from environment variable"""
        os.environ['motherduck_token'] = 'env_test_token'

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db_client = DatabaseClient(db_path='md:my_database')

        assert db_client.db_type == 'motherduck'
        assert 'motherduck_token=env_test_token' in db_client.db_path
