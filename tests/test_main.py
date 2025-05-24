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
    # We need to patch the app in the namespace where __main__ will look for it
    import task_runner.cli.app as app_module
    original_app = app_module.app
    
    try:
        # Create a mock app
        mock_app = Mock()
        app_module.app = mock_app
        
        # Read and execute the file directly with __name__ set to __main__
        import os
        main_path = os.path.join(os.path.dirname(__file__), "..", "src", "task_runner", "__main__.py")
        
        # Create a namespace for execution
        namespace = {
            "__name__": "__main__",
            "__file__": main_path,
            "sys": sys,
        }
        
        with open(main_path) as f:
            code = compile(f.read(), main_path, 'exec')
            exec(code, namespace)
        
        # Verify app was called
        mock_app.assert_called_once()
    finally:
        # Restore original app
        app_module.app = original_app


def test_main_as_script():
    """Test running the module as a script."""
    # Test that the module can be run with python -m
    import task_runner.cli.app as app_module
    original_app = app_module.app
    
    try:
        # Create a mock app
        mock_app = Mock()
        app_module.app = mock_app
        
        with patch.object(sys, 'argv', ['python', '-m', 'task_runner']):
            # This simulates python -m task_runner
            import os
            main_path = os.path.join(os.path.dirname(__file__), "..", "src", "task_runner", "__main__.py")
            
            namespace = {
                "__name__": "__main__",
                "__file__": main_path,
                "sys": sys,
            }
            
            with open(main_path) as f:
                exec(f.read(), namespace)
            
            # App should have been called
            mock_app.assert_called()
    finally:
        # Restore original app
        app_module.app = original_app


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])