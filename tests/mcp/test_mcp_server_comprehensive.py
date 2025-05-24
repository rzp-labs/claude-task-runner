#!/usr/bin/env python3
"""
Comprehensive Tests for MCP Server Module

Testing all functionality of the MCP server module including:
- Main function and argument parsing
- Health check with various scenarios
- Server info retrieval
- Command execution (start, health, info, schema)
- Error handling and edge cases

This test file is designed to achieve high coverage of the mcp_server.py module.
"""

import argparse
import json
import os
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, call, ANY

from task_runner.mcp.mcp_server import (
    main, health_check, get_server_info, configure_logging, ensure_log_directory
)


class TestMCPServerInfo:
    """Tests for server info functions."""

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
        assert info["name"] == "Task Runner MCP Server"
        assert info["version"] == "0.1.0"
        assert "Claude" in info["description"]


class TestMCPServerHealth:
    """Tests for health check functionality."""
    
    @patch("platform.system")
    @patch("platform.python_version")
    @patch("task_runner.mcp.mcp_server.subprocess.run")
    def test_health_check_all_dependencies(self, mock_subprocess_run, mock_python_version, mock_system):
        """Test health check with all dependencies available."""
        # Mock platform info
        mock_system.return_value = "Darwin"
        mock_python_version.return_value = "3.10.0"
        
        # Mock subprocess for Claude CLI check
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "/usr/local/bin/claude\n"
        mock_subprocess_run.return_value = mock_process
        
        # Mock module imports
        with patch.dict("sys.modules", {
            "loguru": Mock(__version__="0.6.0"),
            "rich": Mock(__version__="13.0.0"),
            "typer": Mock(__version__="0.9.0"),
            "fastmcp": Mock(__version__="1.0.0")
        }):
            result = health_check()
            
            # Verify result structure and content
            assert result["status"] == "healthy"
            assert result["platform"] == "Darwin"
            assert result["python_version"] == "3.10.0"
            assert result["loguru_version"] == "0.6.0"
            assert result["rich_version"] == "13.0.0"
            assert result["typer_version"] == "0.9.0"
            assert result["fastmcp_available"] is True
            assert result["fastmcp_version"] == "1.0.0"
            assert result["claude_available"] is True
            assert "/usr/local/bin/claude" in result["claude_path"]
    
    @patch("platform.system")
    @patch("platform.python_version")
    @patch("task_runner.mcp.mcp_server.subprocess.run")
    def test_health_check_missing_fastmcp(self, mock_subprocess_run, mock_python_version, mock_system):
        """Test health check with FastMCP unavailable."""
        # Mock platform info
        mock_system.return_value = "Linux"
        mock_python_version.return_value = "3.9.0"
        
        # Mock subprocess for Claude CLI check
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "/usr/local/bin/claude\n"
        mock_subprocess_run.return_value = mock_process
        
        # Mock module imports with ImportError for fastmcp
        modules = {
            "loguru": Mock(__version__="0.6.0"),
            "rich": Mock(__version__="13.0.0"),
            "typer": Mock(__version__="0.9.0")
        }
        
        with patch.dict("sys.modules", modules):
            # Force ImportError for fastmcp
            with patch("builtins.__import__", side_effect=lambda name, *args, **kwargs: 
                       raise_import_error(name, modules)):
                result = health_check()
                
                # Verify result structure and content
                assert result["status"] == "healthy"  # Still healthy without fastmcp
                assert result["fastmcp_available"] is False
                assert result["fastmcp_version"] == "not installed"
    
    @patch("platform.system")
    @patch("platform.python_version")
    @patch("task_runner.mcp.mcp_server.subprocess.run")
    def test_health_check_claude_not_found(self, mock_subprocess_run, mock_python_version, mock_system):
        """Test health check with Claude CLI not found."""
        # Mock platform info
        mock_system.return_value = "Windows"
        mock_python_version.return_value = "3.8.0"
        
        # Mock subprocess for Claude CLI check (not found)
        mock_process = Mock()
        mock_process.returncode = 1  # Command failed, Claude not found
        mock_process.stdout = ""
        mock_subprocess_run.return_value = mock_process
        
        # Mock module imports
        with patch.dict("sys.modules", {
            "loguru": Mock(__version__="0.6.0"),
            "rich": Mock(__version__="13.0.0"),
            "typer": Mock(__version__="0.9.0"),
            "fastmcp": Mock(__version__="1.0.0")
        }):
            result = health_check()
            
            # Verify result structure and content
            assert result["status"] == "healthy"  # Still healthy without Claude
            assert result["claude_available"] is False
            assert result["claude_path"] == "not found"
    
    @patch("platform.system")
    @patch("platform.python_version")
    @patch("task_runner.mcp.mcp_server.subprocess.run")
    def test_health_check_claude_error(self, mock_subprocess_run, mock_python_version, mock_system):
        """Test health check with error checking for Claude CLI."""
        # Mock platform info
        mock_system.return_value = "Darwin"
        mock_python_version.return_value = "3.10.0"
        
        # Mock subprocess raising exception
        mock_subprocess_run.side_effect = Exception("Command error")
        
        # Mock module imports
        with patch.dict("sys.modules", {
            "loguru": Mock(__version__="0.6.0"),
            "rich": Mock(__version__="13.0.0"),
            "typer": Mock(__version__="0.9.0"),
            "fastmcp": Mock(__version__="1.0.0")
        }):
            result = health_check()
            
            # Verify result structure and content
            assert result["status"] == "healthy"  # Still healthy despite error
            assert result["claude_available"] is False
            assert result["claude_path"] == "error checking"
    
    def test_health_check_exception(self):
        """Test health check when an unexpected exception occurs."""
        # Mock to force exception
        with patch("platform.system", side_effect=Exception("Unexpected error")):
            result = health_check()
            
            # Verify result structure indicates unhealthy status
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Unexpected error" in result["error"]


