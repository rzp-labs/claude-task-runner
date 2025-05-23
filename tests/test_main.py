#!/usr/bin/env python3
"""
Tests for __main__ module

This module tests the entry point of the application.

Test Coverage Target: 100%
"""

import sys
from unittest.mock import patch, Mock

import pytest


def test_main_entry_point():
    """Test that __main__ module can be imported and executed."""
    # Mock the app to prevent actual execution
    with patch("task_runner.cli.app") as mock_app_module:
        mock_app_module.app = Mock()
        
        # Import should work without errors
        import task_runner.__main__
        
        # The module should exist
        assert task_runner.__main__ is not None


def test_main_calls_app():
    """Test that main module calls the app when executed."""
    with patch("task_runner.cli.app") as mock_app_module:
        # Create a mock app object
        mock_app = Mock()
        mock_app_module.app = mock_app
        
        # Execute __main__ by running it as a module
        with patch.object(sys, 'argv', ['task_runner']):
            # Import and thus execute the __main__ module
            import importlib
            import task_runner.__main__
            importlib.reload(task_runner.__main__)
            
            # Verify app was called
            mock_app.assert_called_once()


def test_main_as_script():
    """Test running the module as a script."""
    # Test that the module can be run with python -m
    with patch("task_runner.cli.app.app") as mock_app:
        with patch.object(sys, 'argv', ['python', '-m', 'task_runner']):
            # This simulates python -m task_runner
            exec(open("src/task_runner/__main__.py").read(), {"__name__": "__main__"})
            
            # App should have been called
            mock_app.assert_called()


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])