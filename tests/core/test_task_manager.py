#!/usr/bin/env python3
"""
Tests for Task Manager Module

This module tests the TaskManager functionality including:
- Task parsing and discovery
- Task execution workflow  
- State management and persistence
- Error handling and recovery
- File I/O operations

Test Coverage Target: 85%+
"""

import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call, mock_open

import pytest
from task_runner.core.task_manager import TaskManager, TaskState


class TestTaskManagerInit:
    """Tests for TaskManager initialization."""

    def test_init_creates_directories(self):
        """Test that initialization creates required directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            tm = TaskManager(base_path)
            
            assert tm.base_dir == base_path
            assert tm.tasks_dir == base_path / "tasks"
            assert tm.results_dir == base_path / "results"
            assert tm.state_file == base_path / "task_state.json"
            assert tm.tasks_dir.exists()
            assert tm.results_dir.exists()
            assert tm.clear_context is True

    @patch("task_runner.core.task_manager.TaskManager._find_claude_executable")
    def test_init_finds_claude(self, mock_find):
        """Test that initialization finds Claude executable."""
        mock_find.return_value = "/usr/bin/claude"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tm = TaskManager(Path(temp_dir))
            assert tm.claude_path == "/usr/bin/claude"
            mock_find.assert_called_once()

    @patch("task_runner.core.task_manager.TaskManager._load_state")
    def test_init_loads_state(self, mock_load):
        """Test that initialization loads existing state."""
        mock_load.return_value = {"task1": {"status": TaskState.COMPLETED}}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tm = TaskManager(Path(temp_dir))
            assert tm.task_state == {"task1": {"status": TaskState.COMPLETED}}


class TestTaskParsing:
    """Tests for task list parsing."""

    def test_parse_task_list_success(self):
        """Test successful task list parsing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            tm = TaskManager(base_path)
            
            # Create task list file
            task_list = base_path / "tasks.md"
            task_list.write_text("""
## Task 1: Analyze Code
Analyze the Python code for best practices.

## Task 2: Generate Documentation
Create comprehensive documentation.
            """)
            
            created_files = tm.parse_task_list(task_list)
            
            assert len(created_files) == 2
            assert all(f.exists() for f in created_files)
            assert any("analyze_code" in str(f) for f in created_files)
            assert any("generate_documentation" in str(f) for f in created_files)

    def test_parse_task_list_empty_file(self):
        """Test parsing empty task list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            tm = TaskManager(base_path)
            
            # Create empty task list
            task_list = base_path / "tasks.md"
            task_list.write_text("")
            
            created_files = tm.parse_task_list(task_list)
            assert created_files == []

    def test_parse_task_list_updates_state(self):
        """Test that parsing updates task state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            tm = TaskManager(base_path)
            
            # Create task list
            task_list = base_path / "tasks.md"
            task_list.write_text("## Task 1: Test Task\nTest content")
            
            tm.parse_task_list(task_list)
            
            # Check state was updated
            assert len(tm.task_state) == 1
            task_name = list(tm.task_state.keys())[0]
            assert tm.task_state[task_name]["status"] == TaskState.PENDING
            assert "title" in tm.task_state[task_name]


class TestStateManagement:
    """Tests for state management functionality."""

    def test_load_state_success(self):
        """Test successful state loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            state_file = base_path / "task_state.json"
            test_state = {
                "task1": {
                    "status": TaskState.COMPLETED,
                    "name": "task1",
                    "created_at": "2024-01-01T00:00:00",
                }
            }
            state_file.write_text(json.dumps(test_state))
            
            tm = TaskManager(base_path)
            assert tm.task_state == test_state

    def test_load_state_missing_file(self):
        """Test loading when state file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tm = TaskManager(Path(temp_dir))
            assert tm.task_state == {}

    def test_load_state_corrupted_file(self):
        """Test loading corrupted state file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            state_file = base_path / "task_state.json"
            state_file.write_text("invalid json content")
            
            tm = TaskManager(base_path)
            assert tm.task_state == {}

    def test_save_state_success(self):
        """Test successful state saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            tm = TaskManager(base_path)
            
            test_state = {
                "task1": {
                    "status": TaskState.COMPLETED,
                    "name": "task1",
                }
            }
            tm.task_state = test_state
            tm._save_state()
            
            # Read and verify saved state
            state_file = base_path / "task_state.json"
            saved_state = json.loads(state_file.read_text())
            assert saved_state == test_state

    def test_get_task_status(self):
        """Test getting all task statuses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tm = TaskManager(Path(temp_dir))
            tm.task_state = {
                "task1": {"status": TaskState.COMPLETED},
                "task2": {"status": TaskState.FAILED},
                "task3": {"status": TaskState.PENDING},
            }
            
            status = tm.get_task_status()
            assert status == tm.task_state

    def test_get_task_summary(self):
        """Test task summary generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tm = TaskManager(Path(temp_dir))
            tm.task_state = {
                "task1": {"status": TaskState.COMPLETED},
                "task2": {"status": TaskState.FAILED},
                "task3": {"status": TaskState.PENDING},
                "task4": {"status": TaskState.RUNNING},
                "task5": {"status": TaskState.TIMEOUT},
            }
            
            summary = tm.get_task_summary()
            
            assert summary["total"] == 5
            assert summary["pending"] == 1
            assert summary["running"] == 1
            assert summary["completed"] == 1
            assert summary["failed"] == 1
            assert summary["timeout"] == 1
