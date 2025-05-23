#!/usr/bin/env python3
"""
Tests for CLI Formatters Module

Testing actual functions that exist in the formatters module.
"""

from unittest.mock import patch
import pytest
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from task_runner.cli.formatters import (
    create_status_table,
    create_current_task_panel, 
    create_summary_panel,
    create_progress,
    create_dashboard,
    print_error,
    print_info,
    print_json,
    print_success,
    print_warning,
)


class TestCreateStatusTable:
    """Tests for create_status_table function."""

    def test_create_status_table_basic(self):
        """Test creating status table with basic task state."""
        task_state = {
            "task1": {"status": "completed", "name": "Task 1"},
            "task2": {"status": "pending", "name": "Task 2"},
        }
        
        table = create_status_table(task_state)
        
        assert isinstance(table, Table)
        assert table.title == "Task Status"

    def test_create_status_table_with_current_task(self):
        """Test status table with current running task."""
        task_state = {
            "task1": {"status": "completed", "name": "Task 1"},
            "task2": {"status": "running", "name": "Task 2"},
        }
        
        table = create_status_table(task_state, "task2", 1234567890.0)
        
        assert isinstance(table, Table)

    def test_create_status_table_empty(self):
        """Test status table with empty state."""
        table = create_status_table({})
        
        assert isinstance(table, Table)


class TestCreateCurrentTaskPanel:
    """Tests for create_current_task_panel function."""

    def test_create_current_task_panel_with_task(self):
        """Test panel creation with task info."""
        task_state = {"task1": {"status": "running", "name": "Task 1"}}
        
        panel = create_current_task_panel(task_state, "task1", 1234567890.0)
        
        assert isinstance(panel, Panel)

    def test_create_current_task_panel_no_current_task(self):
        """Test panel when no current task."""
        task_state = {"task1": {"status": "completed", "name": "Task 1"}}
        
        panel = create_current_task_panel(task_state)
        
        assert isinstance(panel, Panel)


class TestCreateSummaryPanel:
    """Tests for create_summary_panel function."""

    def test_create_summary_panel_basic(self):
        """Test summary panel creation."""
        task_state = {
            "task1": {"status": "completed", "name": "Task 1"},
            "task2": {"status": "failed", "name": "Task 2"},
            "task3": {"status": "pending", "name": "Task 3"},
        }
        
        panel = create_summary_panel(task_state)
        
        assert isinstance(panel, Panel)

    def test_create_summary_panel_empty(self):
        """Test summary panel with no tasks."""
        panel = create_summary_panel({})
        
        assert isinstance(panel, Panel)


class TestCreateProgress:
    """Tests for create_progress function."""

    def test_create_progress(self):
        """Test progress object creation."""
        progress = create_progress()
        
        assert isinstance(progress, Progress)


class TestCreateDashboard:
    """Tests for create_dashboard function."""

    def test_create_dashboard_basic(self):
        """Test dashboard creation with task state."""
        task_state = {
            "task1": {"status": "completed", "name": "Task 1"},
            "task2": {"status": "pending", "name": "Task 2"},
        }
        
        dashboard = create_dashboard(task_state)
        
        assert isinstance(dashboard, list)
        assert len(dashboard) > 0

    def test_create_dashboard_with_current_task(self):
        """Test dashboard with current task."""
        task_state = {
            "task1": {"status": "running", "name": "Task 1"},
        }
        
        dashboard = create_dashboard(task_state, "task1", 1234567890.0)
        
        assert isinstance(dashboard, list)


class TestPrintFunctions:
    """Tests for print utility functions."""

    @patch('task_runner.cli.formatters.console')
    def test_print_info(self, mock_console):
        """Test print_info function."""
        print_info("Test message", "Test Title")
        
        assert mock_console.print.called

    @patch('task_runner.cli.formatters.console')
    def test_print_success(self, mock_console):
        """Test print_success function."""
        print_success("Success message")
        
        assert mock_console.print.called

    @patch('task_runner.cli.formatters.console')
    def test_print_error(self, mock_console):
        """Test print_error function."""
        print_error("Error message")
        
        assert mock_console.print.called

    @patch('task_runner.cli.formatters.console')
    def test_print_warning(self, mock_console):
        """Test print_warning function."""
        print_warning("Warning message")
        
        assert mock_console.print.called

    def test_print_json(self, capsys):
        """Test print_json function."""
        data = {"key": "value", "number": 42}
        print_json(data)
        
        captured = capsys.readouterr()
        # Verify it's valid JSON
        import json
        parsed = json.loads(captured.out)
        assert parsed == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])