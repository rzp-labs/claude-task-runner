#!/usr/bin/env python3
"""
MCP Server for Task Runner

This is the main entry point for the Task Runner MCP server,
designed to be referenced in the .mcp.json configuration.

This module is part of the Integration Layer and connects
the MCP functionality to the application core.

Links:
- FastMCP: https://github.com/anthropics/fastmcp
- MCP Protocol: https://github.com/anthropics/model-context-protocol

Sample input:
- MCP server commands

Expected output:
- Running MCP server or command outputs
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger

from task_runner.mcp.wrapper import create_mcp_server


def ensure_log_directory() -> None:
    """Ensure log directory exists"""
    os.makedirs("logs", exist_ok=True)


def configure_logging(level: str = "INFO") -> None:
    """
    Configure logging with proper format and level
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    ensure_log_directory()
    
    # Remove default handlers
    logger.remove()
    
    # Add file logger
    logger.add(
        "logs/task_runner_mcp.log",
        rotation="10 MB",
        retention="1 week",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )
    
    # Add stderr logger for visible output
    logger.add(
        sys.stderr,
        format="<level>{level: <8}</level> | {message}",
        level=level,
        colorize=True
    )


def get_server_info() -> Dict[str, Any]:
    """
    Get server information
    
    Returns:
        Dict[str, Any]: Server information
    """
    return {
        "name": "Task Runner MCP Server",
        "version": "0.1.0",
        "description": "MCP server for running isolated Claude tasks",
        "author": "Graham Anderson",
        "github": "https://github.com/grahama1970/claude_boomerang",
    }


def health_check() -> Dict[str, Any]:
    """
    Perform a health check
    
    Returns:
        Dict[str, Any]: Health check results
    """
    import platform
    
    try:
        # Check if key dependencies are available
        import typer
        import rich
        import loguru
        
        # Check if fastmcp is available
        try:
            import fastmcp
            fastmcp_available = True
            fastmcp_version = getattr(fastmcp, "__version__", "unknown")
        except ImportError:
            fastmcp_available = False
            fastmcp_version = "not installed"
        
        # Check for Claude CLI
        try:
            import subprocess
            claude_result = subprocess.run(
                ["which", "claude"],
                capture_output=True,
                text=True,
                check=False
            )
            claude_available = claude_result.returncode == 0
            claude_path = claude_result.stdout.strip() if claude_available else "not found"
        except Exception:
            claude_available = False
            claude_path = "error checking"
        
        return {
            "status": "healthy",
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "typer_version": getattr(typer, "__version__", "unknown"),
            "rich_version": getattr(rich, "__version__", "unknown"),
            "loguru_version": getattr(loguru, "__version__", "unknown"),
            "fastmcp_available": fastmcp_available,
            "fastmcp_version": fastmcp_version,
            "claude_available": claude_available,
            "claude_path": claude_path,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def main() -> int:
    """
    Main entry point for the MCP server
    
    Returns:
        int: Exit code
    """
    parser = argparse.ArgumentParser(description="Task Runner MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start server command
    start_parser = subparsers.add_parser("start", help="Start the MCP server")
    start_parser.add_argument("--host", type=str, default="localhost", help="Host to listen on")
    start_parser.add_argument("--port", type=int, default=3000, help="Port to listen on")
    start_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check server health")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Display server information")
    
    # Schema command
    schema_parser = subparsers.add_parser("schema", help="Display server schema")
    schema_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "start":
        # Configure logging
        log_level = "DEBUG" if args.debug else "INFO"
        configure_logging(log_level)
        
        # Log startup info
        logger.info(f"Starting MCP server for Task Runner")
        logger.info(f"Host: {args.host}, Port: {args.port}, Debug: {args.debug}")
        
        try:
            # Create and run the MCP server
            mcp = create_mcp_server()
            
            if mcp is None:
                logger.error("Failed to create MCP server")
                return 1
            
            # Start server
            mcp.run_server(host=args.host, port=args.port)
            
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            return 0
        except Exception as e:
            logger.error(f"Server failed to start: {str(e)}", exc_info=True)
            return 1
    
    elif args.command == "health":
        # Run health check
        result = health_check()
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "healthy" else 1
    
    elif args.command == "info":
        # Show server info
        info = get_server_info()
        print(json.dumps(info, indent=2))
        return 0
    
    elif args.command == "schema":
        # Create server to get schema
        mcp = create_mcp_server()
        
        if mcp is None:
            print(json.dumps({"error": "Failed to create MCP server"}, indent=2))
            return 1
        
        # Get schema
        schema = mcp.get_schema()
        
        if args.json:
            print(json.dumps(schema, indent=2))
        else:
            print("Available functions:")
            for function_name, function_info in schema["functions"].items():
                print(f"\n[Function] {function_name}")
                print(f"  Description: {function_info.get('description', 'No description')}")
                
                # Get parameters
                params = function_info.get("parameters", {}).get("properties", {})
                required = function_info.get("parameters", {}).get("required", [])
                
                if params:
                    print("  Parameters:")
                    for param_name, param_info in params.items():
                        req = " (required)" if param_name in required else ""
                        param_type = param_info.get("type", "unknown")
                        description = param_info.get("description", "No description")
                        print(f"    {param_name}: {param_type}{req} - {description}")
        
        return 0
    
    return 0


if __name__ == "__main__":
    """
    Direct entry point for the Task Runner MCP server.
    This file is designed to be referenced in .mcp.json.
    
    Usage:
      python -m task_runner.mcp.mcp_server start [--host HOST] [--port PORT] [--debug]
      python -m task_runner.mcp.mcp_server health
      python -m task_runner.mcp.mcp_server info
      python -m task_runner.mcp.mcp_server schema [--json]
    """
    sys.exit(main())