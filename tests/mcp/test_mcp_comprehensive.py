#!/usr/bin/env python3
"""Comprehensive tests for all MCP modules to boost coverage."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Import all MCP modules
from task_runner.mcp import schema, wrapper, mcp_server


class TestMCPModules:
    """Test all MCP modules comprehensively."""
    
    def test_schema_functions(self):
        """Test all schema generation functions."""
        # Import all schema functions
        from task_runner.mcp.schema import (
            get_clean_schema, get_complete_schema, get_create_project_schema,
            get_get_task_status_schema, get_get_task_summary_schema,
            get_parse_task_list_schema, get_run_all_tasks_schema, get_run_task_schema
        )
        
        # Test each function
        funcs = [get_clean_schema, get_create_project_schema, get_get_task_status_schema,
                 get_get_task_summary_schema, get_parse_task_list_schema, 
                 get_run_all_tasks_schema, get_run_task_schema]
        
        for func in funcs:
            schema = func()
            assert isinstance(schema, dict)
            assert "name" in schema
            assert "inputSchema" in schema
            # Ensure JSON serializable
            json.dumps(schema)
        
        # Test complete schema
        complete = get_complete_schema()
        assert len(complete["tools"]) == 7
        assert complete["name"] == "task-runner"
    
    @patch("task_runner.mcp.wrapper.TaskManager")
    def test_wrapper_handlers(self, mock_tm_class):
        """Test all wrapper handler functions."""
        from task_runner.mcp.wrapper import (
            format_response, clean_handler, create_project_handler,
            get_task_status_handler, get_task_summary_handler,
            parse_task_list_handler, run_task_handler, run_all_tasks_handler,
            mcp_handler
        )
        
        # Test format_response
        assert format_response(True, {"data": 1}) == {"success": True, "data": 1}
        assert format_response(False, None, "err") == {"success": False, "error": "err"}
        
        # Setup mock
        mock_tm = Mock()
        mock_tm_class.return_value = mock_tm
        mock_tm.get_task_status.return_value = {}
        mock_tm.get_task_summary.return_value = {"total": 0}
        mock_tm.parse_task_list.return_value = []
        mock_tm.run_task.return_value = (True, {})
        mock_tm.run_all_tasks.return_value = {}
        
        # Test handlers
        with tempfile.TemporaryDirectory() as td:
            base_dir = str(td)
            Path(td, "tasks").mkdir()
            
            # Test each handler
            assert clean_handler({"params": {"base_dir": base_dir}})["success"]
            assert create_project_handler({"params": {"project_name": "p", "base_dir": base_dir}})["success"]
            assert get_task_status_handler({"params": {"base_dir": base_dir}})["success"]
            assert get_task_summary_handler({"params": {"base_dir": base_dir}})["success"]
            assert parse_task_list_handler({"params": {"task_list_path": "t.md", "base_dir": base_dir}})["success"]
            assert run_task_handler({"params": {"task_file": "t.md", "base_dir": base_dir}})["success"]
            assert run_all_tasks_handler({"params": {"base_dir": base_dir}})["success"]
        
        # Test mcp_handler
        with patch("task_runner.mcp.wrapper.clean_handler") as mock_clean:
            mock_clean.return_value = {"success": True}
            assert mcp_handler({"method": "clean", "params": {}})["success"]
        
        # Test invalid method
        result = mcp_handler({"method": "invalid", "params": {}})
        assert not result["success"]
    
    @patch("task_runner.mcp.mcp_server.FastMCP")
    def test_mcp_server_functions(self, mock_fastmcp):
        """Test mcp_server functions."""
        from task_runner.mcp.mcp_server import (
            configure_logging, ensure_log_directory, get_server_info,
            health_check, create_mcp_server, main
        )
        
        # Test simple functions
        with patch("task_runner.mcp.mcp_server.logger"):
            configure_logging("DEBUG")
        
        with tempfile.TemporaryDirectory() as td:
            with patch("task_runner.mcp.mcp_server.Path.home", return_value=Path(td)):
                ensure_log_directory()
                assert (Path(td) / ".claude" / "logs").exists()
        
        info = get_server_info()
        assert info["name"] == "task-runner-mcp"
        
        health = health_check()
        assert health["status"] == "healthy"
        
        # Test server creation
        mock_server = Mock()
        mock_fastmcp.return_value = mock_server
        server = create_mcp_server()
        assert server == mock_server
        
        # Test main
        with patch("sys.argv", ["prog"]):
            with patch("task_runner.mcp.mcp_server.create_mcp_server", return_value=mock_server):
                assert main() == 0
                mock_server.run.assert_called_with(transport="stdio")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])