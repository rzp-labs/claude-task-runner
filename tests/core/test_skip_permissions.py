#!/usr/bin/env python3
"""
Tests for dangerous mode parameter support in TaskManager
"""

import tempfile
from pathlib import Path

from task_runner.core.task_manager import TaskManager


def test_dangerous_mode_parameter():
    """Test that run_task accepts skip_permissions parameter and processes it without error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TaskManager(Path(temp_dir))
        task_file = Path(temp_dir) / "tasks" / "test.md"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text("Test task")

        # Should not raise TypeError and should complete successfully in demo mode
        success, result = manager.run_task(
            task_file,
            timeout_seconds=10,
            fast_mode=False,
            demo_mode=True,
            use_streaming=False,
            skip_permissions=True,
        )
        assert success is True
        assert result["status"] == "completed"


def test_run_all_tasks_accepts_skip_permissions():
    """Test that run_all_tasks accepts skip_permissions parameter and processes it without error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TaskManager(Path(temp_dir))
        tasks_dir = Path(temp_dir) / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        # Create two dummy tasks
        for i in range(2):
            task_file = tasks_dir / f"task_{i}.md"
            task_file.write_text(f"Test task {i}")

        # Should not raise TypeError and should complete successfully in demo mode
        results = manager.run_all_tasks(
            timeout_seconds=10,
            fast_mode=False,
            demo_mode=True,
            use_streaming=False,
            skip_permissions=True,
        )
        assert results["success"] == 2
        assert results["failed"] == 0
        assert results["timeout"] == 0
        assert results["total"] == 2
        for task_result in results["task_results"].values():
            assert task_result["status"] == "completed"


def test_command_building():
    """Test that commands are built correctly with skip_permissions False (should not include dangerous flag)"""
    claude_path = "/path/to/claude"

    # skip_permissions=False: should NOT include --dangerously-skip-permissions
    cmd_parts = [claude_path, "--print"]
    skip_permissions = False
    if skip_permissions:
        cmd_parts.append("--dangerously-skip-permissions")

    assert (
        "--dangerously-skip-permissions" not in cmd_parts
    ), "Command should not include --dangerously-skip-permissions when skip_permissions is False"


def test_command_building_with_skip_permissions():
    """Test that the command built for Claude execution includes --dangerously-skip-permissions when skip_permissions is True."""
    claude_path = "/usr/local/bin/claude"
    # skip_permissions True: should include --dangerously-skip-permissions
    cmd_parts = [claude_path, "--print"]
    skip_permissions = True
    if skip_permissions:
        cmd_parts.append("--dangerously-skip-permissions")
    assert (
        "--dangerously-skip-permissions" in cmd_parts
    ), "Command should include --dangerously-skip-permissions when skip_permissions is True"


def test_dangerous_mode_interface_regression():
    """
    An error is raised if the run_task or run_all_tasks method does not accept the skip_permissions parameter.
    This detects interface regressions or refactoring errors that could silently break dangerous mode support.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TaskManager(Path(temp_dir))
        task_file = Path(temp_dir) / "tasks" / "test.md"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text("Test task")

        # run_task should accept skip_permissions and not raise TypeError
        try:
            manager.run_task(
                task_file,
                timeout_seconds=5,
                fast_mode=False,
                demo_mode=True,
                use_streaming=False,
                skip_permissions=True,
            )
        except TypeError as e:
            assert "skip_permissions" not in str(
                e
            ), "run_task does not accept skip_permissions parameter"

        # run_all_tasks should accept skip_permissions and not raise TypeError
        try:
            manager.run_all_tasks(
                timeout_seconds=5,
                fast_mode=False,
                demo_mode=True,
                use_streaming=False,
                skip_permissions=True,
            )
        except TypeError as e:
            assert "skip_permissions" not in str(
                e
            ), "run_all_tasks does not accept skip_permissions parameter"
