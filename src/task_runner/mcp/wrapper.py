#!/usr/bin/env python3
"""
MCP Wrapper for Task Runner

This module provides the FastMCP integration for the Task Runner,
wrapping the core functions to make them available via MCP.

This module is part of the Integration Layer and can depend on both
Core Layer and Presentation Layer components.

Links:
- FastMCP: https://github.com/anthropics/fastmcp

Sample input:
- MCP function calls

Expected output:
- MCP-compatible function responses
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from loguru import logger

try:
    from fastmcp import FastMCP
except ImportError:
    logger.error("fastmcp is not installed. Install it with: pip install fastmcp")
    FastMCP = None

from task_runner.core.task_manager import TaskManager
from task_runner.mcp.schema import get_complete_schema


def format_response(success: bool, data: Optional[Dict[str, Any]] = None, 
                   error: Optional[str] = None) -> Dict[str, Any]:
    """
    Format a response for MCP
    
    Args:
        success: Whether the request was successful
        data: Data to include in the response
        error: Error message if the request failed
        
    Returns:
        MCP-compatible response
    """
    response = {"success": success}
    
    if success and data is not None:
        response.update(data)
    elif not success and error is not None:
        response["error"] = error
    
    return response


def run_task_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP handler for running a single task
    
    Args:
        request: MCP request
        
    Returns:
        MCP-compatible response
    """
    try:
        # Get parameters
        task_path = request.get("task_path")
        base_dir = request.get("base_dir", str(Path.home() / "claude_task_runner"))
        timeout_seconds = request.get("timeout_seconds", 300)
        
        # Validate parameters
        if not task_path:
            return format_response(False, error="Missing required parameter: task_path")
        
        # Ensure paths are Path objects
        task_path = Path(task_path)
        base_dir = Path(base_dir)
        
        # Check that task file exists
        if not task_path.exists():
            return format_response(False, error=f"Task file not found: {task_path}")
        
        # Initialize task manager
        manager = TaskManager(base_dir)
        
        # Run task
        success, task_result = manager.run_task(task_path, timeout_seconds)
        
        # Format response
        return format_response(success, data={"task_result": task_result})
    
    except Exception as e:
        logger.exception(f"Error in run_task_handler: {e}")
        return format_response(False, error=f"Error running task: {str(e)}")


def run_all_tasks_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP handler for running all tasks
    
    Args:
        request: MCP request
        
    Returns:
        MCP-compatible response
    """
    try:
        # Get parameters
        base_dir = request.get("base_dir", str(Path.home() / "claude_task_runner"))
        resume = request.get("resume", False)
        
        # Ensure base_dir is a Path object
        base_dir = Path(base_dir)
        
        # Initialize task manager
        manager = TaskManager(base_dir)
        
        # Run all tasks
        results = manager.run_all_tasks()
        
        # Format response
        return format_response(True, data=results)
    
    except Exception as e:
        logger.exception(f"Error in run_all_tasks_handler: {e}")
        return format_response(False, error=f"Error running tasks: {str(e)}")


def parse_task_list_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP handler for parsing a task list
    
    Args:
        request: MCP request
        
    Returns:
        MCP-compatible response
    """
    try:
        # Get parameters
        task_list_path = request.get("task_list_path")
        base_dir = request.get("base_dir", str(Path.home() / "claude_task_runner"))
        
        # Validate parameters
        if not task_list_path:
            return format_response(False, error="Missing required parameter: task_list_path")
        
        # Ensure paths are Path objects
        task_list_path = Path(task_list_path)
        base_dir = Path(base_dir)
        
        # Check that task list file exists
        if not task_list_path.exists():
            return format_response(False, error=f"Task list file not found: {task_list_path}")
        
        # Initialize task manager
        manager = TaskManager(base_dir)
        
        # Parse task list
        task_files = manager.parse_task_list(task_list_path)
        
        # Format response
        return format_response(True, data={
            "task_files": [str(f) for f in task_files],
            "count": len(task_files)
        })
    
    except Exception as e:
        logger.exception(f"Error in parse_task_list_handler: {e}")
        return format_response(False, error=f"Error parsing task list: {str(e)}")


def create_project_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP handler for creating a project
    
    Args:
        request: MCP request
        
    Returns:
        MCP-compatible response
    """
    try:
        # Get parameters
        project_name = request.get("project_name")
        task_list_path = request.get("task_list_path")
        base_dir = request.get("base_dir", str(Path.home() / "claude_task_runner"))
        
        # Validate parameters
        if not project_name:
            return format_response(False, error="Missing required parameter: project_name")
        
        # Ensure paths are Path objects
        base_dir = Path(base_dir)
        project_dir = base_dir / project_name
        
        # Initialize task manager for this project
        manager = TaskManager(project_dir)
        
        # Parse task list if provided
        if task_list_path:
            task_list_path = Path(task_list_path)
            
            # Check that task list file exists
            if not task_list_path.exists():
                return format_response(False, error=f"Task list file not found: {task_list_path}")
            
            # Parse task list
            task_files = manager.parse_task_list(task_list_path)
            
            # Format response
            return format_response(True, data={
                "project": project_name,
                "project_dir": str(project_dir),
                "task_files": [str(f) for f in task_files],
                "count": len(task_files)
            })
        else:
            # Just create the project structure
            return format_response(True, data={
                "project": project_name,
                "project_dir": str(project_dir),
                "message": "Project structure created. Use a task list to add tasks."
            })
    
    except Exception as e:
        logger.exception(f"Error in create_project_handler: {e}")
        return format_response(False, error=f"Error creating project: {str(e)}")


def get_task_status_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP handler for getting task status
    
    Args:
        request: MCP request
        
    Returns:
        MCP-compatible response
    """
    try:
        # Get parameters
        base_dir = request.get("base_dir", str(Path.home() / "claude_task_runner"))
        
        # Ensure base_dir is a Path object
        base_dir = Path(base_dir)
        
        # Initialize task manager
        manager = TaskManager(base_dir)
        
        # Get task status
        task_state = manager.get_task_status()
        
        # Format response
        return format_response(True, data={"tasks": task_state})
    
    except Exception as e:
        logger.exception(f"Error in get_task_status_handler: {e}")
        return format_response(False, error=f"Error getting task status: {str(e)}")


