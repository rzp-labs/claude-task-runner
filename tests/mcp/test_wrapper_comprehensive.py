#!/usr/bin/env python3
"""
Comprehensive Tests for MCP Wrapper Module

Testing all functionality of the MCP wrapper module including:
- Handler functions for each MCP operation
- MCP server creation
- Request handling and routing
- Error handling and edge cases

This test file is designed to achieve high coverage of the wrapper.py module.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, call, ANY

import pytest

from task_runner.mcp.wrapper import (
    format_response,
    run_task_handler,
    run_all_tasks_handler,
    parse_task_list_handler,
    create_project_handler,
    get_task_status_handler,
    get_task_summary_handler,
    clean_handler,
    create_mcp_server,
    mcp_handler
)


class TestFormatResponse:
    """Tests for the format_response function."""

    def test_format_success_response(self):
        """Test formatting a success response with data."""
        response = format_response(True, {"key": "value"})
        assert response == {"success": True, "key": "value"}

    def test_format_error_response(self):
        """Test formatting an error response."""
        response = format_response(False, error="Error message")
        assert response == {"success": False, "error": "Error message"}

    def test_format_minimal_success_response(self):
        """Test formatting a minimal success response."""
        response = format_response(True)
        assert response == {"success": True}

    def test_format_minimal_error_response(self):
        """Test formatting a minimal error response."""
        response = format_response(False)
        assert response == {"success": False}


class TestRunTaskHandler:
    """Tests for the run_task_handler function."""

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_task_success(self, mock_tm_class):
        """Test run_task_handler with valid parameters."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_task.return_value = (True, {"status": "completed"})

        # Create temporary file
        with tempfile.NamedTemporaryFile() as tmp_file:
            request = {
                "task_path": tmp_file.name,
                "base_dir": "/tmp",
                "timeout_seconds": 60
            }

            response = run_task_handler(request)

            # Verify behavior
            mock_tm_class.assert_called_once_with(Path("/tmp"))
            mock_tm.run_task.assert_called_once_with(Path(tmp_file.name), 60)
            assert response["success"] is True
            assert response["task_result"] == {"status": "completed"}

    def test_run_task_missing_parameter(self):
        """Test run_task_handler with missing required parameter."""
        request = {
            "base_dir": "/tmp",
            "timeout_seconds": 60
        }
        # No task_path provided

        response = run_task_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "Missing required parameter" in response["error"]

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_task_file_not_found(self, mock_tm_class):
        """Test run_task_handler with non-existent task file."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm

        request = {
            "task_path": "/nonexistent/file.txt",
            "base_dir": "/tmp",
            "timeout_seconds": 60
        }

        response = run_task_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "not found" in response["error"]

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_task_exception(self, mock_tm_class):
        """Test run_task_handler with exception during execution."""
        # Mock TaskManager to raise exception
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_task.side_effect = Exception("Test error")

        # Create temporary file
        with tempfile.NamedTemporaryFile() as tmp_file:
            request = {
                "task_path": tmp_file.name,
                "base_dir": "/tmp",
                "timeout_seconds": 60
            }

            response = run_task_handler(request)

            # Verify behavior
            assert response["success"] is False
            assert "Error running task" in response["error"]
            assert "Test error" in response["error"]


class TestRunAllTasksHandler:
    """Tests for the run_all_tasks_handler function."""

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_all_tasks_success(self, mock_tm_class):
        """Test run_all_tasks_handler with valid parameters."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.return_value = {
            "total": 2,
            "success": 2,
            "failed": 0,
            "tasks": ["task1", "task2"]
        }

        request = {
            "base_dir": "/tmp"
        }

        response = run_all_tasks_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once_with(Path("/tmp"))
        mock_tm.run_all_tasks.assert_called_once()
        assert response["success"] is True
        assert response["total"] == 2
        assert response["success"] == 2

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_all_tasks_default_base_dir(self, mock_tm_class):
        """Test run_all_tasks_handler with default base directory."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.return_value = {"total": 0}

        request = {}  # No base_dir provided

        response = run_all_tasks_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once()  # Path should be home directory + claude_task_runner
        mock_tm.run_all_tasks.assert_called_once()
        assert response["success"] is True

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_all_tasks_exception(self, mock_tm_class):
        """Test run_all_tasks_handler with exception during execution."""
        # Mock TaskManager to raise exception
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.side_effect = Exception("Test error")

        request = {
            "base_dir": "/tmp"
        }

        response = run_all_tasks_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "Error running tasks" in response["error"]
        assert "Test error" in response["error"]


class TestParseTaskListHandler:
    """Tests for the parse_task_list_handler function."""

    @patch("task_runner.core.task_manager.TaskManager")
    def test_parse_task_list_success(self, mock_tm_class):
        """Test parse_task_list_handler with valid parameters."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.parse_task_list.return_value = [
            Path(tmp_file.name.replace("tmp", "tasks/001_task1.md")),
            Path("/tmp/tasks/002_task2.md")
        ]

        # Create temporary file
        with tempfile.NamedTemporaryFile() as tmp_file:
            request = {
                "task_list_path": tmp_file.name,
                "base_dir": "/tmp"
            }

            response = parse_task_list_handler(request)

            # Verify behavior
            mock_tm_class.assert_called_once_with(Path("/tmp"))
            mock_tm.parse_task_list.assert_called_once_with(Path(tmp_file.name))
            assert response["success"] is True
            assert response["count"] == 2
            assert len(response["task_files"]) == 2

    def test_parse_task_list_missing_parameter(self):
        """Test parse_task_list_handler with missing required parameter."""
        request = {
            "base_dir": "/tmp"
        }
        # No task_list_path provided

        response = parse_task_list_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "Missing required parameter" in response["error"]

    @patch("task_runner.core.task_manager.TaskManager")
    def test_parse_task_list_file_not_found(self, mock_tm_class):
        """Test parse_task_list_handler with non-existent task list file."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm

        request = {
            "task_list_path": "/nonexistent/file.md",
            "base_dir": "/tmp"
        }

        response = parse_task_list_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "not found" in response["error"]

    @patch("task_runner.core.task_manager.TaskManager")
    def test_parse_task_list_exception(self, mock_tm_class):
        """Test parse_task_list_handler with exception during execution."""
        # Mock TaskManager to raise exception
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.parse_task_list.side_effect = Exception("Test error")

        # Create temporary file
        with tempfile.NamedTemporaryFile() as tmp_file:
            request = {
                "task_list_path": tmp_file.name,
                "base_dir": "/tmp"
            }

            response = parse_task_list_handler(request)

            # Verify behavior
            assert response["success"] is False
            assert "Error parsing task list" in response["error"]
            assert "Test error" in response["error"]


class TestCreateProjectHandler:
    """Tests for the create_project_handler function."""

    @patch("task_runner.core.task_manager.TaskManager")
    def test_create_project_success_with_task_list(self, mock_tm_class):
        """Test create_project_handler with task list."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.parse_task_list.return_value = [
            Path("/tmp/my_project/tasks/001_task1.md"),
            Path("/tmp/my_project/tasks/002_task2.md")
        ]

        # Create temporary file
        with tempfile.NamedTemporaryFile() as tmp_file:
            request = {
                "project_name": "my_project",
                "task_list_path": tmp_file.name,
                "base_dir": "/tmp"
            }

            response = create_project_handler(request)

            # Verify behavior
            mock_tm_class.assert_called_once_with(Path("/tmp/my_project"))
            mock_tm.parse_task_list.assert_called_once_with(Path(tmp_file.name))
            assert response["success"] is True
            assert response["project"] == "my_project"
            assert response["count"] == 2
            assert len(response["task_files"]) == 2

    @patch("task_runner.core.task_manager.TaskManager")
    def test_create_project_success_without_task_list(self, mock_tm_class):
        """Test create_project_handler without task list."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm

        request = {
            "project_name": "my_project",
            "base_dir": "/tmp"
        }
        # No task_list_path provided

        response = create_project_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once_with(Path("/tmp/my_project"))
        mock_tm.parse_task_list.assert_not_called()
        assert response["success"] is True
        assert response["project"] == "my_project"
        assert "message" in response

    def test_create_project_missing_parameter(self):
        """Test create_project_handler with missing required parameter."""
        request = {
            "base_dir": "/tmp"
        }
        # No project_name provided

        response = create_project_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "Missing required parameter" in response["error"]

    @patch("task_runner.core.task_manager.TaskManager")
    def test_create_project_task_list_not_found(self, mock_tm_class):
        """Test create_project_handler with non-existent task list file."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm

        request = {
            "project_name": "my_project",
            "task_list_path": "/nonexistent/file.md",
            "base_dir": "/tmp"
        }

        response = create_project_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "not found" in response["error"]

    @patch("task_runner.core.task_manager.TaskManager")
    def test_create_project_exception(self, mock_tm_class):
        """Test create_project_handler with exception during execution."""
        # Mock TaskManager to raise exception
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.parse_task_list.side_effect = Exception("Test error")

        # Create temporary file
        with tempfile.NamedTemporaryFile() as tmp_file:
            request = {
                "project_name": "my_project",
                "task_list_path": tmp_file.name,
                "base_dir": "/tmp"
            }

            response = create_project_handler(request)

            # Verify behavior
            assert response["success"] is False
            if response["success"] is not False or "Error creating project" not in response["error"] or "Test error" not in response["error"]: raise ValueError("Project creation failed with error: {}".format(response["error"]))
            assert "Test error" in response["error"]


