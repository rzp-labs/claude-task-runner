#!/usr/bin/env python3
"""
Comprehensive Tests for Task Manager Module

This module provides additional test coverage for the task_manager.py module,
specifically targeting areas with low coverage as identified in the
coverage report. It focuses on:

1. Task creation and configuration
2. Task execution with different parameters 
3. Task state management and transitions
4. Error handling and edge cases

Specific line ranges targeted:
- Lines 113-114: Task initialization
- Lines 166->174, 167-169: Task configuration/parameters
- Lines 189-193: Task execution/preparation
- Line 295, 312-316: Task state management
- Lines 337, 339, 343: Error handling
- Lines 355-365, 369-389: Task transitions/error handling
- Lines 420-444: Task management methods
- Line 467: Specific condition/branch
- Lines 565->570: Branch condition
- Lines 655-663: Error handling/resource management
- Lines 719-722, 744: Cleanup/finalization
"""

import json
import os
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call, ANY, PropertyMock

import pytest

from task_runner.core.task_manager import (
    TaskManager, TaskState, TaskError, TaskTimeoutError
)


class TestTaskInitialization:
    """Tests for task initialization and configuration (lines 113-114, 166-174)."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            tasks_dir = project_dir / "tasks"
            results_dir = project_dir / "results"
            
            # Create directory structure
            tasks_dir.mkdir()
            results_dir.mkdir()
            
            # Create a sample task file
            task_file = tasks_dir / "001_test_task.md"
            task_file.write_text("# Test Task\n\nThis is a test task.")
            
            # Create a task list file
            task_list_file = project_dir / "task_list.md"
            task_list_file.write_text("""
            # Task List
            
            ## Task 1: First Task
            This is the first task.
            
            ## Task 2: Second Task
            This is the second task.
            """)
            
            yield project_dir

    def test_task_manager_initialization_custom_dirs(self, temp_project):
        """Test TaskManager initialization with custom directories (lines 113-114)."""
        custom_tasks_dir = temp_project / "custom_tasks"
        custom_tasks_dir.mkdir()
        custom_results_dir = temp_project / "custom_results"
        custom_results_dir.mkdir()
        
        # Create manager with custom directories
        manager = TaskManager(
            base_dir=temp_project,
            tasks_dir=custom_tasks_dir,
            results_dir=custom_results_dir
        )
        
        # Verify custom directories were used
        assert manager.tasks_dir == custom_tasks_dir
        assert manager.results_dir == custom_results_dir
        assert manager.base_dir == temp_project

    def test_task_manager_initialization_nonexistent_dirs(self):
        """Test TaskManager initialization with nonexistent directories (lines 113-114)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "nonexistent"
            
            # Create manager with nonexistent base directory
            manager = TaskManager(base_dir=base_dir)
            
            # Verify directories were created
            assert manager.base_dir == base_dir
            assert manager.tasks_dir.exists()
            assert manager.results_dir.exists()

    @patch("task_runner.core.task_manager.subprocess.run")
    def test_task_execution_with_custom_timeout(self, mock_subprocess_run, temp_project):
        """Test task execution with custom timeout parameters (lines 166-174, 167-169)."""
        manager = TaskManager(base_dir=temp_project)
        task_file = temp_project / "tasks" / "001_test_task.md"
        
        # Mock subprocess.run to return a successful completion
        mock_subprocess_run.return_value = Mock(returncode=0)
        
        # Run task with custom timeout
        custom_timeout = 600  # 10 minutes
        success, result = manager.run_task(task_file, timeout_seconds=custom_timeout)
        
        # Verify timeout parameter was used
        assert success is True
        mock_subprocess_run.assert_called_once()
        # Check timeout was passed correctly to subprocess.run
        assert mock_subprocess_run.call_args[1]["timeout"] == custom_timeout

    @patch("task_runner.core.task_manager.subprocess.run")
    def test_task_execution_with_edge_parameters(self, mock_subprocess_run, temp_project):
        """Test task execution with edge case parameters (lines 166-174, 167-169)."""
        manager = TaskManager(base_dir=temp_project)
        task_file = temp_project / "tasks" / "001_test_task.md"
        
        # Mock subprocess.run to return a successful completion
        mock_subprocess_run.return_value = Mock(returncode=0)
        
        # Run task with minimal timeout
        min_timeout = 1  # 1 second
        success, result = manager.run_task(task_file, timeout_seconds=min_timeout)
        
        # Verify timeout parameter was used
        assert success is True
        mock_subprocess_run.assert_called_once()
        # Check timeout was passed correctly to subprocess.run
        assert mock_subprocess_run.call_args[1]["timeout"] == min_timeout


