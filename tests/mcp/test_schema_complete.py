#!/usr/bin/env python3
"""Tests for MCP Schema Module - Complete Coverage"""

import json
import pytest
from task_runner.mcp.schema import *


def test_all_schema_functions():
    """Test all schema generation functions."""
    # Test individual schema functions
    schemas = {
        "clean": get_clean_schema(),
        "create_project": get_create_project_schema(),
        "get_task_status": get_get_task_status_schema(),
        "get_task_summary": get_get_task_summary_schema(),
        "parse_task_list": get_parse_task_list_schema(),
        "run_all_tasks": get_run_all_tasks_schema(),
        "run_task": get_run_task_schema(),
    }
    
    # Verify each schema
    for name, schema in schemas.items():
        assert isinstance(schema, dict)
        assert schema["name"] == name
        assert "description" in schema
        assert "inputSchema" in schema
        assert schema["inputSchema"]["type"] == "object"
        assert "properties" in schema["inputSchema"]
        
        # Test JSON serialization
        json_str = json.dumps(schema)
        assert json.loads(json_str) == schema
    
    # Test complete schema
    complete = get_complete_schema()
    assert isinstance(complete, dict)
    assert complete["name"] == "task-runner"
    assert "version" in complete
    assert len(complete["tools"]) == 7
    
    # Verify all tools in complete schema
    tool_names = [t["name"] for t in complete["tools"]]
    for name in schemas.keys():
        assert name in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])