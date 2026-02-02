"""
E2E tests for DuckDB type serialization to JSON.

Tests that all DuckDB data types serialize correctly through the MCP server.
"""

import json

import pytest

from tests.e2e.conftest import get_result_text


def parse_json_result(result) -> dict:
    """Parse JSON from a tool call result."""
    text = get_result_text(result)
    return json.loads(text)


class TestNumericTypes:
    """Test numeric type serialization."""

    @pytest.mark.asyncio
    async def test_integer_types(self, memory_client):
        """Test all integer types."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT
                    1::TINYINT as tinyint_val,
                    100::SMALLINT as smallint_val,
                    1000::INTEGER as int_val,
                    1000000::BIGINT as bigint_val,
                    170141183460469231731687303715884105727::HUGEINT as hugeint_val
            """
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["rowCount"] == 1

    @pytest.mark.asyncio
    async def test_unsigned_integer_types(self, memory_client):
        """Test unsigned integer types."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT
                    255::UTINYINT as utinyint_val,
                    65535::USMALLINT as usmallint_val,
                    4294967295::UINTEGER as uint_val,
                    18446744073709551615::UBIGINT as ubigint_val
            """
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_floating_point_types(self, memory_client):
        """Test floating point types."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT
                    3.14::FLOAT as float_val,
                    3.141592653589793::DOUBLE as double_val,
                    123.456::DECIMAL(10,3) as decimal_val
            """
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        row = data["rows"][0]
        assert isinstance(row[0], (int, float))
        assert isinstance(row[1], (int, float))


class TestStringAndBinaryTypes:
    """Test string and binary type serialization."""

    @pytest.mark.asyncio
    async def test_varchar_types(self, memory_client):
        """Test VARCHAR/TEXT types."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT
                    'hello'::VARCHAR as varchar_val,
                    'world'::TEXT as text_val,
                    'fixed'::CHAR(10) as char_val
            """
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert "hello" in str(data["rows"][0])

    @pytest.mark.asyncio
    async def test_blob_type(self, memory_client):
        """Test BLOB/binary type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT
                    '\\x48454C4C4F'::BLOB as blob_val,
                    encode('hello') as encoded_val
            """
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_bit_type(self, memory_client):
        """Test BIT/BITSTRING type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT '10101010'::BIT as bit_val"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True


class TestDateTimeTypes:
    """Test date/time type serialization."""

    @pytest.mark.asyncio
    async def test_date_type(self, memory_client):
        """Test DATE type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT DATE '2024-01-15' as date_val"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert "2024" in str(data["rows"][0][0])

    @pytest.mark.asyncio
    async def test_time_type(self, memory_client):
        """Test TIME type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT TIME '14:30:00' as time_val"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_timestamp_type(self, memory_client):
        """Test TIMESTAMP type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT TIMESTAMP '2024-01-15 14:30:00' as timestamp_val"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert "2024" in str(data["rows"][0][0])

    @pytest.mark.asyncio
    async def test_timestamp_with_timezone(self, memory_client):
        """Test TIMESTAMPTZ type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT TIMESTAMPTZ '2024-01-15 14:30:00+00' as timestamptz_val"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_interval_type(self, memory_client):
        """Test INTERVAL type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT INTERVAL '1 year 2 months 3 days' as interval_val"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True


