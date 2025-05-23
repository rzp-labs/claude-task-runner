#!/usr/bin/env python3
"""
JSON Schemas for Task Runner MCP Integration

This module defines the JSON schemas for the Task Runner MCP functions
and parameters. These schemas are used by the MCP wrapper to validate
input and output.

This module is part of the Integration Layer and can depend on both
Core Layer and Presentation Layer components.

Links:
- JSON Schema: https://json-schema.org/
- FastMCP: https://github.com/anthropics/fastmcp

Sample input:
- Schema definition requests

Expected output:
- JSON Schema objects
"""

from typing import Any, Dict


def get_run_task_schema() -> Dict[str, Any]:
    """
    Get schema for run_task MCP function

    Returns:
        JSON Schema for run_task function
    """
    return {
        "description": "Run a single task with Claude in an isolated context",
        "parameters": {
            "type": "object",
            "properties": {
                "task_path": {"type": "string", "description": "Path to the task file"},
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for tasks and results",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds",
                    "default": 300,
                },
            },
            "required": ["task_path"],
        },
    }


def get_run_all_tasks_schema() -> Dict[str, Any]:
    """
    Get schema for run_all_tasks MCP function

    Returns:
        JSON Schema for run_all_tasks function
    """
    return {
        "description": "Run all tasks in the tasks directory",
        "parameters": {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for tasks and results",
                },
                "resume": {
                    "type": "boolean",
                    "description": "Resume from previously interrupted tasks",
                    "default": False,
                },
            },
        },
    }


def get_parse_task_list_schema() -> Dict[str, Any]:
    """
    Get schema for parse_task_list MCP function

    Returns:
        JSON Schema for parse_task_list function
    """
    return {
        "description": "Parse a task list file and split into individual task files",
        "parameters": {
            "type": "object",
            "properties": {
                "task_list_path": {"type": "string", "description": "Path to the task list file"},
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for tasks and results",
                },
            },
            "required": ["task_list_path"],
        },
    }


def get_create_project_schema() -> Dict[str, Any]:
    """
    Get schema for create_project MCP function

    Returns:
        JSON Schema for create_project function
    """
    return {
        "description": "Create a new project from a task list",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Name of the project"},
                "task_list_path": {"type": "string", "description": "Path to the task list file"},
                "base_dir": {"type": "string", "description": "Base directory for projects"},
            },
            "required": ["project_name"],
        },
    }


def get_get_task_status_schema() -> Dict[str, Any]:
    """
    Get schema for get_task_status MCP function

    Returns:
        JSON Schema for get_task_status function
    """
    return {
        "description": "Get the status of all tasks",
        "parameters": {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for tasks and results",
                }
            },
        },
    }


def get_get_task_summary_schema() -> Dict[str, Any]:
    """
    Get schema for get_task_summary MCP function

    Returns:
        JSON Schema for get_task_summary function
    """
    return {
        "description": "Get summary statistics of all tasks",
        "parameters": {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for tasks and results",
                }
            },
        },
    }


def get_clean_schema() -> Dict[str, Any]:
    """
    Get schema for clean MCP function

    Returns:
        JSON Schema for clean function
    """
    return {
        "description": "Clean up any running processes",
        "parameters": {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for tasks and results",
                }
            },
        },
    }


def get_complete_schema() -> Dict[str, Any]:
    """
    Get complete MCP schema

    Returns:
        Complete MCP schema for all functions
    """
    return {
        "functions": {
            "run_task": get_run_task_schema(),
            "run_all_tasks": get_run_all_tasks_schema(),
            "parse_task_list": get_parse_task_list_schema(),
            "create_project": get_create_project_schema(),
            "get_task_status": get_get_task_status_schema(),
            "get_task_summary": get_get_task_summary_schema(),
            "clean": get_clean_schema(),
        }
    }


if __name__ == "__main__":
    # Validate schema definitions
    import json
    import sys

    # List to track all validation failures
    all_validation_failures = []
    TOTAL_TESTS = 0

    # Test 1: Get complete schema
    TOTAL_TESTS += 1
    try:
        schema = get_complete_schema()

        # Validate structure
        if "functions" not in schema:
            all_validation_failures.append("Complete schema missing 'functions' key")

        # Check that all functions are present
        expected_functions = [
            "run_task",
            "run_all_tasks",
            "parse_task_list",
            "create_project",
            "get_task_status",
            "get_task_summary",
            "clean",
        ]

        for func in expected_functions:
            if func not in schema["functions"]:
                all_validation_failures.append(f"Function '{func}' missing from schema")

        # Validate each function schema
        for func, func_schema in schema["functions"].items():
            if "description" not in func_schema:
                all_validation_failures.append(f"Function '{func}' missing description")
            if "parameters" not in func_schema:
                all_validation_failures.append(f"Function '{func}' missing parameters")

        # Print the schema
        print(json.dumps(schema, indent=2))
    except Exception as e:
        all_validation_failures.append(f"Complete schema test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"L VALIDATION FAILED - {len(all_validation_failures)} of {TOTAL_TESTS} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f" VALIDATION PASSED - All {TOTAL_TESTS} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