class TestTaskExecution:
    """Tests for task execution and preparation (lines 189-193, 355-365, 369-389)."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            tasks_dir = project_dir / "tasks"
            results_dir = project_dir / "results"
            
            # Create directory structure
            tasks_dir.mkdir()
            results_dir.mkdir()
            
            # Create a sample task file
            task_file = tasks_dir / "001_test_task.md"
            task_file.write_text("# Test Task\n\nThis is a test task.")
            
            yield project_dir

    @patch("task_runner.core.task_manager.subprocess.run")
    @patch("task_runner.core.task_manager.TaskManager._prepare_task_environment")
    def test_task_preparation_and_execution(self, mock_prepare_env, mock_subprocess_run, temp_project):
        """Test task preparation and execution process (lines 189-193)."""
        manager = TaskManager(base_dir=temp_project)
        task_file = temp_project / "tasks" / "001_test_task.md"
        
        # Mock environment preparation
        mock_prepare_env.return_value = {
            "env_var1": "value1",
            "env_var2": "value2",
            "PATH": os.environ.get("PATH", "")
        }
        
        # Mock subprocess.run to return a successful completion
        mock_subprocess_run.return_value = Mock(returncode=0)
        
        # Run task
        success, result = manager.run_task(task_file)
        
        # Verify preparation and execution steps
        assert success is True
        mock_prepare_env.assert_called_once()
        mock_subprocess_run.assert_called_once()
        # Verify environment was passed to subprocess.run
        assert "env" in mock_subprocess_run.call_args[1]
        assert mock_subprocess_run.call_args[1]["env"]["env_var1"] == "value1"

    @patch("task_runner.core.task_manager.subprocess.run")
    def test_task_execution_with_timeout(self, mock_subprocess_run, temp_project):
        """Test task execution with timeout handling (lines 355-365)."""
        manager = TaskManager(base_dir=temp_project)
        task_file = temp_project / "tasks" / "001_test_task.md"
        
        # Mock subprocess.run to raise TimeoutExpired
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=300)
        
        # Run task
        success, result = manager.run_task(task_file)
        
        # Verify timeout handling
        assert success is False
        assert result["status"] == TaskState.TIMEOUT.value
        mock_subprocess_run.assert_called_once()

    @patch("task_runner.core.task_manager.subprocess.run")
    def test_task_execution_with_error(self, mock_subprocess_run, temp_project):
        """Test task execution with error handling (lines 369-389)."""
        manager = TaskManager(base_dir=temp_project)
        task_file = temp_project / "tasks" / "001_test_task.md"
        
        # Mock subprocess.run to raise an error
        mock_subprocess_run.side_effect = Exception("Command execution failed")
        
        # Run task
        success, result = manager.run_task(task_file)
        
        # Verify error handling
        assert success is False
        assert result["status"] == TaskState.FAILED.value
        assert "Command execution failed" in result["error"]
        mock_subprocess_run.assert_called_once()

    @patch("task_runner.core.task_manager.subprocess.run")
    def test_task_execution_nonzero_return_code(self, mock_subprocess_run, temp_project):
        """Test task execution with non-zero return code (lines 369-389)."""
        manager = TaskManager(base_dir=temp_project)
        task_file = temp_project / "tasks" / "001_test_task.md"
        
        # Mock subprocess.run to return a non-zero exit code
        mock_subprocess_run.return_value = Mock(returncode=1)
        
        # Run task
        success, result = manager.run_task(task_file)
        
        # Verify error handling
        assert success is False
        assert result["status"] == TaskState.FAILED.value
        assert "exited with code 1" in result["error"]
        mock_subprocess_run.assert_called_once()

    @patch("task_runner.core.task_manager.TaskManager._update_task_state")
    @patch("task_runner.core.task_manager.subprocess.run")
    def test_task_state_updates_during_execution(self, mock_subprocess_run, mock_update_state, temp_project):
        """Test task state updates during execution process (lines 369-389)."""
        manager = TaskManager(base_dir=temp_project)
        task_file = temp_project / "tasks" / "001_test_task.md"
        
        # Mock subprocess.run to return a successful completion
        mock_subprocess_run.return_value = Mock(returncode=0)
        
        # Run task
        success, result = manager.run_task(task_file)
        
        # Verify state updates
        assert success is True
        # Should be called at least twice - once for RUNNING, once for COMPLETED
        assert mock_update_state.call_count >= 2
        # Check for RUNNING state update
        running_call = call(str(task_file.stem), TaskState.RUNNING, ANY)
        assert running_call in mock_update_state.mock_calls
        # Check for COMPLETED state update
        completed_call = call(str(task_file.stem), TaskState.COMPLETED, ANY)
        assert completed_call in mock_update_state.mock_calls


class TestTaskStateManagement:
    """Tests for task state management (lines 295, 312-316, 420-444)."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure with task state file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            tasks_dir = project_dir / "tasks"
            results_dir = project_dir / "results"
            
            # Create directory structure
            tasks_dir.mkdir()
            results_dir.mkdir()
            
            # Create sample task files
            task1_file = tasks_dir / "001_task1.md"
            task1_file.write_text("# Task 1\n\nThis is task 1.")
            
            task2_file = tasks_dir / "002_task2.md"
            task2_file.write_text("# Task 2\n\nThis is task 2.")
            
            # Create initial task state file
            task_state = {
                "001_task1": {
                    "status": TaskState.PENDING.value,
                    "updated_at": datetime.now().isoformat()
                },
                "002_task2": {
                    "status": TaskState.PENDING.value,
                    "updated_at": datetime.now().isoformat()
                }
            }
            
            state_file = project_dir / "task_state.json"
            with open(state_file, "w") as f:
                json.dump(task_state, f)
            
            yield project_dir

    def test_get_task_status(self, temp_project):
        """Test retrieving task status (line 295)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Get task status
        status = manager.get_task_status()
        
        # Verify status retrieval
        assert len(status) == 2
        assert "001_task1" in status
        assert "002_task2" in status
        assert status["001_task1"]["status"] == TaskState.PENDING.value
        assert status["002_task2"]["status"] == TaskState.PENDING.value

    def test_get_task_summary(self, temp_project):
        """Test generating task summary (lines 312-316)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Update task states for testing summary generation
        manager._update_task_state("001_task1", TaskState.COMPLETED, {"result": "Success"})
        manager._update_task_state("002_task2", TaskState.FAILED, {"error": "Test error"})
        
        # Get task summary
        summary = manager.get_task_summary()
        
        # Verify summary statistics
        assert summary["total"] == 2
        assert summary["completed"] == 1
        assert summary["failed"] == 1
        assert summary["pending"] == 0
        assert summary["running"] == 0

    def test_task_state_persistence(self, temp_project):
        """Test task state persistence (lines 420-444)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Update a task state
        manager._update_task_state("001_task1", TaskState.RUNNING, {"start_time": datetime.now().isoformat()})
        
        # Create a new manager instance to test persistence
        new_manager = TaskManager(base_dir=temp_project)
        status = new_manager.get_task_status()
        
        # Verify state was persisted
        assert "001_task1" in status
        assert status["001_task1"]["status"] == TaskState.RUNNING.value
        
    @patch("task_runner.core.task_manager.json.dump")
    def test_state_file_write_error(self, mock_json_dump, temp_project):
        """Test error handling during state file writing (lines 337, 339, 343)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Mock json.dump to raise an error
        mock_json_dump.side_effect = IOError("Permission denied")
        
        # Attempt to update task state
        # This should handle the IOError without crashing
        manager._update_task_state("001_task1", TaskState.RUNNING, {"start_time": datetime.now().isoformat()})
        
        # Verify we can still get task status (though it won't reflect the update)
        status = manager.get_task_status()
        assert "001_task1" in status
        # The state should still be PENDING since the update couldn't be persisted
        assert status["001_task1"]["status"] == TaskState.PENDING.value


