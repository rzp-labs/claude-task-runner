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
        assert "description" in schema
        assert "parameters" in schema
        assert schema["parameters"]["type"] == "object"
        assert "properties" in schema["parameters"]
        
        # Test JSON serialization
        json_str = json.dumps(schema)
        assert json.loads(json_str) == schema
    
    # Test complete schema
    complete = get_complete_schema()
    assert isinstance(complete, dict)
    assert "functions" in complete
    assert isinstance(complete["functions"], dict)
    # Should have 7 functions
    assert len(complete["functions"]) == 7
    
    # Verify all functions are included
    expected_funcs = ["run_task", "run_all_tasks", "get_task_status", 
                     "get_task_summary", "parse_task_list", "create_project", "clean"]
    for func in expected_funcs:
        assert func in complete["functions"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])