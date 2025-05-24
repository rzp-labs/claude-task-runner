#!/usr/bin/env python3
"""
Simple Working Tests for CLI App

These tests focus on testing the CLI commands with proper mocking.
"""

from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

import pytest
from typer.testing import CliRunner

from task_runner.cli import app


class TestCLIHelp:
    """Test help commands."""

    def test_main_help(self):
        """Test main help command."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Claude Task Runner" in result.output

    def test_run_help(self):
        """Test run command help."""
        runner = CliRunner()
        result = runner.invoke(app, ["run", "--help"])
        
        assert result.exit_code == 0
        assert "Run tasks" in result.output

    def test_status_help(self):
        """Test status command help."""
        runner = CliRunner()
        result = runner.invoke(app, ["status", "--help"])
        
        assert result.exit_code == 0
        assert "Show" in result.output

    def test_create_help(self):
        """Test create command help."""
        runner = CliRunner()
        result = runner.invoke(app, ["create", "--help"])
        
        assert result.exit_code == 0
        assert "Create" in result.output


class TestCLICommands:
    """Test actual commands with mocking."""

    @patch('task_runner.core.task_manager.TaskManager')
    def test_run_demo_mode(self, mock_task_manager_class):
        """Test run command in demo mode."""
        # Set up mock
        mock_tm = Mock()
        mock_task_manager_class.return_value = mock_tm
        mock_tm.run_all_tasks.return_value = {
            "total": 2,
            "success": 2,
            "failed": 0,
            "task_results": {}
        }
        mock_tm.cleanup = Mock()

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create task directory and a task file
            task_dir = Path(temp_dir) / "tasks"
            task_dir.mkdir()
            (task_dir / "001_test.md").write_text("# Test Task\nDemo task")
            
            result = runner.invoke(app, [
                "run",
                "--base-dir", temp_dir,
                "--quick-demo"
            ])
        
        assert result.exit_code == 0

    @patch('task_runner.core.task_manager.TaskManager')
    def test_status_command(self, mock_task_manager_class):
        """Test status command."""
        # Set up mock
        mock_tm = Mock()
        mock_task_manager_class.return_value = mock_tm
        mock_tm.get_task_status.return_value = {
            "task1": {"status": "completed", "name": "Task 1"}
        }
        mock_tm.get_task_summary.return_value = {
            "total": 1,
            "pending": 0,
            "running": 0,
            "completed": 1,
            "failed": 0,
            "timeout": 0
        }
        mock_tm.current_task = None
        mock_tm.current_task_start_time = None

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(app, [
                "status",
                "--base-dir", temp_dir
            ])
        
        assert result.exit_code == 0

    @patch('task_runner.core.task_manager.TaskManager')
    def test_status_json_output(self, mock_task_manager_class):
        """Test status command with JSON output."""
        # Set up mock
        mock_tm = Mock()
        mock_task_manager_class.return_value = mock_tm
        mock_tm.get_task_status.return_value = {"task1": {"status": "completed"}}
        mock_tm.get_task_summary.return_value = {"total": 1, "completed": 1}

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(app, [
                "status",
                "--base-dir", temp_dir,
                "--json"
            ])
        
        assert result.exit_code == 0
        # Verify JSON output
        import json
        output_data = json.loads(result.output)
        assert "tasks" in output_data
        assert "summary" in output_data

    @patch('task_runner.core.task_manager.TaskManager')
    def test_create_project(self, mock_task_manager_class):
        """Test create command."""
        # Set up mock
        mock_tm = Mock()
        mock_task_manager_class.return_value = mock_tm

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(app, [
                "create",
                "test_project",
                "--base-dir", temp_dir
            ])
        
        assert result.exit_code == 0
        assert "test_project" in result.output

    def test_clean_abort(self):
        """Test clean command basic functionality."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create required directories
            (Path(temp_dir) / "tasks").mkdir()
            results_dir = Path(temp_dir) / "results"
            results_dir.mkdir()
            (results_dir / "test.txt").write_text("test")
            
            result = runner.invoke(app, [
                "clean",
                "--base-dir", temp_dir
            ])
        
        # Clean command should succeed
        assert result.exit_code == 0
        # File should still exist - clean only removes processes, not files
        assert (results_dir / "test.txt").exists()

    def test_clean_force(self):
        """Test clean command with JSON output."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create required directories
            (Path(temp_dir) / "tasks").mkdir()
            results_dir = Path(temp_dir) / "results"
            results_dir.mkdir()
            (results_dir / "test.txt").write_text("test")
            
            result = runner.invoke(app, [
                "clean",
                "--base-dir", temp_dir,
                "--json"
            ])
        
        assert result.exit_code == 0
        assert "success" in result.output.lower()


class TestCLIErrors:
    """Test error handling."""

    def test_invalid_base_dir(self):
        """Test with non-existent base directory."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "run",
            "--base-dir", "/nonexistent/path/that/should/not/exist"
        ])
        
        assert result.exit_code == 1  # Should fail with exit code 1

    def test_invalid_timeout(self):
        """Test with invalid timeout value."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "run",
            "--timeout", "-5"  # Negative timeout
        ])
        
        assert result.exit_code == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])