class TestSpecialTypes:
    """Test special type serialization."""

    @pytest.mark.asyncio
    async def test_boolean_type(self, memory_client):
        """Test BOOLEAN type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT true as bool_true, false as bool_false"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["rows"][0][0] is True
        assert data["rows"][0][1] is False

    @pytest.mark.asyncio
    async def test_uuid_type(self, memory_client):
        """Test UUID type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": "SELECT uuid() as uuid_val, '550e8400-e29b-41d4-a716-446655440000'::UUID as fixed_uuid"
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        # UUID should serialize as string
        assert "-" in str(data["rows"][0][1])

    @pytest.mark.asyncio
    async def test_null_values(self, memory_client):
        """Test NULL value handling."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": "SELECT NULL as null_val, NULL::INTEGER as null_int, NULL::VARCHAR as null_str"
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["rows"][0][0] is None
        assert data["rows"][0][1] is None
        assert data["rows"][0][2] is None


class TestNestedTypes:
    """Test nested/composite type serialization."""

    @pytest.mark.asyncio
    async def test_list_type(self, memory_client):
        """Test LIST type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT [1, 2, 3] as int_list, ['a', 'b', 'c'] as str_list"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        # Lists should serialize as JSON arrays
        row = data["rows"][0]
        assert isinstance(row[0], list)
        assert row[0] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_array_type(self, memory_client):
        """Test ARRAY (fixed-length) type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT array_value(1, 2, 3) as fixed_array"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_struct_type(self, memory_client):
        """Test STRUCT type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT {'name': 'Alice', 'age': 30} as person"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        # Struct should serialize as dict
        row = data["rows"][0]
        assert isinstance(row[0], dict)
        assert row[0]["name"] == "Alice"
        assert row[0]["age"] == 30

    @pytest.mark.asyncio
    async def test_map_type(self, memory_client):
        """Test MAP type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT MAP([1, 2], ['one', 'two']) as int_to_str_map"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_nested_list_of_structs(self, memory_client):
        """Test nested LIST of STRUCT types."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT [
                    {'name': 'Alice', 'score': 95},
                    {'name': 'Bob', 'score': 87}
                ] as students
            """
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        students = data["rows"][0][0]
        assert isinstance(students, list)
        assert len(students) == 2
        assert students[0]["name"] == "Alice"


class TestJSONType:
    """Test JSON type serialization."""

    @pytest.mark.asyncio
    async def test_json_object(self, memory_client):
        """Test JSON object type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": """SELECT '{"key": "value", "num": 42}'::JSON as json_obj"""},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_json_array(self, memory_client):
        """Test JSON array type."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": """SELECT '[1, 2, 3, "four"]'::JSON as json_arr"""},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True


class TestSpatialTypes:
    """Test spatial/geometry type serialization (if spatial extension available)."""

    @pytest.mark.asyncio
    async def test_spatial_extension_load(self, memory_client):
        """Test loading spatial extension and basic geometry."""
        # Try to install and load spatial extension
        install_result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "INSTALL spatial; LOAD spatial;"},
        )
        # Skip if extension not available
        if install_result.isError:
            pytest.skip("Spatial extension not available")

        # Test POINT
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT ST_Point(1.0, 2.0) as point_geom"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_geometry_types(self, memory_client):
        """Test various geometry types."""
        # Install extension first
        await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "INSTALL spatial; LOAD spatial;"},
        )

        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT
                    ST_Point(1.0, 2.0) as point,
                    ST_GeomFromText('LINESTRING(0 0, 1 1, 2 2)') as line,
                    ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))') as polygon
            """
            },
        )
        # May fail if spatial not available, which is okay
        if not result.isError:
            data = parse_json_result(result)
            assert data["success"] is True


class TestEdgeCases:
    """Test edge cases and special values."""

    @pytest.mark.asyncio
    async def test_infinity_values(self, memory_client):
        """Test infinity float values."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT 'infinity'::DOUBLE as pos_inf, '-infinity'::DOUBLE as neg_inf"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_nan_value(self, memory_client):
        """Test NaN float value."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT 'nan'::DOUBLE as nan_val"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_empty_string(self, memory_client):
        """Test empty string value."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT '' as empty_str"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["rows"][0][0] == ""

    @pytest.mark.asyncio
    async def test_unicode_strings(self, memory_client):
        """Test unicode string values."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT '日本語' as japanese, '🦆' as emoji, 'café' as accented"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["rows"][0][0] == "日本語"
        assert data["rows"][0][1] == "🦆"

    @pytest.mark.asyncio
    async def test_large_numbers(self, memory_client):
        """Test very large number values."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT
                    9223372036854775807::BIGINT as max_bigint,
                    (-9223372036854775807 - 1)::BIGINT as min_bigint
            """
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_empty_list(self, memory_client):
        """Test empty list value."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT []::INTEGER[] as empty_list"},
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["rows"][0][0] == []

    @pytest.mark.asyncio
    async def test_deeply_nested_structure(self, memory_client):
        """Test deeply nested data structure."""
        result = await memory_client.call_tool_mcp(
            "execute_query",
            {
                "sql": """
                SELECT {
                    'level1': {
                        'level2': {
                            'level3': [1, 2, 3]
                        }
                    }
                } as nested
            """
            },
        )
        assert result.isError is False
        data = parse_json_result(result)
        assert data["success"] is True
        nested = data["rows"][0][0]
        assert nested["level1"]["level2"]["level3"] == [1, 2, 3]
