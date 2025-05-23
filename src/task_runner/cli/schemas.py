#!/usr/bin/env python3
"""
Schemas for Task Runner CLI

This module provides data models and schema definitions for the CLI,
ensuring consistent type checking and data validation.

This module is part of the CLI Layer and should only depend on
Core Layer components, not on Integration Layer.

Sample input:
- Raw data structures

Expected output:
- Validated and typed data structures
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class TaskState(str, Enum):
    """Task state enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


def format_cli_response(
    success: bool, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format a standard CLI response structure

    Args:
        success: Whether the operation was successful
        data: Optional data to include in the response
        error: Optional error message

    Returns:
        Formatted response dictionary
    """
    response: Dict[str, Any] = {"success": success}

    if data:
        response["data"] = data

    if error:
        response["error"] = error

    return response


def generate_cli_schema() -> Dict[str, Any]:
    """
    Generate a schema for the CLI commands and options

    Returns:
        Schema dictionary
    """
    return {
        "commands": {
            "run": {
                "help": "Run tasks with Claude in isolated contexts",
                "parameters": {
                    "task_list": {
                        "type": "path",
                        "required": False,
                        "help": "Path to task list file. If not provided, uses existing task files.",
                    },
                    "base_dir": {
                        "type": "path",
                        "default": "~/claude_task_runner",
                        "help": "Base directory for tasks and results",
                    },
                    "claude_path": {
                        "type": "string",
                        "required": False,
                        "help": "Path to Claude executable",
                    },
                    "resume": {
                        "type": "boolean",
                        "default": False,
                        "help": "Resume from previously interrupted tasks",
                    },
                    "json_output": {
                        "type": "boolean",
                        "default": False,
                        "help": "Output results as JSON",
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 300,
                        "help": "Timeout in seconds for each task (default: 300s)",
                    },
                    "quick_demo": {
                        "type": "boolean",
                        "default": False,
                        "help": "Run a quick demo with simulated responses",
                    },
                    "debug_claude": {
                        "type": "boolean",
                        "default": False,
                        "help": "Debug Claude launch performance with detailed timing logs",
                    },
                    "no_pool": {
                        "type": "boolean",
                        "default": False,
                        "help": "Disable Claude process pooling (creates new process for each task)",
                    },
                    "pool_size": {
                        "type": "integer",
                        "default": 3,
                        "help": "Maximum number of Claude processes to keep in the pool",
                    },
                    "reuse_context": {
                        "type": "boolean",
                        "default": True,
                        "help": "Reuse Claude processes with /clear command between tasks",
                    },
                    "no_streaming": {
                        "type": "boolean",
                        "default": False,
                        "help": "Disable real-time output streaming (uses simple file redirection)",
                    },
                    "no_table_repeat": {
                        "type": "boolean",
                        "default": False,
                        "help": "Display the table only once, don't repeat after each task (better with streaming)",
                    },
                    "dangerous": {
                        "type": "boolean",
                        "default": False,
                        "help": "Use --dangerously-skip-permissions to bypass Claude permission checks (skip_permissions parameter)",
                    },
                },
            },
            "status": {
                "help": "Show status of all tasks",
                "parameters": {
                    "base_dir": {
                        "type": "path",
                        "default": "~/claude_task_runner",
                        "help": "Base directory for tasks and results",
                    },
                    "json_output": {
                        "type": "boolean",
                        "default": False,
                        "help": "Output results as JSON",
                    },
                },
            },
            "create": {
                "help": "Create a new project from a task list",
                "parameters": {
                    "project_name": {
                        "type": "string",
                        "required": True,
                        "help": "Name of the project",
                    },
                    "task_list": {
                        "type": "path",
                        "required": False,
                        "help": "Path to task list file",
                    },
                    "base_dir": {
                        "type": "path",
                        "default": "~/claude_task_runner",
                        "help": "Base directory for tasks and results",
                    },
                    "json_output": {
                        "type": "boolean",
                        "default": False,
                        "help": "Output results as JSON",
                    },
                },
            },
            "clean": {
                "help": "Clean up any running processes",
                "parameters": {
                    "base_dir": {
                        "type": "path",
                        "default": "~/claude_task_runner",
                        "help": "Base directory for tasks and results",
                    },
                    "json_output": {
                        "type": "boolean",
                        "default": False,
                        "help": "Output results as JSON",
                    },
                },
            },
        }
    }