def get_task_summary_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP handler for getting task summary
    
    Args:
        request: MCP request
        
    Returns:
        MCP-compatible response
    """
    try:
        # Get parameters
        base_dir = request.get("base_dir", str(Path.home() / "claude_task_runner"))
        
        # Ensure base_dir is a Path object
        base_dir = Path(base_dir)
        
        # Initialize task manager
        manager = TaskManager(base_dir)
        
        # Get task summary
        summary = manager.get_task_summary()
        
        # Format response
        return format_response(True, data={"summary": summary})
    
    except Exception as e:
        logger.exception(f"Error in get_task_summary_handler: {e}")
        return format_response(False, error=f"Error getting task summary: {str(e)}")


def clean_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP handler for cleaning up processes
    
    Args:
        request: MCP request
        
    Returns:
        MCP-compatible response
    """
    try:
        # Get parameters
        base_dir = request.get("base_dir", str(Path.home() / "claude_task_runner"))
        
        # Ensure base_dir is a Path object
        base_dir = Path(base_dir)
        
        # Initialize task manager
        manager = TaskManager(base_dir)
        
        # Clean up processes
        manager.cleanup()
        
        # Format response
        return format_response(True, data={"message": "Cleaned up all processes"})
    
    except Exception as e:
        logger.exception(f"Error in clean_handler: {e}")
        return format_response(False, error=f"Error cleaning up processes: {str(e)}")


def create_mcp_server() -> Optional[FastMCP]:
    """
    Create a FastMCP server for the Task Runner
    
    Returns:
        FastMCP server or None if FastMCP is not available
    """
    if FastMCP is None:
        logger.error("FastMCP is not available")
        return None
    
    # Create FastMCP server
    mcp = FastMCP(
        name="Task Runner",
        description="Run tasks with Claude in isolated contexts",
        schema_version="1.0",
    )
    
    # Register handlers
    mcp.register_function("run_task", run_task_handler)
    mcp.register_function("run_all_tasks", run_all_tasks_handler)
    mcp.register_function("parse_task_list", parse_task_list_handler)
    mcp.register_function("create_project", create_project_handler)
    mcp.register_function("get_task_status", get_task_status_handler)
    mcp.register_function("get_task_summary", get_task_summary_handler)
    mcp.register_function("clean", clean_handler)
    
    # Set schema
    mcp.set_schema(get_complete_schema())
    
    return mcp


def mcp_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top-level MCP handler for the Task Runner
    
    Args:
        request: MCP request
        
    Returns:
        MCP-compatible response
    """
    mcp = create_mcp_server()
    
    if mcp is None:
        return {"error": "FastMCP is not available"}
    
    return mcp.handle_request(request)


if __name__ == "__main__":
    """Validate MCP wrapper"""
    import sys
    
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<level>{level}: {message}</level>",
        level="INFO",
        colorize=True
    )
    
    # If FastMCP is not available, exit with an error
    if FastMCP is None:
        logger.error("FastMCP is not installed. Install it with: pip install fastmcp")
        sys.exit(1)
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Create MCP server
    total_tests += 1
    try:
        mcp = create_mcp_server()
        
        if mcp is None:
            all_validation_failures.append("Failed to create MCP server")
        
        # Check that all handlers are registered
        schema = mcp.get_schema()
        expected_functions = [
            "run_task",
            "run_all_tasks",
            "parse_task_list",
            "create_project",
            "get_task_status",
            "get_task_summary",
            "clean"
        ]
        
        for func in expected_functions:
            if func not in schema["functions"]:
                all_validation_failures.append(f"Function '{func}' not registered in MCP server")
        
        print("MCP Schema:")
        print(json.dumps(schema, indent=2))
    except Exception as e:
        all_validation_failures.append(f"Create MCP server test failed: {e}")
    
    # Test 2: Format response
    total_tests += 1
    try:
        # Test success response
        success_response = format_response(True, data={"message": "Success"})
        if not success_response.get("success") or "message" not in success_response:
            all_validation_failures.append("Success response format incorrect")
        
        # Test error response
        error_response = format_response(False, error="Error message")
        if error_response.get("success") or error_response.get("error") != "Error message":
            all_validation_failures.append("Error response format incorrect")
        
        print("\nSuccess response:")
        print(json.dumps(success_response, indent=2))
        print("\nError response:")
        print(json.dumps(error_response, indent=2))
    except Exception as e:
        all_validation_failures.append(f"Format response test failed: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"L VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f" VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)