#!/usr/bin/env python3
"""
Additional Coverage Tests for CLI App Module

This module provides additional test coverage for the CLI app module,
specifically targeting areas with low coverage as identified in the
coverage report:
- Lines 147, 169-180: Command validation and initialization
- Line 222: Reporting or command handling
- Lines 249-264: Command-specific functionality
- Lines 291-294, 298: Error handling or recovery
- Lines 372-378, 384: Validation or error handling
- Lines 415-420: Cleanup or resource management
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call, ANY

import pytest
import typer
from typer.testing import CliRunner

import task_runner.cli.app as app_module
from task_runner.cli.app import app, configure_task_runner, format_output
from task_runner.core.task_manager import TaskState


class TestConfigValidation:
    """Tests for configuration validation and edge cases."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @patch("task_runner.cli.app.validate_base_dir")
    def test_invalid_base_dir_characters(self, mock_validate_base_dir, runner):
        """Test validation for base directory with invalid characters."""
        # Mock the validation to fail with specific message
        mock_validate_base_dir.return_value = False
        
        result = runner.invoke(app, ["run", "--base-dir", "/path/with/invalid<chars>"])
        
        assert result.exit_code == 1
        assert "Invalid base directory" in result.output

    @patch("task_runner.cli.app.validate_timeout")
    def test_timeout_validation_edge_cases(self, mock_validate_timeout, runner):
        """Test timeout validation with edge cases."""
        # Set up the mock to fail
        mock_validate_timeout.return_value = False
        
        result = runner.invoke(app, ["run", "--timeout", "-1"])
        
        assert result.exit_code == 1
        assert "Invalid timeout" in result.output.lower()

    @patch("task_runner.cli.app.validate_json_output")
    def test_json_quiet_combination_validation(self, mock_validate_json, runner):
        """Test validation of JSON output with quiet mode."""
        # Mock the validation to fail
        mock_validate_json.return_value = False
        
        result = runner.invoke(app, ["run", "--json", "--quiet"])
        
        assert result.exit_code == 1
        assert "Cannot use" in result.output.lower()


