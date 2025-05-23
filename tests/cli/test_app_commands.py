#!/usr/bin/env python3
"""
Comprehensive Tests for CLI App Commands

This module tests each CLI command with proper mocking to achieve high coverage.

Test Coverage Target: Cover the untested lines in cli/app.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from task_runner.cli import app


class TestRunCommand:
    """Tests for the run command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create directories
            (base_path / "tasks").mkdir()
            (base_path / "results").mkdir()
            
            # Create sample tasks
            task1 = base_path / "tasks" / "001_test.md"
            task1.write_text("# Test Task 1\nThis is a test task.")
            
            task2 = base_path / "tasks" / "002_test.md"
            task2.write_text("# Test Task 2\nThis is another test task.")
            
            # Create a task list file
            task_list = base_path / "task_list.md"
            task_list.write_text("- Task 1\n- Task 2\n")
            
            yield base_path

    def test_run_demo_mode(self, runner, temp_project):
        """Test successful run in demo mode."""
        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--quick-demo",
        ])

        assert result.exit_code == 0
        assert "Run Summary" in result.output

    def test_run_with_task_list(self, runner, temp_project):
        """Test run with task list parsing in demo mode."""
        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--task-list", str(temp_project / "task_list.md"),
            "--quick-demo",
        ])

        assert result.exit_code == 0
        assert "Created 2 task files" in result.output

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_single_task(self, mock_manager_class, runner, temp_project):
        """Test running a single task."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_task.return_value = (True, {"status": "completed"})

        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--single-task", "001_test.md",
        ])

        assert result.exit_code == 0
        assert mock_manager.run_task.called

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_json_output(self, mock_manager_class, runner, temp_project):
        """Test run with JSON output."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_all_tasks.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
            "task_results": {"001_test": {"status": "completed"}},
        }

        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--json",
        ])

        assert result.exit_code == 0
        # Verify JSON output
        output_data = json.loads(result.output)
        assert output_data["total"] == 1
        assert output_data["success"] == 1

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_with_failures(self, mock_manager_class, runner, temp_project):
        """Test run with some task failures."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_all_tasks.return_value = {
            "total": 2,
            "success": 1,
            "failed": 1,
            "task_results": {
                "001_test": {"status": "completed"},
                "002_test": {"status": "failed", "error": "Test error"},
            },
        }

        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
        ])

        assert result.exit_code == 1  # Should fail when tasks fail
        assert mock_manager.run_all_tasks.called

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_with_claude_path(self, mock_manager_class, runner, temp_project):
        """Test run with custom Claude path."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_all_tasks.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
            "task_results": {},
        }

        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--claude-path", "/custom/path/to/claude",
        ])

        assert result.exit_code == 0
        assert mock_manager.claude_path == "/custom/path/to/claude"

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_with_process_pool_options(self, mock_manager_class, runner, temp_project):
        """Test run with process pool configuration."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_all_tasks.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
            "task_results": {},
        }

        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--pool-size", "4",
            "--reuse-context",
        ])

        assert result.exit_code == 0
        # Verify logging was called with pool info
        assert "process pool" in result.output.lower()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_no_pool(self, mock_manager_class, runner, temp_project):
        """Test run with process pooling disabled."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_all_tasks.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
            "task_results": {},
        }

        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--no-pool",
        ])

        assert result.exit_code == 0
        assert "pooling disabled" in result.output.lower()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_task_list_not_found(self, mock_manager_class, runner, temp_project):
        """Test run with missing task list file."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--task-list", str(temp_project / "missing.md"),
        ])

        assert result.exit_code == 1
        assert "Task list file not found" in result.output

    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_with_exception(self, mock_manager_class, runner, temp_project):
        """Test run with unexpected exception."""
        # Set up mock to raise exception
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_all_tasks.side_effect = Exception("Unexpected error")

        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
        ])

        assert result.exit_code == 1
        assert mock_manager.cleanup.called


class TestStatusCommand:
    """Tests for the status command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @patch("task_runner.core.task_manager.TaskManager")
    def test_status_basic(self, mock_manager_class, runner):
        """Test basic status command."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_task_status.return_value = {
            "001_test": {"status": "completed", "name": "Test Task 1"},
            "002_test": {"status": "pending", "name": "Test Task 2"},
        }
        mock_manager.get_task_summary.return_value = {
            "total": 2,
            "pending": 1,
            "running": 0,
            "completed": 1,
            "failed": 0,
            "timeout": 0,
        }
        mock_manager.current_task = None
        mock_manager.current_task_start_time = None

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "Task Status" in result.output

    @patch("task_runner.core.task_manager.TaskManager")
    def test_status_json_output(self, mock_manager_class, runner):
        """Test status with JSON output."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_task_status.return_value = {
            "001_test": {"status": "completed"},
        }
        mock_manager.get_task_summary.return_value = {
            "total": 1,
            "completed": 1,
        }

        result = runner.invoke(app, ["status", "--json"])

        assert result.exit_code == 0
        # Verify JSON output
        output_data = json.loads(result.output)
        assert "tasks" in output_data
        assert "summary" in output_data