class TestMCPServerMain:
    """Tests for the main function and command handling."""
    
    @pytest.fixture
    def mock_argparse(self):
        """Mock argparse to control command-line arguments."""
        with patch("task_runner.mcp.mcp_server.argparse.ArgumentParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Mock subparsers
            mock_subparsers = MagicMock()
            mock_parser.add_subparsers.return_value = mock_subparsers
            
            # Mock subcommand parsers
            mock_start_parser = MagicMock()
            mock_health_parser = MagicMock()
            mock_info_parser = MagicMock()
            mock_schema_parser = MagicMock()
            
            # Configure subparsers.add_parser() to return different parsers
            def add_parser_side_effect(command, **kwargs):
                if command == "start":
                    return mock_start_parser
                elif command == "health":
                    return mock_health_parser
                elif command == "info":
                    return mock_info_parser
                elif command == "schema":
                    return mock_schema_parser
                return MagicMock()
                
            mock_subparsers.add_parser.side_effect = add_parser_side_effect
            
            yield mock_parser, mock_start_parser, mock_health_parser, mock_info_parser, mock_schema_parser
    
    def test_main_no_command(self, mock_argparse):
        """Test main function with no command specified."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args with no command
        args = argparse.Namespace(command=None)
        mock_parser.parse_args.return_value = args
        
        # Execute main function
        result = main()
        
        # Verify behavior
        mock_parser.print_help.assert_called_once()
        assert result == 1  # Should return error code
    
    @patch("task_runner.mcp.mcp_server.configure_logging")
    @patch("task_runner.mcp.mcp_server.create_mcp_server")
    @patch("task_runner.mcp.mcp_server.logger")
    def test_main_start_command_success(self, mock_logger, mock_create_mcp, mock_configure_logging, mock_argparse):
        """Test main function with 'start' command (success case)."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'start' command
        args = argparse.Namespace(
            command="start",
            host="localhost",
            port=3000,
            debug=True
        )
        mock_parser.parse_args.return_value = args
        
        # Mock MCP server
        mock_mcp = Mock()
        mock_create_mcp.return_value = mock_mcp
        
        # Execute main function
        result = main()
        
        # Verify behavior
        mock_configure_logging.assert_called_once_with("DEBUG")
        mock_logger.info.assert_called()
        mock_create_mcp.assert_called_once()
        mock_mcp.run_server.assert_called_once_with(host="localhost", port=3000)
        assert result == 0  # Should return success code
    
    @patch("task_runner.mcp.mcp_server.configure_logging")
    @patch("task_runner.mcp.mcp_server.create_mcp_server")
    @patch("task_runner.mcp.mcp_server.logger")
    def test_main_start_command_create_failure(self, mock_logger, mock_create_mcp, mock_configure_logging, mock_argparse):
        """Test main function with 'start' command when MCP server creation fails."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'start' command
        args = argparse.Namespace(
            command="start",
            host="localhost",
            port=3000,
            debug=False
        )
        mock_parser.parse_args.return_value = args
        
        # Mock MCP server creation failure
        mock_create_mcp.return_value = None
        
        # Execute main function
        result = main()
        
        # Verify behavior
        mock_configure_logging.assert_called_once_with("INFO")
        mock_logger.error.assert_called_once()
        assert result == 1  # Should return error code
    
    @patch("task_runner.mcp.mcp_server.configure_logging")
    @patch("task_runner.mcp.mcp_server.create_mcp_server")
    @patch("task_runner.mcp.mcp_server.logger")
    def test_main_start_command_keyboard_interrupt(self, mock_logger, mock_create_mcp, mock_configure_logging, mock_argparse):
        """Test main function with 'start' command and KeyboardInterrupt."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'start' command
        args = argparse.Namespace(
            command="start",
            host="localhost",
            port=3000,
            debug=False
        )
        mock_parser.parse_args.return_value = args
        
        # Mock MCP server with KeyboardInterrupt
        mock_mcp = Mock()
        mock_create_mcp.return_value = mock_mcp
        mock_mcp.run_server.side_effect = KeyboardInterrupt()
        
        # Execute main function
        result = main()
        
        # Verify behavior
        mock_logger.info.assert_called_with("Server stopped by user")
        assert result == 0  # Should return success code for clean shutdown
    
    @patch("task_runner.mcp.mcp_server.configure_logging")
    @patch("task_runner.mcp.mcp_server.create_mcp_server")
    @patch("task_runner.mcp.mcp_server.logger")
    def test_main_start_command_exception(self, mock_logger, mock_create_mcp, mock_configure_logging, mock_argparse):
        """Test main function with 'start' command and unexpected exception."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'start' command
        args = argparse.Namespace(
            command="start",
            host="localhost",
            port=3000,
            debug=False
        )
        mock_parser.parse_args.return_value = args
        
        # Mock MCP server with exception
        mock_mcp = Mock()
        mock_create_mcp.return_value = mock_mcp
        mock_mcp.run_server.side_effect = Exception("Server error")
        
        # Execute main function
        result = main()
        
        # Verify behavior
        mock_logger.error.assert_called_once()
        assert "Server failed to start" in mock_logger.error.call_args[0][0]
        assert result == 1  # Should return error code
    
    @patch("task_runner.mcp.mcp_server.health_check")
    @patch("json.dumps")
    def test_main_health_command(self, mock_json_dumps, mock_health_check, mock_argparse):
        """Test main function with 'health' command."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'health' command
        args = argparse.Namespace(command="health")
        mock_parser.parse_args.return_value = args
        
        # Mock health check results
        mock_health_check.return_value = {"status": "healthy", "key": "value"}
        mock_json_dumps.return_value = '{"status": "healthy", "key": "value"}'
        
        # Execute main function
        with patch("builtins.print") as mock_print:
            result = main()
            
            # Verify behavior
            mock_health_check.assert_called_once()
            mock_json_dumps.assert_called_once_with({"status": "healthy", "key": "value"}, indent=2)
            mock_print.assert_called_once_with('{"status": "healthy", "key": "value"}')
            assert result == 0  # Should return success code
    
    @patch("task_runner.mcp.mcp_server.health_check")
    @patch("json.dumps")
    def test_main_health_command_unhealthy(self, mock_json_dumps, mock_health_check, mock_argparse):
        """Test main function with 'health' command and unhealthy status."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'health' command
        args = argparse.Namespace(command="health")
        mock_parser.parse_args.return_value = args
        
        # Mock health check results with unhealthy status
        mock_health_check.return_value = {"status": "unhealthy", "error": "Something is wrong"}
        mock_json_dumps.return_value = '{"status": "unhealthy", "error": "Something is wrong"}'
        
        # Execute main function
        with patch("builtins.print") as mock_print:
            result = main()
            
            # Verify behavior
            mock_health_check.assert_called_once()
            mock_json_dumps.assert_called_once_with({"status": "unhealthy", "error": "Something is wrong"}, indent=2)
            mock_print.assert_called_once_with('{"status": "unhealthy", "error": "Something is wrong"}')
            assert result == 1  # Should return error code for unhealthy status
    
    @patch("task_runner.mcp.mcp_server.get_server_info")
    @patch("json.dumps")
    def test_main_info_command(self, mock_json_dumps, mock_get_server_info, mock_argparse):
        """Test main function with 'info' command."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'info' command
        args = argparse.Namespace(command="info")
        mock_parser.parse_args.return_value = args
        
        # Mock server info results
        server_info = {
            "name": "Task Runner MCP Server",
            "version": "0.1.0",
            "description": "MCP server for running isolated Claude tasks"
        }
        mock_get_server_info.return_value = server_info
        mock_json_dumps.return_value = json.dumps(server_info)
        
        # Execute main function
        with patch("builtins.print") as mock_print:
            result = main()
            
            # Verify behavior
            mock_get_server_info.assert_called_once()
            mock_json_dumps.assert_called_once_with(server_info, indent=2)
            mock_print.assert_called_once()
            assert result == 0  # Should return success code
    
    @patch("task_runner.mcp.mcp_server.create_mcp_server")
    @patch("json.dumps")
    def test_main_schema_command_json(self, mock_json_dumps, mock_create_mcp, mock_argparse):
        """Test main function with 'schema' command and JSON output."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'schema' command with JSON flag
        args = argparse.Namespace(command="schema", json=True)
        mock_parser.parse_args.return_value = args
        
        # Mock MCP server and schema
        mock_mcp = Mock()
        mock_create_mcp.return_value = mock_mcp
        
        schema = {
            "functions": {
                "test_function": {
                    "description": "Test function",
                    "parameters": {
                        "properties": {
                            "param1": {"type": "string", "description": "Parameter 1"}
                        },
                        "required": ["param1"]
                    }
                }
            }
        }
        mock_mcp.get_schema.return_value = schema
        mock_json_dumps.return_value = json.dumps(schema, indent=2)
        
        # Execute main function
        with patch("builtins.print") as mock_print:
            result = main()
            
            # Verify behavior
            mock_create_mcp.assert_called_once()
            mock_mcp.get_schema.assert_called_once()
            mock_json_dumps.assert_called_once_with(schema, indent=2)
            mock_print.assert_called_once_with(json.dumps(schema, indent=2))
            assert result == 0  # Should return success code
    
    @patch("task_runner.mcp.mcp_server.create_mcp_server")
    def test_main_schema_command_text(self, mock_create_mcp, mock_argparse):
        """Test main function with 'schema' command and text output."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'schema' command without JSON flag
        args = argparse.Namespace(command="schema", json=False)
        mock_parser.parse_args.return_value = args
        
        # Mock MCP server and schema
        mock_mcp = Mock()
        mock_create_mcp.return_value = mock_mcp
        
        schema = {
            "functions": {
                "test_function": {
                    "description": "Test function",
                    "parameters": {
                        "properties": {
                            "param1": {"type": "string", "description": "Parameter 1"}
                        },
                        "required": ["param1"]
                    }
                }
            }
        }
        mock_mcp.get_schema.return_value = schema
        
        # Execute main function
        with patch("builtins.print") as mock_print:
            result = main()
            
            # Verify behavior
            mock_create_mcp.assert_called_once()
            mock_mcp.get_schema.assert_called_once()
            assert mock_print.call_count >= 3  # Should print multiple lines for text output
            assert result == 0  # Should return success code
    
    @patch("task_runner.mcp.mcp_server.create_mcp_server")
    def test_main_schema_command_error(self, mock_create_mcp, mock_argparse):
        """Test main function with 'schema' command when MCP server creation fails."""
        mock_parser, *_ = mock_argparse
        
        # Configure parser.parse_args() to return args for 'schema' command
        args = argparse.Namespace(command="schema", json=True)
        mock_parser.parse_args.return_value = args
        
        # Mock MCP server creation failure
        mock_create_mcp.return_value = None
        
        # Execute main function
        with patch("builtins.print") as mock_print:
            with patch("json.dumps") as mock_json_dumps:
                mock_json_dumps.return_value = '{"error": "Failed to create MCP server"}'
                result = main()
                
                # Verify behavior
                mock_create_mcp.assert_called_once()
                mock_json_dumps.assert_called_once_with({"error": "Failed to create MCP server"}, indent=2)
                mock_print.assert_called_once_with('{"error": "Failed to create MCP server"}')
                assert result == 1  # Should return error code


# Helper function for import error mocking
def raise_import_error(name, modules):
    """Raise ImportError for specified modules or return mock."""
    if name == "fastmcp":
        raise ImportError("No module named 'fastmcp'")
    elif name in modules:
        return modules[name]
    return None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