class TestTaskListManagement:
    """Tests for task list management and parsing (line 467, 565->570)."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure with task list file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            tasks_dir = project_dir / "tasks"
            
            # Create directory structure
            tasks_dir.mkdir()
            
            # Create a task list file with various task formats
            task_list_file = project_dir / "task_list.md"
            task_list_file.write_text("""
            # Task List
            
            ## Task 1: First Task
            This is the first task.
            
            ## Task 2: Second Task
            This is the second task.
            
            ## Task 3: Special Chars in Title!@#$%^&*()
            Task with special characters.
            
            # Not a task section
            
            ## Task 4: Empty Task
            
            """)
            
            yield project_dir

    def test_parse_task_list_various_formats(self, temp_project):
        """Test parsing task list with various formats (line 467, 565->570)."""
        manager = TaskManager(base_dir=temp_project)
        task_list_file = temp_project / "task_list.md"
        
        # Parse task list
        task_files = manager.parse_task_list(task_list_file)
        
        # Verify parsing results
        assert len(task_files) == 4  # Should identify all 4 tasks
        
        # Check task files were created
        assert (temp_project / "tasks" / "001_first_task.md").exists()
        assert (temp_project / "tasks" / "002_second_task.md").exists()
        assert (temp_project / "tasks" / "003_special_chars_in_title.md").exists()
        assert (temp_project / "tasks" / "004_empty_task.md").exists()
        
        # Check content of created files
        with open(temp_project / "tasks" / "001_first_task.md") as f:
            content = f.read()
            assert "First Task" in content
            assert "This is the first task." in content

    def test_parse_task_list_empty(self, temp_project):
        """Test parsing empty task list (line 467)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Create empty task list file
        empty_task_list = temp_project / "empty_task_list.md"
        empty_task_list.write_text("# Empty Task List\n\nNo tasks here.")
        
        # Parse task list
        task_files = manager.parse_task_list(empty_task_list)
        
        # Verify parsing results
        assert len(task_files) == 0  # Should find no tasks

    def test_parse_task_list_nonexistent(self, temp_project):
        """Test parsing nonexistent task list (lines 565->570)."""
        manager = TaskManager(base_dir=temp_project)
        nonexistent_file = temp_project / "nonexistent.md"
        
        # Verify exception is raised
        with pytest.raises(FileNotFoundError):
            manager.parse_task_list(nonexistent_file)


