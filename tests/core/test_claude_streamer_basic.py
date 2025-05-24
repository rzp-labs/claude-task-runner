#!/usr/bin/env python3
"""
Basic Tests for Claude Streamer Module

Testing the core functions of the claude_streamer.py module:
- find_claude_path
- stream_claude_output
- clear_claude_context
- run_claude_tasks

This serves as a starting point for improving test coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, mock_open

import pytest

from task_runner.core.claude_streamer import (
    find_claude_path,
    stream_claude_output,
    clear_claude_context,
    run_claude_tasks
)


class TestClaudeStreamerBasics:
    """Basic tests for Claude Streamer module functions."""

    @patch("subprocess.run")
    def test_find_claude_path_success(self, mock_run):
        """Test finding Claude path when it's in the PATH."""
        # Mock successful 'which claude' command
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "/usr/local/bin/claude\n"
        mock_run.return_value = mock_process
        
        # Find Claude path
        claude_path = find_claude_path()
        
        # Verify result
        assert claude_path == "/usr/local/bin/claude"
        mock_run.assert_called_once()
    
    @patch("subprocess.run")
    def test_find_claude_path_not_found(self, mock_run):
        """Test finding Claude path when it's not in the PATH."""
        # Mock unsuccessful 'which claude' command
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        # Find Claude path - should return None or default value
        claude_path = find_claude_path()
        
        # Verify result indicates not found
        assert claude_path is None or claude_path == ""
        mock_run.assert_called_once()
    
    @patch("subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    def test_clear_claude_context(self, mock_temp_file, mock_run):
        """Test clearing Claude context."""
        # Mock temp file
        mock_file = Mock()
        mock_file.name = "/tmp/clear_context.txt"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Mock subprocess
        mock_process = Mock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Test with explicit claude_path
        result = clear_claude_context(claude_path="/usr/local/bin/claude")
        
        # Verify subprocess was called and temp file was created
        assert result is True
        mock_temp_file.assert_called_once()
        mock_run.assert_called_once()
        # Verify the command contained '/clear'
        assert '/clear' in str(mock_run.call_args)
    
    @pytest.fixture
    def temp_task_file(self):
        """Create a temporary task file for testing."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as temp_file:
            temp_file.write("# Test Task\n\nThis is a test task.")
            temp_path = temp_file.name
        
        yield Path(temp_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @patch("subprocess.Popen")
    def test_stream_claude_output_basic(self, mock_popen, temp_task_file):
        """Test basic functionality of stream_claude_output."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = [
            b"Claude: Processing...\n",
            b"Claude: Here's the result.\n",
            b"",  # Empty line to signal end of output
        ]
        mock_process.poll.side_effect = [None, None, 0]  # Return code 0 on last poll
        mock_popen.return_value = mock_process
        
        # Create a temporary file for results
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt') as result_file:
            # Stream Claude output
            success = stream_claude_output(
                task_file=str(temp_task_file),
                result_file=result_file.name
            )
            
            # Verify success
            assert success is True
            mock_popen.assert_called_once()
            
            # Verify result file contains output
            result_file.seek(0)
            content = result_file.read()
            assert "Claude:" in content
    
    @patch("task_runner.core.claude_streamer.stream_claude_output")
    @patch("task_runner.core.claude_streamer.clear_claude_context")
    def test_run_claude_tasks(self, mock_clear_context, mock_stream_output):
        """Test running multiple Claude tasks."""
        # Mock dependencies
        mock_clear_context.return_value = True
        mock_stream_output.return_value = True
        
        # Create test task files
        with tempfile.TemporaryDirectory() as temp_dir:
            task1 = Path(temp_dir) / "task1.md"
            task1.write_text("# Task 1")
            task2 = Path(temp_dir) / "task2.md"
            task2.write_text("# Task 2")
            
            # Run tasks
            results = run_claude_tasks([str(task1), str(task2)])
            
            # Verify results
            assert isinstance(results, dict)
            assert len(results) == 2
            assert str(task1) in results
            assert str(task2) in results
            assert results[str(task1)]["success"] is True
            assert results[str(task2)]["success"] is True
            
            # Verify dependencies were called
            assert mock_clear_context.call_count >= 1
            assert mock_stream_output.call_count == 2
    
    @patch("task_runner.core.claude_streamer.stream_claude_output")
    def test_run_claude_tasks_failure(self, mock_stream_output):
        """Test running Claude tasks with failure."""
        # Mock stream_claude_output to fail for the second task
        def mock_stream_side_effect(task_file, *args, **kwargs):
            return task_file != "task2.md"
        
        mock_stream_output.side_effect = mock_stream_side_effect
        
        # Run tasks
        results = run_claude_tasks(["task1.md", "task2.md"])
        
        # Verify results
        assert isinstance(results, dict)
        assert len(results) == 2
        assert "task1.md" in results
        assert "task2.md" in results
        assert results["task1.md"]["success"] is True
        assert results["task2.md"]["success"] is False
        
        # Verify dependencies were called
        assert mock_stream_output.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

