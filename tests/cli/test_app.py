#!/usr/bin/env python3
"""
Tests for CLI App Module

This module tests the CLI application functionality including:
- Command execution (run, status, create, clean)
- Parameter validation
- Error handling
- Output formatting

Test Coverage Target: 90%+
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from typer.testing import CliRunner

# Import the module directly to access TaskManager for patching
import task_runner.cli.app as app_module
from task_runner.cli import app
from task_runner.core.task_manager import TaskState


class TestCLICommands:
    """Tests for CLI commands."""

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
            mock_tm.get_task_status.return_value = {
                "task1": {"status": TaskState.COMPLETED},
                "task2": {"status": TaskState.FAILED},
                "task3": {"status": TaskState.PENDING},
            }
            mock_tm.run_all_tasks.return_value = {
                "total": 3,
                "success": 2,
                "failed": 1,
                "task_results": {},
            }
            
            yield mock_tm_class, mock_tm

    def test_run_command_default(self, runner, mock_task_manager):
        """Test run command with default parameters."""
        mock_tm_class, mock_tm = mock_task_manager
        
        result = runner.invoke(app, ["run"])
        
        # Print output for debugging
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        
        assert result.exit_code == 0
        mock_tm_class.assert_called_once()
        mock_tm.run_all_tasks.assert_called_once_with(
            timeout_seconds=300,
            fast_mode=False,
            demo_mode=True,
            use_streaming=False,
            skip_permissions=False,
        )

    def test_run_command_with_base_dir(self, runner, mock_task_manager):
        """Test run command with custom base directory."""
        mock_tm_class, mock_tm = mock_task_manager
        
        result = runner.invoke(app, ["run", "--base-dir", "/custom/path"])
        
        assert result.exit_code == 0
        mock_tm_class.assert_called_once_with(Path("/custom/path"))

    def test_run_command_all_options(self, runner, mock_task_manager):
        """Test run command with all options."""
        mock_tm_class, mock_tm = mock_task_manager
        
        result = runner.invoke(app, [
            "run",
            "--base-dir", "/custom/path",
            "--timeout", "600",
            "--fast-mode",
            "--real-mode",
            "--streaming",
            "--skip-permissions",
            "--quiet",
            "--json",
        ])
        
        assert result.exit_code == 0
        mock_tm.run_all_tasks.assert_called_once_with(
            timeout_seconds=600,
            fast_mode=True,
            demo_mode=False,
            use_streaming=True,
            skip_permissions=True,
        )

    def test_run_command_no_tasks(self, runner, mock_task_manager):
        """Test run command when no tasks are found."""
        mock_tm_class, mock_tm = mock_task_manager
        mock_tm.run_all_tasks.return_value = {
            "success": False,
            "error": "No task files found",
        }
        
        result = runner.invoke(app, ["run"])
        
        assert result.exit_code == 1
        assert "No task files found" in result.output

    @patch("task_runner.cli.app.validate_timeout")
    def test_run_command_invalid_timeout(self, mock_validate, runner):
        """Test run command with invalid timeout."""
        mock_validate.return_value = False
        
        result = runner.invoke(app, ["run", "--timeout", "-1"])
        
        assert result.exit_code == 1

    def test_status_command(self, runner, mock_task_manager):
        """Test status command."""
        mock_tm_class, mock_tm = mock_task_manager
        
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        mock_tm.get_task_summary.assert_called_once()
        mock_tm.get_task_status.assert_called_once()

    def test_status_command_json(self, runner, mock_task_manager):
        """Test status command with JSON output."""
        mock_tm_class, mock_tm = mock_task_manager
        
        result = runner.invoke(app, ["status", "--json"])
        
        assert result.exit_code == 0
        # Output should be valid JSON
        output_data = json.loads(result.output)
        assert "summary" in output_data
        assert "tasks" in output_data

    def test_create_command(self, runner, mock_task_manager, tmp_path):
        """Test create command."""
        mock_tm_class, mock_tm = mock_task_manager
        
        # Create a test task list file
        task_list = tmp_path / "tasks.md"
        task_list.write_text("## Task 1: Test\nTest task")
        
        mock_tm.parse_task_list.return_value = [
            tmp_path / "tasks" / "001_test.md"
        ]
        
        result = runner.invoke(app, [
            "create",
            "--base-dir", str(tmp_path),
            "--task-list", str(task_list),
        ])
        
        assert result.exit_code == 0
        mock_tm.parse_task_list.assert_called_once_with(task_list)

    def test_create_command_no_file(self, runner, tmp_path):
        """Test create command with non-existent file."""
        result = runner.invoke(app, [
            "create",
            "--base-dir", str(tmp_path),
            "--task-list", "/non/existent/file.md",
        ])
        
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_clean_command_confirm(self, runner, mock_task_manager, tmp_path):
        """Test clean command with confirmation."""
        mock_tm_class, mock_tm = mock_task_manager
        
        # Create some test files
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "test.result").write_text("result")
        (tmp_path / "task_state.json").write_text("{}")
        
        # Simulate user confirmation
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(tmp_path),
        ], input="y\n")
        
        assert result.exit_code == 0
        # Files should be deleted
        assert not (results_dir / "test.result").exists()
        assert not (tmp_path / "task_state.json").exists()

    def test_clean_command_no_confirm(self, runner, tmp_path, mock_task_manager):
        """Test clean command basic functionality."""
        # Setup directories
        (tmp_path / "tasks").mkdir()
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "test.result").write_text("result")
        
        mock_tm_class, mock_tm = mock_task_manager
        
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(tmp_path),
        ])
        
        assert result.exit_code == 0
        # Clean only affects processes, not files
        assert (results_dir / "test.result").exists()
        mock_tm.cleanup.assert_called_once()

    def test_clean_command_force(self, runner, tmp_path, mock_task_manager):
        """Test clean command with JSON output."""
        # Setup directories
        (tmp_path / "tasks").mkdir()
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "test.result").write_text("result")
        
        mock_tm_class, mock_tm = mock_task_manager
        
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(tmp_path),
            "--json",
        ])
        
        assert result.exit_code == 0
        assert '"success": true' in result.output
        mock_tm.cleanup.assert_called_once()


class TestErrorHandling:
    """Tests for error handling in CLI."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_keyboard_interrupt_handling(self, mock_tm_class, runner):
        """Test handling of keyboard interrupt."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(app, ["run"])
        
        assert result.exit_code == 130
        assert "interrupted" in result.output.lower()
        mock_tm.cleanup.assert_called_once()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_exception_handling(self, mock_tm_class, runner):
        """Test handling of unexpected exceptions."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.side_effect = Exception("Test error")
        
        result = runner.invoke(app, ["run"])
        
        assert result.exit_code == 1
        assert "error" in result.output.lower()

    @patch("sys.exit")
    def test_main_function(self, mock_exit):
        """Test the main() function."""
        from task_runner.cli.app import main
        
        with patch("typer.main.get_command") as mock_get_command:
            mock_command = Mock()
            mock_get_command.return_value = mock_command
            
            # Simulate successful execution
            mock_command.return_value = 0
            main()
            mock_exit.assert_not_called()
            
            # Simulate error
            mock_command.return_value = 1
            main()
            mock_exit.assert_called_with(1)