class TestRunTask:
    """Tests for running individual tasks."""

    @pytest.fixture
    def task_setup(self):
        """Set up test environment for task execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            tasks_dir = base_path / "tasks"
            results_dir = base_path / "results"
            tasks_dir.mkdir()
            results_dir.mkdir()
            
            # Create a test task
            task_file = tasks_dir / "001_test_task.md"
            task_file.write_text("# Test Task\nTest content")
            
            yield {
                "base_path": base_path,
                "task_file": task_file,
                "task_name": "001_test_task",
            }

    def test_run_task_demo_mode(self, task_setup):
        """Test running task in demo mode."""
        tm = TaskManager(task_setup["base_path"])
        
        success, state = tm.run_task(
            task_setup["task_file"],
            demo_mode=True,
        )
        
        assert success is True
        assert state["status"] == TaskState.COMPLETED
        assert "execution_time" in state
        
        # Check result file was created
        result_file = task_setup["base_path"] / "results" / f"{task_setup['task_name']}.result"
        assert result_file.exists()

    @patch("subprocess.run")
    def test_run_task_success(self, mock_run, task_setup):
        """Test successful task execution."""
        mock_run.return_value = Mock(returncode=0)
        
        tm = TaskManager(task_setup["base_path"])
        tm.claude_path = "/usr/bin/claude"
        
        success, state = tm.run_task(
            task_setup["task_file"],
            demo_mode=False,
            use_streaming=False,
        )
        
        assert success is True
        assert state["status"] == TaskState.COMPLETED
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_task_failure(self, mock_run, task_setup):
        """Test task execution failure."""
        mock_run.return_value = Mock(returncode=1)
        
        # Create error file with content
        error_file = task_setup["base_path"] / "results" / f"{task_setup['task_name']}.error"
        error_file.parent.mkdir(exist_ok=True)
        error_file.write_text("Task failed with error")
        
        tm = TaskManager(task_setup["base_path"])
        tm.claude_path = "/usr/bin/claude"
        
        # Force non-demo mode by checking claude path exists
        with patch("os.path.exists", return_value=True):
            success, state = tm.run_task(
                task_setup["task_file"],
                demo_mode=False,
                use_streaming=False,
            )
        
        assert success is False
        assert state["status"] == TaskState.FAILED
        assert "error" in state

    @patch("subprocess.run")
    def test_run_task_timeout(self, mock_run, task_setup):
        """Test task execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="claude", timeout=30
        )
        
        tm = TaskManager(task_setup["base_path"])
        tm.claude_path = "/usr/bin/claude"
        
        # Force non-demo mode
        with patch("os.path.exists", return_value=True):
            success, state = tm.run_task(
                task_setup["task_file"],
                timeout_seconds=30,
                demo_mode=False,
                use_streaming=False,
            )
        
        assert success is False
        assert state["status"] == TaskState.TIMEOUT

    @patch("subprocess.run")
    def test_run_task_with_streaming(self, mock_run, task_setup):
        """Test task execution with streaming mode."""
        mock_run.return_value = Mock(returncode=0)
        
        tm = TaskManager(task_setup["base_path"])
        tm.claude_path = "/usr/bin/claude"
        
        # Force non-demo mode
        with patch("os.path.exists", return_value=True):
            success, state = tm.run_task(
                task_setup["task_file"],
                demo_mode=False,
                use_streaming=True,
            )
        
        assert success is True
        # Check that streaming command was used (contains 'script' and 'tee')
        cmd = mock_run.call_args[0][0]
        assert "script" in cmd
        assert "tee" in cmd

    @patch("subprocess.run")
    def test_run_task_skip_permissions(self, mock_run, task_setup):
        """Test task execution with skip permissions flag."""
        mock_run.return_value = Mock(returncode=0)
        
        tm = TaskManager(task_setup["base_path"])
        tm.claude_path = "/usr/bin/claude"
        
        # Force non-demo mode
        with patch("os.path.exists", return_value=True):
            success, state = tm.run_task(
                task_setup["task_file"],
                demo_mode=False,
                use_streaming=False,
                skip_permissions=True,
            )
        
        assert success is True
        # Check that skip permissions flag was included
        cmd = mock_run.call_args[0][0]
        assert "--dangerously-skip-permissions" in cmd

    def test_run_task_updates_current_task(self, task_setup):
        """Test that running a task updates current task tracking."""
        tm = TaskManager(task_setup["base_path"])
        
        # Current task should be None initially
        assert tm.current_task is None
        assert tm.current_task_start_time is None
        
        # Run task in demo mode
        tm.run_task(task_setup["task_file"], demo_mode=True)
        
        # Current task should be set during execution
        # (Will be None after completion, but state should show it ran)
        assert task_setup["task_name"] in tm.task_state
        assert "started_at" in tm.task_state[task_setup["task_name"]]


