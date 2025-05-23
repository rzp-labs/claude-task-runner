#!/usr/bin/env python3
"""Complete Tests for MCP Wrapper Module"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from task_runner.mcp.wrapper import *


class TestWrapperFunctions:
    """Test all wrapper functions."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            (base_path / "tasks").mkdir()
            (base_path / "results").mkdir()
            
            task_file = base_path / "tasks" / "001_test.md"
            task_file.write_text("# Test Task")
            
            task_list = base_path / "task_list.md"
            task_list.write_text("- Task 1")
            
            yield base_path
    
    def test_format_response(self):
        """Test response formatting."""
        # Success case
        result = format_response(True, {"key": "value"})
        assert result == {"success": True, "key": "value"}
        
        # Error case
        result = format_response(False, None, "Error")
        assert result == {"success": False, "error": "Error"}
        
        # Minimal case
        result = format_response(True)
        assert result == {"success": True}
    
    @patch("task_runner.mcp.wrapper.TaskManager")
    def test_all_handlers(self, mock_tm_class, temp_project):
        """Test all handler functions."""
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        
        # Test each handler
        handlers = [
            (clean_handler, {"base_dir": str(temp_project)}),
            (create_project_handler, {"project_name": "test", "base_dir": str(temp_project)}),
            (get_task_status_handler, {"base_dir": str(temp_project)}),
            (get_task_summary_handler, {"base_dir": str(temp_project)}),
            (parse_task_list_handler, {"task_list_path": str(temp_project / "task_list.md"), "base_dir": str(temp_project)}),
            (run_task_handler, {"task_file": "001_test.md", "base_dir": str(temp_project)}),
            (run_all_tasks_handler, {"base_dir": str(temp_project)}),
        ]
        
        # Configure mocks
        mock_tm.get_task_status.return_value = {"001": {"status": "done"}}
        mock_tm.get_task_summary.return_value = {"total": 1, "completed": 1}
        mock_tm.parse_task_list.return_value = [temp_project / "tasks" / "001_test.md"]
        mock_tm.run_task.return_value = (True, {"status": "completed"})
        mock_tm.run_all_tasks.return_value = {"total": 1, "success": 1}
        
        for handler, params in handlers:
            request = {"params": params}
            result = handler(request)
            assert result["success"] is True
    
    def test_mcp_handler(self):
        """Test main MCP handler."""
        # Test valid methods
        methods = ["clean", "create_project", "get_task_status", 
                  "get_task_summary", "parse_task_list", "run_task", "run_all_tasks"]
        
        for method in methods:
            with patch(f"task_runner.mcp.wrapper.{method}_handler") as mock_handler:
                mock_handler.return_value = {"success": True}
                request = {"method": method, "params": {}}
                result = mcp_handler(request)
                assert result["success"] is True
        
        # Test invalid method
        result = mcp_handler({"method": "invalid", "params": {}})
        assert result["success"] is False
        assert "Unknown method" in result["error"]
    
    def test_error_handling(self):
        """Test error handling in handlers."""
        with patch("task_runner.mcp.wrapper.TaskManager") as mock_tm_class:
            mock_tm_class.side_effect = Exception("Test error")
            
            request = {"params": {"base_dir": "/invalid"}}
            result = clean_handler(request)
            
            assert result["success"] is False
            assert "Test error" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])