class TestCreateCommand:
    """Tests for the create command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @patch("task_runner.core.task_manager.TaskManager")
    def test_create_with_task_list(self, mock_manager_class, runner, temp_dir):
        """Test creating project with task list."""
        # Create task list file
        task_list = temp_dir / "tasks.md"
        task_list.write_text("- Task 1\n- Task 2\n")

        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.parse_task_list.return_value = [
            Path("tasks/001_task1.md"),
            Path("tasks/002_task2.md"),
        ]

        result = runner.invoke(app, [
            "create",
            "test_project",
            str(task_list),
            "--base-dir", str(temp_dir),
        ])

        assert result.exit_code == 0
        assert "Project 'test_project' created" in result.output
        assert mock_manager.parse_task_list.called

    @patch("task_runner.core.task_manager.TaskManager")
    def test_create_without_task_list(self, mock_manager_class, runner, temp_dir):
        """Test creating project without task list."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(app, [
            "create",
            "test_project",
            "--base-dir", str(temp_dir),
        ])

        assert result.exit_code == 0
        assert "Project 'test_project' created" in result.output

    @patch("task_runner.core.task_manager.TaskManager")
    def test_create_json_output(self, mock_manager_class, runner, temp_dir):
        """Test create with JSON output."""
        # Set up mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(app, [
            "create",
            "test_project",
            "--base-dir", str(temp_dir),
            "--json",
        ])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["success"] is True
        assert output_data["project"] == "test_project"

    def test_create_missing_task_list(self, runner, temp_dir):
        """Test create with missing task list file."""
        result = runner.invoke(app, [
            "create",
            "test_project",
            str(temp_dir / "missing.md"),
            "--base-dir", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "Task list file not found" in result.output


class TestCleanCommand:
    """Tests for the clean command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create directories
            (base_path / "tasks").mkdir()
            results_dir = base_path / "results"
            results_dir.mkdir()
            
            # Create some result files
            (results_dir / "result1.txt").write_text("Result 1")
            (results_dir / "result2.txt").write_text("Result 2")
            
            yield base_path

    def test_clean_with_confirmation(self, runner, temp_project):
        """Test clean command with user confirmation."""
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(temp_project),
        ], input="y\n")  # User confirms

        assert result.exit_code == 0
        assert "Results cleaned successfully" in result.output
        # Check that results were deleted
        assert not list((temp_project / "results").glob("*.txt"))

    def test_clean_abort(self, runner, temp_project):
        """Test clean command when user aborts."""
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(temp_project),
        ], input="n\n")  # User aborts

        assert result.exit_code == 1
        assert "Operation cancelled" in result.output
        # Check that results were NOT deleted
        assert len(list((temp_project / "results").glob("*.txt"))) == 2

    def test_clean_force(self, runner, temp_project):
        """Test clean command with force flag."""
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(temp_project),
            "--force",
        ])

        assert result.exit_code == 0
        assert "Results cleaned successfully" in result.output
        # Check that results were deleted
        assert not list((temp_project / "results").glob("*.txt"))

    def test_clean_json_output(self, runner, temp_project):
        """Test clean with JSON output."""
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(temp_project),
            "--force",
            "--json",
        ])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["success"] is True
        assert output_data["files_deleted"] == 2


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])