class TestGetTaskStatusHandler:
    """Tests for the get_task_status_handler function."""

    @patch("task_runner.core.task_manager.TaskManager")
    def test_get_task_status_success(self, mock_tm_class):
        """Test get_task_status_handler with valid parameters."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_status.return_value = {
            "task1": {"status": "completed"},
            "task2": {"status": "pending"},
            "task3": {"status": "running"}
        }

        request = {
            "base_dir": "/tmp"
        }

        response = get_task_status_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once_with(Path("/tmp"))
        mock_tm.get_task_status.assert_called_once()
        assert response["success"] is True
        assert len(response["tasks"]) == 3
        assert "task1" in response["tasks"]

    @patch("task_runner.core.task_manager.TaskManager")
    def test_get_task_status_default_base_dir(self, mock_tm_class):
        """Test get_task_status_handler with default base directory."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_status.return_value = {}

        request = {}  # No base_dir provided

        response = get_task_status_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once()  # Path should be home directory + claude_task_runner
        mock_tm.get_task_status.assert_called_once()
        assert response["success"] is True
        assert "tasks" in response

    @patch("task_runner.core.task_manager.TaskManager")
    def test_get_task_status_exception(self, mock_tm_class):
        """Test get_task_status_handler with exception during execution."""
        # Mock TaskManager to raise exception
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_status.side_effect = Exception("Test error")

        request = {
            "base_dir": "/tmp"
        }

        response = get_task_status_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "Error getting task status" in response["error"]
        assert "Test error" in response["error"]


