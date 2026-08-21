"""
Unit tests for identifier quoting logic.
"""

import pytest

from mcp_server_motherduck.database import (
    DatabaseClient,
    identifier_needs_quoting,
    quote_sql_identifier,
)


class TestIdentifierNeedsQuoting:
    """Tests for identifier_needs_quoting()."""

    def test_simple_name(self):
        assert identifier_needs_quoting("users", set()) is False

    def test_underscore_name(self):
        assert identifier_needs_quoting("my_table", set()) is False

    def test_starts_with_underscore(self):
        assert identifier_needs_quoting("_private", set()) is False

    def test_hyphen(self):
        assert identifier_needs_quoting("my-table", set()) is True

    def test_space(self):
        assert identifier_needs_quoting("my table", set()) is True

    def test_colon(self):
        assert identifier_needs_quoting("Unnamed: 12", set()) is True

    def test_starts_with_digit(self):
        assert identifier_needs_quoting("2023_sales", set()) is True

    def test_empty(self):
        assert identifier_needs_quoting("", set()) is True

    def test_reserved_word(self):
        reserved = {"SELECT", "FROM", "TABLE"}
        assert identifier_needs_quoting("select", reserved) is True
        assert identifier_needs_quoting("SELECT", reserved) is True
        assert identifier_needs_quoting("Select", reserved) is True

    def test_not_reserved(self):
        reserved = {"SELECT", "FROM", "TABLE"}
        assert identifier_needs_quoting("users", reserved) is False

    def test_dot(self):
        assert identifier_needs_quoting("schema.table", set()) is True

    def test_at_sign(self):
        assert identifier_needs_quoting("col@name", set()) is True

    def test_hash(self):
        assert identifier_needs_quoting("field#1", set()) is True


class TestQuoteSqlIdentifier:
    """Tests for quote_sql_identifier()."""

    def test_simple(self):
        assert quote_sql_identifier("users") == '"users"'

    def test_with_hyphen(self):
        assert quote_sql_identifier("my-table") == '"my-table"'

    def test_escapes_internal_quotes(self):
        assert quote_sql_identifier('my"table') == '"my""table"'

    def test_empty(self):
        assert quote_sql_identifier("") == '""'


class TestDatabaseClientQuoting:
    """Tests for DatabaseClient quoting methods using in-memory DuckDB."""

    @pytest.fixture
    def db_client(self):
        return DatabaseClient(db_path=":memory:")

    def test_get_reserved_keywords_returns_nonempty(self, db_client):
        keywords = db_client.get_reserved_keywords()
        assert len(keywords) > 0
        assert "SELECT" in keywords
        assert "FROM" in keywords
        assert "TABLE" in keywords

    def test_get_reserved_keywords_cached(self, db_client):
        kw1 = db_client.get_reserved_keywords()
        kw2 = db_client.get_reserved_keywords()
        assert kw1 is kw2  # same object, not re-fetched

    def test_quote_identifier_for_display_safe_name(self, db_client):
        assert db_client.quote_identifier_for_display("users") == "users"

    def test_quote_identifier_for_display_hyphen(self, db_client):
        assert db_client.quote_identifier_for_display("my-table") == '"my-table"'

    def test_quote_identifier_for_display_reserved_word(self, db_client):
        assert db_client.quote_identifier_for_display("select") == '"select"'

    def test_quote_identifier_for_display_digit_start(self, db_client):
        assert db_client.quote_identifier_for_display("2023_sales") == '"2023_sales"'

    def test_quote_identifier_for_display_census_example(self, db_client):
        result = db_client.quote_identifier_for_display("ACSDT5Y2023_B19080-Data")
        assert result == '"ACSDT5Y2023_B19080-Data"'

    def test_quote_identifier_for_display_unnamed_column(self, db_client):
        result = db_client.quote_identifier_for_display("Unnamed: 12")
        assert result == '"Unnamed: 12"'