class TestErrorHandlingAndCleanup:
    """Tests for error handling and cleanup operations (lines 655-663, 719-722, 744)."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            tasks_dir = project_dir / "tasks"
            results_dir = project_dir / "results"
            
            # Create directory structure
            tasks_dir.mkdir()
            results_dir.mkdir()
            
            # Create a sample task file
            task_file = tasks_dir / "001_test_task.md"
            task_file.write_text("# Test Task\n\nThis is a test task.")
            
            yield project_dir

    @patch("task_runner.core.task_manager.os.kill")
    @patch("task_runner.core.task_manager.signal.SIGTERM")
    def test_cleanup_running_processes(self, mock_sigterm, mock_kill, temp_project):
        """Test cleanup of running processes (lines 655-663)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Create a fake process ID file
        pid_file = temp_project / "tasks" / "001_test_task.pid"
        pid_file.write_text("12345")  # Fake PID
        
        # Call cleanup
        manager.cleanup()
        
        # Verify kill was called
        mock_kill.assert_called_once_with(12345, mock_sigterm)
        # Verify PID file was removed
        assert not pid_file.exists()

    @patch("task_runner.core.task_manager.os.kill")
    def test_cleanup_nonexistent_process(self, mock_kill, temp_project):
        """Test cleanup with nonexistent process (lines 655-663)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Create a fake process ID file
        pid_file = temp_project / "tasks" / "001_test_task.pid"
        pid_file.write_text("12345")  # Fake PID
        
        # Mock os.kill to raise ProcessLookupError (process not found)
        mock_kill.side_effect = ProcessLookupError("No such process")
        
        # Call cleanup - should handle the error without crashing
        manager.cleanup()
        
        # Verify kill was called
        mock_kill.assert_called_once()
        # Verify PID file was removed despite error
        assert not pid_file.exists()

    @patch("task_runner.core.task_manager.subprocess.run")
    def test_run_all_tasks_error_handling(self, mock_subprocess_run, temp_project):
        """Test error handling during run_all_tasks (lines 719-722)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Create another task file
        task2_file = temp_project / "tasks" / "002_another_task.md"
        task2_file.write_text("# Another Task\n\nThis is another task.")
        
        # Mock subprocess.run to fail on first task but succeed on second
        def mock_run_side_effect(*args, **kwargs):
            if "001_test_task" in str(args[0]):
                raise Exception("Command execution failed")
            else:
                return Mock(returncode=0)
        
        mock_subprocess_run.side_effect = mock_run_side_effect
        
        # Run all tasks
        results = manager.run_all_tasks()
        
        # Verify partial success handling
        assert results["total"] == 2
        assert results["success"] == 1
        assert results["failed"] == 1
        # Should have task-specific results
        assert "task_results" in results
        assert len(results["task_results"]) == 2

    def test_missing_task_directory(self, temp_project):
        """Test handling of missing task directory (line 744)."""
        manager = TaskManager(base_dir=temp_project)
        
        # Remove the tasks directory
        import shutil
        shutil.rmtree(temp_project / "tasks")
        
        # Run all tasks - should handle missing directory
        results = manager.run_all_tasks()
        
        # Verify results
        assert results["total"] == 0
        assert results["success"] == 0
        assert results["failed"] == 0
        assert "task_results" in results
        assert len(results["task_results"]) == 0

        # Verify the tasks directory was recreated
        assert (temp_project / "tasks").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
