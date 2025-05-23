#!/usr/bin/env python3
"""
Tests for CLI App Main Function

This module tests the main entry point of the CLI app.

Test Coverage Target: Cover the main() function
"""

import sys
from unittest.mock import patch, Mock

import pytest


def test_main_function_success():
    """Test main function with successful execution."""
    from task_runner.cli.app import main
    
    # Mock sys.argv to simulate command line args
    with patch.object(sys, "argv", ["task-runner", "--help"]):
        with patch("task_runner.cli.app.app") as mock_app:
            # Simulate successful execution
            mock_app.return_value = None
            
            # Should not raise SystemExit for help
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Help should exit with 0
            assert exc_info.value.code == 0


def test_main_function_keyboard_interrupt():
    """Test main function handling keyboard interrupt."""
    from task_runner.cli.app import main
    
    with patch("task_runner.cli.app.app") as mock_app:
        # Simulate keyboard interrupt
        mock_app.side_effect = KeyboardInterrupt()
        
        # Should exit with 130
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 130


def test_main_function_exception():
    """Test main function handling exceptions."""
    from task_runner.cli.app import main
    
    with patch("task_runner.cli.app.app") as mock_app:
        # Simulate an exception
        mock_app.side_effect = Exception("Test error")
        
        # Should exit with 1
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])