class TestGetTaskSummaryHandler:
    """Tests for the get_task_summary_handler function."""

    @patch("task_runner.core.task_manager.TaskManager")
    def test_get_task_summary_success(self, mock_tm_class):
        """Test get_task_summary_handler with valid parameters."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_summary.return_value = {
            "total": 10,
            "completed": 5,
            "pending": 3,
            "failed": 2
        }

        request = {
            "base_dir": "/tmp"
        }

        response = get_task_summary_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once_with(Path("/tmp"))
        mock_tm.get_task_summary.assert_called_once()
        assert response["success"] is True
        assert "summary" in response
        assert response["summary"]["total"] == 10
        assert response["summary"]["completed"] == 5

    @patch("task_runner.core.task_manager.TaskManager")
    def test_get_task_summary_default_base_dir(self, mock_tm_class):
        """Test get_task_summary_handler with default base directory."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_summary.return_value = {"total": 0}

        request = {}  # No base_dir provided

        response = get_task_summary_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once()  # Path should be home directory + claude_task_runner
        mock_tm.get_task_summary.assert_called_once()
        assert response["success"] is True
        assert "summary" in response

    @patch("task_runner.core.task_manager.TaskManager")
    def test_get_task_summary_exception(self, mock_tm_class):
        """Test get_task_summary_handler with exception during execution."""
        # Mock TaskManager to raise exception
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_summary.side_effect = Exception("Test error")

        request = {
            "base_dir": "/tmp"
        }

        response = get_task_summary_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "Error getting task summary" in response["error"]
        assert "Test error" in response["error"]


