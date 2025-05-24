#!/usr/bin/env python3
"""
Tests for Claude Streamer Module

This module tests the claude_streamer functionality including:
- Claude executable detection
- Stream output processing
- Process lifecycle management
- Timeout handling
- Error scenarios

Test Coverage Target: 80%+
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call, mock_open

import pytest
from task_runner.core.claude_streamer import (
    find_claude_path,
    stream_claude_output,
    clear_claude_context,
    run_claude_tasks,
)


class TestFindClaudePath:
    """Tests for find_claude_path function."""

    @patch("subprocess.run")
    def test_find_claude_path_success(self, mock_run):
        """Test successful Claude path detection."""
        mock_run.return_value = Mock(
            returncode=0, stdout="/usr/local/bin/claude\n"
        )
        
        result = find_claude_path()
        
        assert result == "/usr/local/bin/claude"
        mock_run.assert_called_once_with(
            ["which", "claude"], capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    def test_find_claude_path_not_found(self, mock_run):
        """Test when Claude is not found in PATH."""
        mock_run.return_value = Mock(returncode=1, stdout="")
        
        result = find_claude_path()
        
        assert result == "claude"  # Falls back to default

    @patch("subprocess.run")
    def test_find_claude_path_exception(self, mock_run):
        """Test exception handling during path detection."""
        mock_run.side_effect = Exception("Command failed")
        
        result = find_claude_path()
        
        assert result == "claude"  # Falls back to default


class TestStreamClaudeOutput:
    """Tests for stream_claude_output function."""

    @pytest.fixture
    def temp_files(self):
        """Create temporary test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            task_file = temp_path / "test_task.md"
            task_file.write_text("# Test Task\nTest content")
            
            yield {
                "temp_dir": temp_path,
                "task_file": str(task_file),
                "result_file": str(temp_path / "result.txt"),
                "error_file": str(temp_path / "error.txt"),
            }

    @patch("subprocess.Popen")
    def test_stream_claude_output_success(self, mock_popen, temp_files):
        """Test successful Claude execution with streaming."""
        # Mock process with successful execution
        mock_process = Mock()
        # Need enough poll calls for the entire flow
        mock_process.poll.side_effect = [None, None, None, 0, 0, 0]
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = [
            "Processing task...\n",
            "Task completed successfully\n",
            "",  # End of output
        ]
        mock_process.stdout.readable.return_value = True
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        result = stream_claude_output(
            task_file=temp_files["task_file"],
            result_file=temp_files["result_file"],
            error_file=temp_files["error_file"],
            quiet=True,
        )

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["status"] == "completed"
        assert result["task_file"] == temp_files["task_file"]
        assert result["result_file"] == temp_files["result_file"]
        assert result["error_file"] == temp_files["error_file"]
        assert "execution_time" in result
        assert result["execution_time"] > 0

        # Verify output was written
        with open(temp_files["result_file"], "r") as f:
            content = f.read()
            assert "Processing task..." in content
            assert "Task completed successfully" in content

    @patch("subprocess.Popen")
    def test_stream_claude_output_failure(self, mock_popen, temp_files):
        """Test Claude execution failure."""
        # Mock process with failed execution
        mock_process = Mock()
        # Need enough poll calls for the entire flow
        mock_process.poll.side_effect = [None, None, 1, 1, 1]
        mock_process.returncode = 1
        mock_process.stdout.readline.side_effect = [
            "Error: Task failed\n",
            "",
        ]
        mock_process.stdout.readable.return_value = True
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        result = stream_claude_output(
            task_file=temp_files["task_file"],
            quiet=True,
        )

        assert result["success"] is False
        assert result["exit_code"] == 1
        assert result["status"] == "failed"

    @patch("subprocess.Popen")
    @patch("time.time")
    def test_stream_claude_output_timeout(self, mock_time, mock_popen, temp_files):
        """Test timeout handling during execution."""
        # Mock time to simulate timeout
        mock_time.side_effect = [
            0,      # Start time
            0.1,    # First check
            0.2,    # Second check
            301,    # Timeout exceeded
        ]
        
        # Mock process that never completes
        mock_process = Mock()
        mock_process.poll.return_value = None  # Always running
        mock_process.stdout.readline.return_value = ""
        mock_process.stdout.readable.return_value = True
        mock_popen.return_value = mock_process

        result = stream_claude_output(
            task_file=temp_files["task_file"],
            timeout_seconds=300,
            quiet=True,
        )

        assert result["success"] is False
        assert result["exit_code"] == -1
        assert result["status"] == "timeout"
        mock_process.terminate.assert_called_once()

    @patch("subprocess.Popen")
    def test_stream_claude_output_exception(self, mock_popen, temp_files):
        """Test exception handling during streaming."""
        mock_popen.side_effect = Exception("Process creation failed")

        result = stream_claude_output(
            task_file=temp_files["task_file"],
            quiet=True,
        )

        assert result["success"] is False
        assert result["status"] == "error"
        assert "error" in result
        assert "Process creation failed" in result["error"]

    def test_stream_claude_output_usage_limit(self, temp_files):
        """Test detection of usage limit reached."""
        with patch("subprocess.Popen") as mock_popen:
            # Mock process with usage limit message
            mock_process = Mock()
            # Need enough poll calls for the entire flow
            mock_process.poll.side_effect = [None, None, 0, 0, 0]
            mock_process.returncode = 0
            mock_process.stdout.readline.side_effect = [
                "Error: usage limit reached for your account\n",
                "",
            ]
            mock_process.stdout.readable.return_value = True
            mock_process.wait.return_value = None
            mock_popen.return_value = mock_process

            result = stream_claude_output(
                task_file=temp_files["task_file"],
                quiet=False,  # Enable logging to test detection
            )

            # Should still complete but with usage limit detected
            assert result["exit_code"] == 0
            
            # Verify usage limit message was written
            with open(result["result_file"], "r") as f:
                content = f.read()
                assert "usage limit reached" in content.lower()

    def test_stream_claude_output_raw_json(self, temp_files):
        """Test raw JSON output mode."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.poll.side_effect = [None, 0, 0]
            mock_process.returncode = 0
            mock_process.stdout.readline.side_effect = ["", ""]
            mock_process.stdout.readable.return_value = True
            mock_process.wait.return_value = None
            mock_popen.return_value = mock_process

            result = stream_claude_output(
                task_file=temp_files["task_file"],
                raw_json=True,
                quiet=True,
            )

            # Verify --json flag was used
            call_args = mock_popen.call_args[0][0]
            assert "--json" in call_args

    def test_stream_claude_output_custom_paths(self, temp_files):
        """Test with custom Claude executable path."""
        custom_claude = "/custom/path/to/claude"
        
        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.poll.side_effect = [0, 0]
            mock_process.returncode = 0
            mock_process.stdout = None
            mock_process.wait.return_value = None
            mock_popen.return_value = mock_process

            result = stream_claude_output(
                task_file=temp_files["task_file"],
                claude_path=custom_claude,
                quiet=True,
            )

            # Verify custom path was used
            call_args = mock_popen.call_args[0][0]
            assert call_args[0] == custom_claude


class TestClearClaudeContext:
    """Tests for clear_claude_context function."""

    @patch("subprocess.run")
    def test_clear_context_success(self, mock_run):
        """Test successful context clearing."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        result = clear_claude_context()
        
        assert result is True
        # Verify echo command was used
        call_args = mock_run.call_args[0][0]
        assert "echo '/clear'" in call_args

    @patch("subprocess.run")
    def test_clear_context_failure(self, mock_run):
        """Test failed context clearing."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr=b"Error clearing"
        )
        
        result = clear_claude_context()
        
        assert result is False

    @patch("subprocess.run")
    def test_clear_context_exception(self, mock_run):
        """Test exception during context clearing."""
        mock_run.side_effect = Exception("Command failed")
        
        result = clear_claude_context()
        
        assert result is False

    @patch("subprocess.run")
    @patch("task_runner.core.claude_streamer.find_claude_path")
    def test_clear_context_custom_path(self, mock_find, mock_run):
        """Test with custom Claude path."""
        custom_path = "/custom/claude"
        mock_run.return_value = Mock(returncode=0)
        
        result = clear_claude_context(claude_path=custom_path)
        
        assert result is True
        # Verify custom path was used
        call_args = mock_run.call_args[0][0]
        assert custom_path in call_args
        mock_find.assert_not_called()


class TestRunClaudeTasks:
    """Tests for run_claude_tasks function."""

    @pytest.fixture
    def task_files(self):
        """Create multiple task files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            files = []
            
            for i in range(3):
                task_file = temp_path / f"task_{i}.md"
                task_file.write_text(f"# Task {i}\nContent for task {i}")
                files.append(str(task_file))
            
            yield files

    @patch("task_runner.core.claude_streamer.stream_claude_output")
    @patch("task_runner.core.claude_streamer.clear_claude_context")
    def test_run_claude_tasks_success(self, mock_clear, mock_stream, task_files):
        """Test running multiple tasks successfully."""
        # Mock successful execution for each task
        mock_stream.side_effect = [
            {"success": True, "exit_code": 0, "execution_time": 1.0},
            {"success": True, "exit_code": 0, "execution_time": 2.0},
            {"success": True, "exit_code": 0, "execution_time": 1.5},
        ]
        mock_clear.return_value = True

        result = run_claude_tasks(task_files, quiet=True)

        assert result["total_tasks"] == 3
        assert result["successful_tasks"] == 3
        assert result["failed_tasks"] == 0
        assert len(result["results"]) == 3
        assert all(r["success"] for r in result["results"])
        
        # Verify context was cleared between tasks (but not after last)
        assert mock_clear.call_count == 2

    @patch("task_runner.core.claude_streamer.stream_claude_output")
    def test_run_claude_tasks_partial_failure(self, mock_stream, task_files):
        """Test with some tasks failing."""
        # Mock mixed results
        mock_stream.side_effect = [
            {"success": True, "exit_code": 0, "execution_time": 1.0},
            {"success": False, "exit_code": 1, "execution_time": 0.5},
            {"success": True, "exit_code": 0, "execution_time": 2.0},
        ]

        result = run_claude_tasks(task_files, clear_context=False, quiet=True)

        assert result["total_tasks"] == 3
        assert result["successful_tasks"] == 2
        assert result["failed_tasks"] == 1

    def test_run_claude_tasks_no_files(self):
        """Test with no task files provided."""
        result = run_claude_tasks([], quiet=True)
        
        assert result["success"] is False
        assert result["error"] == "No task files provided"

    def test_run_claude_tasks_missing_file(self, task_files):
        """Test with non-existent file."""
        task_files.append("/non/existent/file.md")
        
        with patch("task_runner.core.claude_streamer.stream_claude_output") as mock_stream:
            # Only called for existing files
            mock_stream.side_effect = [
                {"success": True, "exit_code": 0, "execution_time": 1.0},
                {"success": True, "exit_code": 0, "execution_time": 1.0},
                {"success": True, "exit_code": 0, "execution_time": 1.0},
            ]
            
            result = run_claude_tasks(task_files, quiet=True)
            
            assert result["total_tasks"] == 4
            assert result["successful_tasks"] == 3
            assert result["failed_tasks"] == 1
            
            # Find the failed result
            failed = [r for r in result["results"] if not r.get("success", True)]
            assert len(failed) == 1
            assert failed[0]["error"] == "File not found"


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])