class TestOutputFormatting:
    """Tests for output formatting options."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_quiet_mode(self, mock_tm_class, runner):
        """Test quiet mode suppresses info messages."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
        }
        
        result = runner.invoke(app, ["run", "--quiet"])
        
        assert result.exit_code == 0
        # Should have minimal output
        assert len(result.output.strip()) < 100

    @patch("task_runner.core.task_manager.TaskManager")
    def test_json_output_run(self, mock_tm_class, runner):
        """Test JSON output for run command."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.return_value = {
            "total": 3,
            "success": 2,
            "failed": 1,
            "task_results": {
                "task1": {"status": "completed"},
                "task2": {"status": "failed"},
            }
        }
        
        result = runner.invoke(app, ["run", "--json"])
        
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert data["total"] == 3
        assert data["success"] == 2


class TestValidation:
    """Tests for input validation."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_invalid_base_dir(self, runner):
        """Test with invalid base directory."""
        with patch("task_runner.cli.app.validate_base_dir", return_value=False):
            result = runner.invoke(app, ["run", "--base-dir", ""])
            assert result.exit_code == 1

    def test_invalid_timeout(self, runner):
        """Test with invalid timeout value."""
        result = runner.invoke(app, ["run", "--timeout", "0"])
        assert result.exit_code == 1
        assert "timeout must be positive" in result.output.lower()

    def test_invalid_json_flag_combinations(self, runner):
        """Test invalid combinations with JSON flag."""
        with patch("task_runner.cli.app.validate_json_output", return_value=False):
            result = runner.invoke(app, ["run", "--json", "--quiet"])
            assert result.exit_code == 1


class TestSpecialCases:
    """Tests for special cases and edge conditions."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_empty_results_handling(self, mock_tm_class, runner):
        """Test handling of empty results."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_status.return_value = {}
        mock_tm.get_task_summary.return_value = {
            "total": 0,
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "timeout": 0,
        }
        
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "no tasks" in result.output.lower()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_large_task_count(self, mock_tm_class, runner):
        """Test handling of many tasks."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Create 100 tasks
        large_task_status = {
            f"task{i}": {"status": TaskState.COMPLETED}
            for i in range(100)
        }
        mock_tm.get_task_status.return_value = large_task_status
        mock_tm.get_task_summary.return_value = {
            "total": 100,
            "completed": 100,
            "pending": 0,
            "running": 0,
            "failed": 0,
            "timeout": 0,
        }
        
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "100" in result.output


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])