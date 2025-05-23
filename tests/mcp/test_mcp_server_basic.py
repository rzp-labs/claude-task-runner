#!/usr/bin/env python3
"""
Basic Tests for MCP Server Module

Testing the basic functionality of the MCP server module.
"""

import pytest
from unittest.mock import patch, Mock
import sys

from task_runner.mcp.mcp_server import ensure_log_directory, configure_logging


class TestMCPServerUtils:
    """Tests for MCP server utility functions."""

    @patch('os.makedirs')
    def test_ensure_log_directory(self, mock_makedirs):
        """Test log directory creation."""
        ensure_log_directory()
        
        mock_makedirs.assert_called_once_with("logs", exist_ok=True)

    @patch('task_runner.mcp.mcp_server.logger')
    @patch('task_runner.mcp.mcp_server.ensure_log_directory')
    def test_configure_logging(self, mock_ensure_log, mock_logger):
        """Test logging configuration."""
        configure_logging("DEBUG")
        
        # Should ensure log directory exists
        mock_ensure_log.assert_called_once()
        
        # Should remove default handlers
        mock_logger.remove.assert_called()
        
        # Should add new handlers
        assert mock_logger.add.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])