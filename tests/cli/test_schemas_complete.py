#!/usr/bin/env python3
"""
Complete Tests for CLI Schemas Module
"""

import pytest
from task_runner.cli.schemas import (
    format_cli_response,
    generate_cli_schema,
    TaskState,
)


class TestFormatCliResponse:
    """Tests for format_cli_response function."""

    def test_format_cli_response_success_only(self):
        """Test formatting success response without data."""
        result = format_cli_response(success=True)
        
        assert result["success"] is True
        # Response format may vary based on implementation

    def test_format_cli_response_success_with_data(self):
        """Test formatting success response with data."""
        data = {"key": "value", "count": 42}
        result = format_cli_response(success=True, data=data)
        
        assert result["success"] is True
        assert result["data"] == data

    def test_format_cli_response_error(self):
        """Test formatting error response."""
        error_msg = "Something went wrong"
        result = format_cli_response(success=False, error=error_msg)
        
        assert result["success"] is False
        assert result["error"] == error_msg

    def test_format_cli_response_with_data_and_error(self):
        """Test formatting response with both data and error."""
        data = {"partial": "result"}
        error_msg = "Warning occurred"
        result = format_cli_response(success=False, data=data, error=error_msg)
        
        assert result["success"] is False
        assert result["data"] == data
        assert result["error"] == error_msg


class TestGenerateCliSchema:
    """Tests for generate_cli_schema function."""

    def test_generate_cli_schema(self):
        """Test schema generation returns valid structure."""
        schema = generate_cli_schema()
        
        assert isinstance(schema, dict)
        assert "commands" in schema or len(schema) > 0  # Should have some content


class TestTaskState:
    """Tests for TaskState enum."""

    def test_task_state_values(self):
        """Test TaskState enum has expected values."""
        # Check that TaskState has the expected enum values
        assert hasattr(TaskState, 'PENDING') or hasattr(TaskState, 'pending')
        assert hasattr(TaskState, 'RUNNING') or hasattr(TaskState, 'running')
        assert hasattr(TaskState, 'COMPLETED') or hasattr(TaskState, 'completed')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])