class TestCommandSpecificFunctionality:
    """Tests for specific command functionality and error handling."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_task_manager(self):
        """Create a mock TaskManager."""
        with patch("task_runner.core.task_manager.TaskManager") as mock_tm_class:
            mock_tm = MagicMock()
            mock_tm_class.return_value = mock_tm
            
            # Set up default return values
            mock_tm.get_task_summary.return_value = {
                "total": 3,
                "pending": 1,
                "running": 0,
                "completed": 1,
                "failed": 1,
                "timeout": 0,
            }
            
            yield mock_tm_class, mock_tm

    @patch("task_runner.cli.app.validate_base_dir")
    @patch("task_runner.cli.app.validate_timeout")
    @patch("task_runner.cli.app.validate_json_output")
    def test_run_command_validation_chain(self, mock_validate_json, mock_validate_timeout, 
                                         mock_validate_base_dir, runner, mock_task_manager):
        """Test the validation chain for the run command (lines 169-180)."""
        # Set up all validations to pass
        mock_validate_base_dir.return_value = True
        mock_validate_timeout.return_value = True
        mock_validate_json.return_value = True
        
        mock_tm_class, mock_tm = mock_task_manager
        mock_tm.run_all_tasks.return_value = {
            "total": 3,
            "success": 2,
            "failed": 1,
        }
        
        result = runner.invoke(app, [
            "run",
            "--base-dir", "/custom/path",
            "--timeout", "120",
            "--json"
        ])
        
        # Verify all validations were called in sequence
        mock_validate_base_dir.assert_called_once()
        mock_validate_timeout.assert_called_once()
        mock_validate_json.assert_called_once()
        
        assert result.exit_code == 0
        # Since JSON output is enabled, we should have valid JSON in the output
        try:
            output_data = json.loads(result.output)
            assert "total" in output_data
            assert output_data["total"] == 3
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    @patch("task_runner.cli.app.validate_base_dir")
    def test_task_specific_execution(self, mock_validate_base_dir, runner, mock_task_manager):
        """Test running a specific task (lines 249-264)."""
        mock_validate_base_dir.return_value = True
        mock_tm_class, mock_tm = mock_task_manager
        
        # Create a test task file
        with tempfile.NamedTemporaryFile(suffix=".md") as tmp_file:
            # Set up the mock for run_task
            mock_tm.run_task.return_value = (True, {"status": "completed"})
            
            result = runner.invoke(app, [
                "run",
                "--task", tmp_file.name,
                "--base-dir", "/custom/path"
            ])
            
            # Verify the correct method was called
            mock_tm.run_task.assert_called_once()
            assert result.exit_code == 0
            assert "completed" in result.output.lower()

    @patch("task_runner.cli.app.validate_base_dir")
    def test_task_specific_execution_failure(self, mock_validate_base_dir, runner, mock_task_manager):
        """Test running a specific task that fails (lines 249-264)."""
        mock_validate_base_dir.return_value = True
        mock_tm_class, mock_tm = mock_task_manager
        
        # Create a test task file
        with tempfile.NamedTemporaryFile(suffix=".md") as tmp_file:
            # Set up the mock for run_task to return failure
            mock_tm.run_task.return_value = (False, {"status": "failed", "error": "Test error"})
            
            result = runner.invoke(app, [
                "run",
                "--task", tmp_file.name,
                "--base-dir", "/custom/path"
            ])
            
            # Verify the correct method was called
            mock_tm.run_task.assert_called_once()
            assert result.exit_code == 1  # Should exit with error code
            assert "failed" in result.output.lower()
            assert "test error" in result.output.lower()

    @patch("task_runner.cli.app.validate_base_dir")
    def test_task_file_not_found(self, mock_validate_base_dir, runner):
        """Test running a specific task that doesn't exist (lines 249-264)."""
        mock_validate_base_dir.return_value = True
        
        result = runner.invoke(app, [
            "run",
            "--task", "/path/to/nonexistent/task.md",
            "--base-dir", "/custom/path"
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "does not exist" in result.output.lower()


class TestErrorHandlingAndRecovery:
    """Tests for error handling and recovery mechanisms."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @patch("task_runner.core.task_manager.TaskManager")
    @patch("task_runner.cli.app.validate_base_dir")
    def test_unknown_exception_handling(self, mock_validate_base_dir, mock_tm_class, runner):
        """Test handling of unknown exceptions (lines 291-294, 298)."""
        mock_validate_base_dir.return_value = True
        
        # Mock TaskManager to raise an unexpected exception
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.side_effect = ValueError("Unexpected test error")
        
        result = runner.invoke(app, ["run", "--base-dir", "/custom/path"])
        
        assert result.exit_code == 1
        assert "error" in result.output.lower()
        assert "unexpected test error" in result.output.lower()

    @patch("task_runner.core.task_manager.TaskManager")
    @patch("task_runner.cli.app.validate_base_dir")
    def test_no_tasks_error_handling(self, mock_validate_base_dir, mock_tm_class, runner):
        """Test handling when no tasks are found."""
        mock_validate_base_dir.return_value = True
        
        # Mock TaskManager to return an error about no tasks
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.return_value = {
            "success": False,
            "error": "No task files found in directory"
        }
        
        result = runner.invoke(app, ["run", "--base-dir", "/custom/path"])
        
        assert result.exit_code == 1
        assert "no task files found" in result.output.lower()

    @patch("task_runner.core.task_manager.TaskManager")
    @patch("task_runner.cli.app.validate_base_dir")
    def test_resource_error_handling(self, mock_validate_base_dir, mock_tm_class, runner):
        """Test handling of resource-related errors."""
        mock_validate_base_dir.return_value = True
        
        # Mock TaskManager to raise an IOError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.side_effect = IOError("Permission denied")
        
        result = runner.invoke(app, ["run", "--base-dir", "/custom/path"])
        
        assert result.exit_code == 1
        assert "error" in result.output.lower()
        assert "permission denied" in result.output.lower()


class TestEdgeCasesAndValidation:
    """Tests for edge cases and validation mechanisms."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_invalid_base_dir_format(self, runner):
        """Test with base directory in invalid format (lines 372-378)."""
        # This should trigger validation error handling
        result = runner.invoke(app, ["run", "--base-dir", ""])
        
        assert result.exit_code == 1
        assert "invalid" in result.output.lower() or "error" in result.output.lower()

    def test_invalid_command_output_format(self, runner):
        """Test with invalid output format specification (line 384)."""
        # This combination should trigger validation logic
        result = runner.invoke(app, ["run", "--json", "--output", "invalid_format"])
        
        assert result.exit_code == 1
        assert "invalid" in result.output.lower() or "error" in result.output.lower()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_cleanup_resource_handling(self, mock_tm_class, runner):
        """Test resource cleanup handling (lines 415-420)."""
        # Mock TaskManager to test cleanup behavior
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # First ensure the command succeeds
        mock_tm.cleanup.return_value = True
        
        result = runner.invoke(app, ["clean", "--force"])
        
        assert result.exit_code == 0
        assert mock_tm.cleanup.called
        
        # Now test failure case
        mock_tm.cleanup.side_effect = Exception("Cleanup failed")
        
        result = runner.invoke(app, ["clean", "--force"])
        
        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "error" in result.output.lower()


class TestMainFunctionality:
    """Tests for main function and overall application behavior."""

    @patch("sys.argv", ["task-runner"])
    @patch("typer.main.get_command")
    @patch("sys.exit")
    def test_main_function_no_command(self, mock_exit, mock_get_command):
        """Test main function with no command specified."""
        # Mock the Typer command to return help
        mock_command = Mock()
        mock_get_command.return_value = mock_command
        mock_command.return_value = 0
        
        app_module.main()
        
        # Help should have been displayed, no exit
        mock_exit.assert_not_called()
        
    @patch("sys.argv", ["task-runner", "invalid"])
    @patch("typer.main.get_command")
    @patch("sys.exit")
    def test_main_function_invalid_command(self, mock_exit, mock_get_command):
        """Test main function with invalid command."""
        # Mock the Typer command to return error
        mock_command = Mock()
        mock_get_command.return_value = mock_command
        mock_command.return_value = 2
        
        app_module.main()
        
        # Should exit with error code
        mock_exit.assert_called_with(2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

