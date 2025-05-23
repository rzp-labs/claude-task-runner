#!/usr/bin/env python3
"""
Tests for the TaskManager core functionality
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from task_runner.core.task_manager import TaskManager, TaskState


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def task_manager(temp_dir):
    """Create a TaskManager instance for testing"""
    return TaskManager(temp_dir)


@pytest.fixture
def task_list_file(temp_dir):
    """Create a sample task list file for testing"""
    task_list = temp_dir / "task_list.md"
    with open(task_list, "w") as f:
        f.write(
            """# Test Tasks

## Task 1: First Task
This is the first task.

## Task 2: Second Task
This is the second task.
"""
        )
    return task_list


def test_init(temp_dir):
    """Test TaskManager initialization"""
    manager = TaskManager(temp_dir)

    # Check that directories were created
    assert (temp_dir / "tasks").exists()
    assert (temp_dir / "results").exists()

    # Check that state was initialized
    assert manager.task_state == {}


def test_parse_task_list(task_manager, task_list_file):
    """Test parsing a task list"""
    task_files = task_manager.parse_task_list(task_list_file)

    # Check that task files were created
    assert len(task_files) == 2

    # Check file naming
    assert task_files[0].name == "001_first_task.md"
    assert task_files[1].name == "002_second_task.md"

    # Check file contents
    with open(task_files[0], "r") as f:
        assert f.read() == "# First Task\n\nThis is the first task."

    with open(task_files[1], "r") as f:
        assert f.read() == "# Second Task\n\nThis is the second task."

    # Check that task state was updated
    assert len(task_manager.task_state) == 2
    assert "001_first_task" in task_manager.task_state
    assert "002_second_task" in task_manager.task_state

    # Check task state properties
    assert task_manager.task_state["001_first_task"]["status"] == TaskState.PENDING
    assert task_manager.task_state["001_first_task"]["title"] == "First Task"


def test_get_task_summary(task_manager, task_list_file):
    """Test getting task summary"""
    # Parse task list to create tasks
    task_manager.parse_task_list(task_list_file)

    # Get summary
    summary = task_manager.get_task_summary()

    # Check summary structure
    assert "total" in summary
    assert "completed" in summary
    assert "failed" in summary
    assert "timeout" in summary
    assert "pending" in summary
    assert "running" in summary
    assert "completion_pct" in summary

    # Check counts
    assert summary["total"] == 2
    assert summary["pending"] == 2
    assert summary["completed"] == 0
    assert summary["failed"] == 0
    assert summary["timeout"] == 0
    assert summary["running"] == 0
    assert summary["completion_pct"] == 0
