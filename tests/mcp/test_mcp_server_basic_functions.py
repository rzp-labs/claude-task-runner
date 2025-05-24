#!/usr/bin/env python3
"""
Basic Tests for MCP Server Module

Testing the core functions of the MCP server module: configure_logging, get_server_info, and health_check.
This serves as a starting point for improving test coverage.
"""

import os
import json
from unittest.mock import patch, Mock

import pytest

from task_runner.mcp.mcp_server import (
    configure_logging,
    get_server_info,
    health_check,
    ensure_log_directory,
)


class TestMCPServerBasics:
    """Basic tests for MCP server functions."""

    @patch('task_runner.mcp.mcp_server.logger')
    def test_configure_logging_default(self, mock_logger):
        """Test logging configuration with default settings."""
        configure_logging()
        
        # Verify logger configuration
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count >= 2  # Should add at least file and stderr loggers
        
        # Check level was set to INFO by default
        for call_args in mock_logger.add.call_args_list:
            call_kwargs = call_args[1]
            if 'sys.stderr' in str(call_args) or 'stderr' in str(call_args):
                assert call_kwargs.get('level', '') == 'INFO'

    @patch('task_runner.mcp.mcp_server.logger')
    def test_configure_logging_debug(self, mock_logger):
        """Test logging configuration with debug level."""
        configure_logging(level="DEBUG")
        
        # Verify logger configuration
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count >= 2
        
        # Check level was set to DEBUG
        for call_args in mock_logger.add.call_args_list:
            call_kwargs = call_args[1]
            if 'sys.stderr' in str(call_args) or 'stderr' in str(call_args):
                assert call_kwargs.get('level', '') == 'DEBUG'

    @patch('os.makedirs')
    def test_ensure_log_directory(self, mock_makedirs):
        """Test log directory creation."""
        ensure_log_directory()
        
        mock_makedirs.assert_called_once_with("logs", exist_ok=True)

    def test_get_server_info(self):
        """Test retrieving server information."""
        info = get_server_info()
        
        # Verify structure and content
        assert isinstance(info, dict)
        assert "name" in info
        assert "version" in info
        assert "description" in info
        assert "author" in info
        assert "github" in info
        
        # Check specific values
        assert "Task Runner" in info["name"]
        assert isinstance(info["version"], str)
        assert len(info["version"]) > 0

    @patch("platform.system")
    @patch("platform.python_version")
    @patch("subprocess.run")
    def test_health_check_basic(self, mock_subprocess_run, mock_python_version, mock_system):
        """Test basic health check functionality."""
        # Mock platform info
        mock_system.return_value = "Linux"
        mock_python_version.return_value = "3.10.0"
        
        # Mock subprocess for Claude CLI check
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "/usr/local/bin/claude\n"
        mock_subprocess_run.return_value = mock_process
        
        # Mock imports to avoid ImportError during testing
        with patch.dict('sys.modules', {
            'loguru': Mock(__version__="0.6.0"),
            'rich': Mock(__version__="13.0.0"),
            'typer': Mock(__version__="0.9.0"),
            'fastmcp': Mock(__version__="1.0.0")
        }):
            # Run health check
            result = health_check()
            
            # Verify structure
            assert isinstance(result, dict)
            assert "status" in result
            assert result["status"] == "healthy"
            assert "platform" in result
            assert "python_version" in result
            assert "claude_available" in result
            assert result["claude_available"] is True

    @patch("platform.system")
    @patch("platform.python_version")
    @patch("subprocess.run")
    def test_health_check_no_claude(self, mock_subprocess_run, mock_python_version, mock_system):
        """Test health check when Claude CLI is not available."""
        # Mock platform info
        mock_system.return_value = "Windows"
        mock_python_version.return_value = "3.9.0"
        
        # Mock subprocess to indicate Claude not found
        mock_process = Mock()
        mock_process.returncode = 1  # Non-zero indicates failure
        mock_process.stdout = ""
        mock_subprocess_run.return_value = mock_process
        
        # Mock imports
        with patch.dict('sys.modules', {
            'loguru': Mock(__version__="0.6.0"),
            'rich': Mock(__version__="13.0.0"),
            'typer': Mock(__version__="0.9.0"),
            'fastmcp': Mock(__version__="1.0.0")
        }):
            # Run health check
            result = health_check()
            
            # Verify structure
            assert isinstance(result, dict)
            assert "status" in result
            assert result["status"] == "healthy"  # Should still be healthy even without Claude
            assert "claude_available" in result
            assert result["claude_available"] is False
            assert "claude_path" in result
            assert result["claude_path"] == "not found"

    @patch("platform.system")
    @patch("platform.python_version")
    @patch("subprocess.run")
    def test_health_check_missing_fastmcp(self, mock_subprocess_run, mock_python_version, mock_system):
        """Test health check when FastMCP is not installed."""
        # Mock platform info
        mock_system.return_value = "Darwin"
        mock_python_version.return_value = "3.10.0"
        
        # Mock subprocess for Claude CLI check
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "/usr/local/bin/claude\n"
        mock_subprocess_run.return_value = mock_process
        
        # Mock imports without fastmcp
        with patch.dict('sys.modules', {
            'loguru': Mock(__version__="0.6.0"),
            'rich': Mock(__version__="13.0.0"),
            'typer': Mock(__version__="0.9.0"),
        }):
            # Mock import to raise ImportError for fastmcp
            with patch("builtins.__import__", side_effect=lambda name, *args, **kwargs: 
                      raise_import_error(name, {
                          'loguru': Mock(__version__="0.6.0"),
                          'rich': Mock(__version__="13.0.0"),
                          'typer': Mock(__version__="0.9.0"),
                      })):
                result = health_check()
                
                # Verify structure
                assert isinstance(result, dict)
                assert "status" in result
                assert result["status"] == "healthy"  # Still healthy without fastmcp
                assert "fastmcp_available" in result
                assert result["fastmcp_available"] is False
                assert "fastmcp_version" in result
                assert result["fastmcp_version"] == "not installed"

    @patch("platform.system")
    def test_health_check_exception(self, mock_system):
        """Test health check when an exception occurs."""
        # Mock platform to raise an exception
        mock_system.side_effect = Exception("Test error")
        
        # Run health check
        result = health_check()
        
        # Verify error handling
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Test error" in result["error"]


# Helper function for testing import errors
def raise_import_error(name, modules):
    """Raise ImportError for specified modules or return mock."""
    if name == "fastmcp":
        raise ImportError("No module named 'fastmcp'")
    elif name in modules:
        return modules[name]
    return None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

