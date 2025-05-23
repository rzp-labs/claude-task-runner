#!/usr/bin/env python3
"""Tests for MCP Server Module"""

from unittest.mock import Mock, patch
import pytest
from typer.testing import CliRunner

from task_runner.mcp.server import (
    app, configure_logging, get_server_info, health_check,
    health, info, schema, start
)


class TestServerFunctions:
    """Test server utility functions."""
    
    def test_configure_logging(self):
        """Test logging configuration."""
        with patch("task_runner.mcp.server.logger") as mock_logger:
            configure_logging("DEBUG")
            mock_logger.remove.assert_called_once()
            mock_logger.add.assert_called()
    
    def test_get_server_info(self):
        """Test server info retrieval."""
        info = get_server_info()
        assert info["name"] == "task-runner-mcp"
        assert "version" in info
        assert "description" in info
    
    def test_health_check(self):
        """Test health check."""
        result = health_check()
        assert result["status"] == "healthy"
        assert "server_info" in result


class TestCLICommands:
    """Test CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()
    
    def test_health_command(self, runner):
        """Test health command."""
        result = runner.invoke(app, ["health"])
        assert result.exit_code == 0
        assert "healthy" in result.output
    
    def test_info_command(self, runner):
        """Test info command."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "task-runner-mcp" in result.output
    
    def test_schema_command(self, runner):
        """Test schema command."""
        result = runner.invoke(app, ["schema"])
        assert result.exit_code == 0
        assert "functions" in result.output
    
    def test_schema_json(self, runner):
        """Test schema with JSON output."""
        result = runner.invoke(app, ["schema", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        import json
        json.loads(result.output)
    
    @patch("task_runner.mcp.server.uvicorn.run")
    def test_start_command(self, mock_run, runner):
        """Test start command."""
        result = runner.invoke(app, ["start"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        
        # Check default parameters
        call_args = mock_run.call_args[1]
        assert call_args["host"] == "localhost"
        assert call_args["port"] == 3000
    
    @patch("task_runner.mcp.server.uvicorn.run")
    def test_start_custom_params(self, mock_run, runner):
        """Test start with custom parameters."""
        result = runner.invoke(app, [
            "start", 
            "--host", "0.0.0.0",
            "--port", "8080",
            "--debug"
        ])
        assert result.exit_code == 0
        
        call_args = mock_run.call_args[1]
        assert call_args["host"] == "0.0.0.0"
        assert call_args["port"] == 8080
        assert call_args["log_level"] == "debug"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])