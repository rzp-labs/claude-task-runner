#!/usr/bin/env python3
"""
Tests for the formatters in the presentation layer
"""

import pytest
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from io import StringIO

from task_runner.presentation.formatters import (
    create_status_table,
    create_current_task_panel,
    create_summary_panel,
    print_error,
    print_warning,
    print_info,
    print_success,
    print_json
)


@pytest.fixture
def sample_task_state():
    """Sample task state for testing formatters"""
    return {
        "001_task_one": {
            "status": "completed",
            "started_at": "2023-01-01T10:00:00",
            "completed_at": "2023-01-01T10:05:00",
            "execution_time": 300,
            "exit_code": 0
        },
        "002_task_two": {
            "status": "running",
            "started_at": "2023-01-01T10:10:00"
        },
        "003_task_three": {
            "status": "pending"
        }
    }


def test_create_status_table(sample_task_state):
    """Test creating a status table"""
    table = create_status_table(sample_task_state)
    
    # Basic validation
    assert isinstance(table, Table)
    assert table.title == "Task Status"
    assert len(table.columns) == 6


def test_create_current_task_panel(sample_task_state):
    """Test creating a current task panel"""
    # Test with current task
    panel = create_current_task_panel(sample_task_state, "002_task_two", 1609502400)
    assert isinstance(panel, Panel)
    
    # Test with no current task
    panel = create_current_task_panel(sample_task_state)
    assert isinstance(panel, Panel)
    assert panel.title == "Current Task"


def test_create_summary_panel(sample_task_state):
    """Test creating a summary panel"""
    panel = create_summary_panel(sample_task_state)
    assert isinstance(panel, Panel)


def test_print_functions():
    """Test print functions"""
    # Create a string console for capturing output
    str_io = StringIO()
    console = Console(file=str_io, width=100)
    
    # Temporarily override the console in formatters
    import task_runner.presentation.formatters as formatters
    original_console = formatters.console
    formatters.console = console
    
    try:
        # Test print functions
        print_error("This is an error")
        output = str_io.getvalue()
        assert "This is an error" in output
        assert "Error" in output
        
        # Reset output
        str_io.truncate(0)
        str_io.seek(0)
        
        print_warning("This is a warning")
        output = str_io.getvalue()
        assert "This is a warning" in output
        assert "Warning" in output
        
        # Reset output
        str_io.truncate(0)
        str_io.seek(0)
        
        print_info("This is info")
        output = str_io.getvalue()
        assert "This is info" in output
        assert "Info" in output
        
        # Reset output
        str_io.truncate(0)
        str_io.seek(0)
        
        print_success("This is success")
        output = str_io.getvalue()
        assert "This is success" in output
        assert "Success" in output
        
        # Reset output
        str_io.truncate(0)
        str_io.seek(0)
        
        # Test print_json
        print_json({"key": "value"})
        output = str_io.getvalue()
        assert '"key": "value"' in output
    
    finally:
        # Restore original console
        formatters.console = original_console