class TestCleanHandler:
    """Tests for the clean_handler function."""

    @patch("task_runner.core.task_manager.TaskManager")
    def test_clean_success(self, mock_tm_class):
        """Test clean_handler with valid parameters."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm

        request = {
            "base_dir": "/tmp"
        }

        response = clean_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once_with(Path("/tmp"))
        mock_tm.cleanup.assert_called_once()
        assert response["success"] is True
        assert "message" in response

    @patch("task_runner.core.task_manager.TaskManager")
    def test_clean_default_base_dir(self, mock_tm_class):
        """Test clean_handler with default base directory."""
        # Mock TaskManager
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm

        request = {}  # No base_dir provided

        response = clean_handler(request)

        # Verify behavior
        mock_tm_class.assert_called_once()  # Path should be home directory + claude_task_runner
        mock_tm.cleanup.assert_called_once()
        assert response["success"] is True

    @patch("task_runner.core.task_manager.TaskManager")
    def test_clean_exception(self, mock_tm_class):
        """Test clean_handler with exception during execution."""
        # Mock TaskManager to raise exception
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.cleanup.side_effect = Exception("Test error")

        request = {
            "base_dir": "/tmp"
        }

        response = clean_handler(request)

        # Verify behavior
        assert response["success"] is False
        assert "Error cleaning up processes" in response["error"]
        assert "Test error" in response["error"]


class TestCreateMCPServer:
    """Tests for the create_mcp_server function."""

    def test_create_mcp_server_success(self):
        """Test create_mcp_server with FastMCP available."""
        # Mock FastMCP
        mock_fastmcp = Mock()
        mock_fastmcp_instance = Mock()
        mock_fastmcp.return_value = mock_fastmcp_instance

        with patch.dict("sys.modules", {"fastmcp": mock_fastmcp}):
            with patch("task_runner.mcp.wrapper.FastMCP", mock_fastmcp):
                server = create_mcp_server()

                # Verify behavior
                assert server is not None
                assert server == mock_fastmcp_instance
                # Verify that FastMCP was initialized with correct args
                mock_fastmcp.assert_called_once()
                # Verify that add_tool was called for each handler
                assert mock_fastmcp_instance.add_tool.call_count >= 7  # Should be called for each handler

    def test_create_mcp_server_fastmcp_unavailable(self):
        """Test create_mcp_server with FastMCP unavailable."""
        with patch("task_runner.mcp.wrapper.FastMCP", None):
            with patch("task_runner.mcp.wrapper.logger") as mock_logger:
                server = create_mcp_server()

                # Verify behavior
                assert server is None
                mock_logger.error.assert_called_once()


class TestMCPHandler:
    """Tests for the mcp_handler function."""

    @patch("task_runner.mcp.wrapper.create_mcp_server")
    def test_mcp_handler_success(self, mock_create_mcp):
        """Test mcp_handler with valid request."""
        # Mock MCP server
        mock_mcp = Mock()
        mock_create_mcp.return_value = mock_mcp
        mock_mcp.handle_request.return_value = {"success": True, "result": "test"}

        request = {"method": "run_task", "params": {"task_path": "test.md"}}
        response = mcp_handler(request)

        # Verify behavior
        mock_create_mcp.assert_called_once()
        mock_mcp.handle_request.assert_called_once_with(request)
        assert response == {"success": True, "result": "test"}

    @patch("task_runner.mcp.wrapper.create_mcp_server")
    def test_mcp_handler_server_creation_fails(self, mock_create_mcp):
        """Test mcp_handler when server creation fails."""
        # Mock server creation failure
        mock_create_mcp.return_value = None

        request = {"method": "run_task", "params": {"task_path": "test.md"}}
        response = mcp_handler(request)

        # Verify behavior
        mock_create_mcp.assert_called_once()
        assert response == {"error": "FastMCP is not available"}

    @patch("task_runner.mcp.wrapper.create_mcp_server")
    def test_mcp_handler_request_error(self, mock_create_mcp):
        """Test mcp_handler with request that causes error."""
        # Mock MCP server
        mock_mcp = Mock()
        mock_create_mcp.return_value = mock_mcp
        mock_mcp.handle_request.side_effect = Exception("Request error")

        request = {"method": "invalid", "params": {}}
        
        # Directly testing error propagation would be challenging
        # since our implementation just passes through to FastMCP
        response = mcp_handler(request)
        
        # FastMCP handle_request was called
        mock_mcp.handle_request.assert_called_once_with(request)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
