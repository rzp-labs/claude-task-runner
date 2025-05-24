#!/usr/bin/env python3
"""
Integration Tests for CLI App

This module tests the CLI app through actual command invocation.

Test Coverage Target: Increase CLI app coverage
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

# Import the app directly from the cli module
from task_runner.cli import app


class TestCLIIntegration:
    """Integration tests for CLI commands."""

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
            
            # Create a sample task
            task_file = base_path / "tasks" / "001_test.md"
            task_file.write_text("# Test Task\nThis is a test task.")
            
            yield base_path

    def test_help_command(self, runner):
        """Test help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Claude Task Runner" in result.output

    def test_run_help(self, runner):
        """Test run command help."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "Run tasks" in result.output

    def test_status_help(self, runner):
        """Test status command help."""
        result = runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0
        assert "Show task status" in result.output

    def test_create_help(self, runner):
        """Test create command help."""
        result = runner.invoke(app, ["create", "--help"]) 
        assert result.exit_code == 0
        assert "Create task files" in result.output

    def test_clean_help(self, runner):
        """Test clean command help."""
        result = runner.invoke(app, ["clean", "--help"])
        assert result.exit_code == 0
        assert "Clean results" in result.output

    @patch("task_runner.core.task_manager.TaskManager.run_all_tasks")
    def test_run_demo_mode(self, mock_run_all, runner, temp_project):
        """Test run command in demo mode."""
        mock_run_all.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
            "task_results": {},
        }
        
        result = runner.invoke(app, [
            "run",
            "--base-dir", str(temp_project),
            "--demo-mode",
        ])
        
        # Should succeed
        assert result.exit_code == 0
        assert mock_run_all.called

    @patch("task_runner.core.task_manager.TaskManager.get_task_summary")
    @patch("task_runner.core.task_manager.TaskManager.get_task_status")
    def test_status_command_basic(self, mock_status, mock_summary, runner, temp_project):
        """Test basic status command."""
        mock_summary.return_value = {
            "total": 1,
            "pending": 1,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "timeout": 0,
        }
        mock_status.return_value = {
            "001_test": {"status": "pending", "name": "001_test"},
        }
        
        result = runner.invoke(app, [
            "status",
            "--base-dir", str(temp_project),
        ])
        
        assert result.exit_code == 0
        assert "Task Status" in result.output

    def test_create_missing_file(self, runner, temp_project):
        """Test create command with missing file."""
        result = runner.invoke(app, [
            "create",
            "--base-dir", str(temp_project),
            "--task-list", str(temp_project / "missing.md"),
        ])
        
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_clean_no_force_abort(self, runner, temp_project):
        """Test clean command without force (user aborts)."""
        # Create a result file
        result_file = temp_project / "results" / "test.result"
        result_file.write_text("test result")
        
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(temp_project),
        ], input="n\n")  # User says no
        
        assert result.exit_code == 1
        # File should still exist
        assert result_file.exists()


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])