class TestRunAllTasks:
    """Tests for running all tasks."""

    @pytest.fixture
    def multi_task_setup(self):
        """Set up multiple tasks for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            tasks_dir = base_path / "tasks"
            results_dir = base_path / "results"
            tasks_dir.mkdir()
            results_dir.mkdir()
            
            # Create multiple test tasks
            task_files = []
            for i in range(3):
                task_file = tasks_dir / f"00{i}_task.md"
                task_file.write_text(f"# Task {i}")
                task_files.append(task_file)
            
            yield {
                "base_path": base_path,
                "task_files": task_files,
            }

    @patch("task_runner.core.task_manager.TaskManager.run_task")
    def test_run_all_tasks_success(self, mock_run_task, multi_task_setup):
        """Test running all tasks successfully."""
        mock_run_task.return_value = (True, {"status": TaskState.COMPLETED})
        
        tm = TaskManager(multi_task_setup["base_path"])
        results = tm.run_all_tasks(demo_mode=True)
        
        assert results["total"] == 3
        assert results["success"] == 3
        assert results["failed"] == 0
        assert mock_run_task.call_count == 3

    @patch("task_runner.core.task_manager.TaskManager.run_task")
    def test_run_all_tasks_partial_failure(self, mock_run_task, multi_task_setup):
        """Test running tasks with some failures."""
        mock_run_task.side_effect = [
            (True, {"status": TaskState.COMPLETED}),
            (False, {"status": TaskState.FAILED}),
            (True, {"status": TaskState.COMPLETED}),
        ]
        
        tm = TaskManager(multi_task_setup["base_path"])
        results = tm.run_all_tasks(demo_mode=True)
        
        assert results["total"] == 3
        assert results["success"] == 2
        assert results["failed"] == 1

    @patch("task_runner.core.task_manager.TaskManager.run_task")
    @patch("task_runner.core.task_manager.TaskManager._clear_claude_context")
    def test_run_all_tasks_clear_context(self, mock_clear, mock_run_task, multi_task_setup):
        """Test context clearing between tasks."""
        mock_run_task.return_value = (True, {"status": TaskState.COMPLETED})
        mock_clear.return_value = True
        
        tm = TaskManager(multi_task_setup["base_path"])
        tm.clear_context = True
        tm.run_all_tasks(demo_mode=True)
        
        # Context should be cleared between tasks (2 times for 3 tasks)
        assert mock_clear.call_count == 2

    def test_run_all_tasks_no_tasks(self):
        """Test running with no tasks available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tm = TaskManager(Path(temp_dir))
            results = tm.run_all_tasks(demo_mode=True)
            
            assert results["success"] is False
            assert results["error"] == "No task files found"

    @patch("task_runner.core.task_manager.TaskManager.run_task")
    def test_run_all_tasks_skips_completed(self, mock_run_task, multi_task_setup):
        """Test that completed tasks are skipped."""
        tm = TaskManager(multi_task_setup["base_path"])
        
        # Mark first task as completed
        task_name = multi_task_setup["task_files"][0].stem
        tm.task_state[task_name] = {"status": TaskState.COMPLETED}
        
        mock_run_task.return_value = (True, {"status": TaskState.COMPLETED})
        tm.run_all_tasks(demo_mode=True)
        
        # Should only run 2 tasks (skipping the completed one)
        assert mock_run_task.call_count == 2


class TestCleanup:
    """Tests for cleanup functionality."""

    def test_cleanup_clears_current_task(self):
        """Test that cleanup clears current task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tm = TaskManager(Path(temp_dir))
            tm.current_task = "test_task"
            tm.current_task_start_time = time.time()
            
            tm.cleanup()
            
            assert tm.current_task is None
            assert tm.current_task_start_time is None

    @patch("task_runner.core.task_manager.TaskManager._save_state")
    def test_cleanup_saves_state(self, mock_save):
        """Test that cleanup saves state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tm = TaskManager(Path(temp_dir))
            tm.task_state = {"task1": {"status": TaskState.RUNNING}}
            
            tm.cleanup()
            
            mock_save.assert_called_once()


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])