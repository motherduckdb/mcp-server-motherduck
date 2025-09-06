# Tests Directory

This directory contains all tests for the MCP Tariffs Server project.

## Structure

- `test_consolidation.py` - Tests for the consolidated MCP server functionality
- `test_mcp_logging.py` - Tests for MCP request logging functionality

## Running Tests

### Run all tests with pytest:
```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_consolidation.py

# Run tests with verbose output
pytest -v
```

### Run individual test scripts:
```bash
# Run consolidation tests
python tests/test_consolidation.py

# Run logging tests  
python tests/test_mcp_logging.py
```

## Test Types

- **Integration Tests**: Test the full server initialization and database connectivity
- **Logging Tests**: Verify that MCP request logging is working correctly
- **Database Tests**: Test database operations and schema validation

## Adding New Tests

When adding new tests:
1. Create test files with the `test_*.py` naming pattern
2. Use pytest fixtures for common setup/teardown
3. Mark async tests with `@pytest.mark.asyncio` 
4. Add appropriate imports for the modules under test
