#!/usr/bin/env python3
"""
Tests for MCP Server Module

This module tests the MCP server functionality.

Test Coverage Target: 50%+
"""

from unittest.mock import Mock, patch, MagicMock

import pytest

from task_runner.mcp.mcp_server import (
    list_tools,
    call_tool,
    TaskRunnerServer,
)


class TestMCPServer:
    """Tests for MCP server functionality."""

    def test_list_tools(self):
        """Test listing available tools."""
        tools = list_tools()
        
        # Should return a list of tools
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    @patch("task_runner.mcp.mcp_server.TaskManager")
    def test_call_tool_run_tasks(self, mock_tm_class):
        """Test calling the run_tasks tool."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.return_value = {
            "total": 3,
            "success": 2,
            "failed": 1,
        }
        
        # Test with minimal arguments
        result = call_tool("run_tasks", {})
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["total"] == 3

    @patch("task_runner.mcp.mcp_server.TaskManager")
    def test_call_tool_run_tasks_with_options(self, mock_tm_class):
        """Test calling run_tasks with options."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
        }
        
        # Test with all options
        result = call_tool("run_tasks", {
            "base_dir": "/tmp/test",
            "timeout": 600,
            "streaming": True,
            "skip_permissions": True,
        })
        
        assert result["success"] is True
        mock_tm.run_all_tasks.assert_called_once_with(
            timeout_seconds=600,
            fast_mode=False,
            demo_mode=True,
            use_streaming=True,
            skip_permissions=True,
        )

    @patch("task_runner.mcp.mcp_server.TaskManager")
    def test_call_tool_get_status(self, mock_tm_class):
        """Test calling the get_status tool."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_summary.return_value = {
            "total": 5,
            "completed": 3,
            "failed": 1,
            "pending": 1,
        }
        mock_tm.get_task_status.return_value = {
            "task1": {"status": "completed"},
            "task2": {"status": "failed"},
        }
        
        result = call_tool("get_status", {})
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["summary"]["total"] == 5

    @patch("task_runner.mcp.mcp_server.TaskManager")
    def test_call_tool_parse_tasks(self, mock_tm_class):
        """Test calling the parse_tasks tool."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.parse_task_list.return_value = [
            "/tmp/tasks/001_task.md",
            "/tmp/tasks/002_task.md",
        ]
        
        result = call_tool("parse_tasks", {
            "task_list_path": "/tmp/tasks.md"
        })
        
        assert result["success"] is True
        assert len(result["data"]["created_files"]) == 2

    def test_call_tool_unknown(self):
        """Test calling an unknown tool."""
        result = call_tool("unknown_tool", {})
        
        assert result["success"] is False
        assert "error" in result

    def test_task_runner_server_init(self):
        """Test TaskRunnerServer initialization."""
        server = TaskRunnerServer()
        
        assert server.name == "task-runner"
        assert hasattr(server, "list_tools")
        assert hasattr(server, "call_tool")


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])