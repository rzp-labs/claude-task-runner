#!/usr/bin/env python3
"""
Basic Tests for MCP Wrapper Module

Testing the utility functions in the wrapper module.
"""

import pytest
from unittest.mock import Mock, patch

from task_runner.mcp.wrapper import format_response


class TestFormatResponse:
    """Tests for format_response function."""

    def test_format_response_success(self):
        """Test formatting successful response."""
        result = format_response(success=True, data={"result": "ok"})
        
        assert result["success"] is True
        assert result["result"] == "ok"  # Data is merged into response
        assert "error" not in result

    def test_format_response_error(self):
        """Test formatting error response."""
        result = format_response(success=False, error="Something went wrong")
        
        assert result["success"] is False
        assert result["error"] == "Something went wrong"

    def test_format_response_minimal(self):
        """Test minimal response format."""
        result = format_response(success=True)
        
        assert result["success"] is True
        assert len(result) == 1  # Only success key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])