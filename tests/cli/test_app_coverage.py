#!/usr/bin/env python3
"""Additional tests to increase app.py coverage"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from typer.testing import CliRunner

from task_runner.cli.app import app


class TestAppCoverage:
    """Tests to cover uncovered lines in app.py"""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    @pytest.fixture  
    def temp_project(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "tasks").mkdir()
            (base / "results").mkdir()
            
            # Create multiple tasks
            for i in range(5):
                task = base / "tasks" / f"00{i}_test.md"
                task.write_text(f"# Task {i}\nContent")
            
            yield base
    
    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_keyboard_interrupt(self, mock_tm_class, runner, temp_project):
        """Test KeyboardInterrupt handling."""
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(app, ["run", "--base-dir", str(temp_project)])
        
        assert result.exit_code == 130
        mock_tm.cleanup.assert_called()
    
    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_exception(self, mock_tm_class, runner, temp_project):
        """Test exception handling."""
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.side_effect = Exception("Test error")
        
        result = runner.invoke(app, ["run", "--base-dir", str(temp_project)])
        
        assert result.exit_code == 1
        assert "Test error" in result.output
        mock_tm.cleanup.assert_called()
    
    @patch("task_runner.core.task_manager.TaskManager")
    def test_run_json_error(self, mock_tm_class, runner, temp_project):
        """Test JSON output with error."""
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.run_all_tasks.side_effect = Exception("JSON error")
        
        result = runner.invoke(app, ["run", "--base-dir", str(temp_project), "--json"])
        
        assert result.exit_code == 1
        assert '"error": "JSON error"' in result.output
    
    @patch("task_runner.core.task_manager.TaskManager")
    def test_status_json(self, mock_tm_class, runner, temp_project):
        """Test status command with JSON output."""
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_summary.return_value = {"total": 5, "completed": 3}
        mock_tm.get_task_status.return_value = {}
        
        result = runner.invoke(app, ["status", "--base-dir", str(temp_project), "--json"])
        
        assert result.exit_code == 0
        assert '"total": 5' in result.output
    
    def test_create_with_task_list(self, runner, temp_project):
        """Test create command with task list."""
        task_list = temp_project / "tasks.md"
        task_list.write_text("- Task A\n- Task B\n- Task C")
        
        result = runner.invoke(app, [
            "create", "new_project",
            "--base-dir", str(temp_project),
            "--task-list", str(task_list)
        ])
        
        assert result.exit_code == 0
        assert "Created 3 task files" in result.output
    
    def test_create_json_output(self, runner, temp_project):
        """Test create command with JSON output."""
        result = runner.invoke(app, [
            "create", "test_proj",
            "--base-dir", str(temp_project),
            "--json"
        ])
        
        assert result.exit_code == 0
        assert '"project_name": "test_proj"' in result.output
    
    def test_clean_json(self, runner, temp_project):
        """Test clean command with JSON output."""
        result = runner.invoke(app, [
            "clean",
            "--base-dir", str(temp_project),
            "--json"
        ])
        
        assert result.exit_code == 0
        assert '"success": true' in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])