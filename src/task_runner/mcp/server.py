#!/usr/bin/env python3
"""
MCP Server Entry Point for Task Runner

This module serves as the entry point for the Task Runner MCP server.
It imports and re-exports the functionality from mcp_server.py.
"""

import sys
from typing import Any, Dict

import typer

from task_runner.mcp.mcp_server import (
    configure_logging,
    get_server_info,
    health_check,
)

app = typer.Typer(help="Task Runner MCP Server")


@app.command()
def start(host: str = "localhost", port: int = 3000, debug: bool = False) -> None:
    """Start the MCP server."""
    # Configure logging
    log_level = "DEBUG" if debug else "INFO"
    configure_logging(log_level)

    # Create and run the MCP server
    try:
        from task_runner.mcp.wrapper import create_mcp_server

        mcp = create_mcp_server()

        if mcp is None:
            print("Failed to create MCP server")
            sys.exit(1)

        # Start server
        mcp.run(transport="streamable-http", host=host, port=port)

    except KeyboardInterrupt:
        print("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Server failed to start: {str(e)}")
        sys.exit(1)


@app.command()
def health() -> None:
    """Check server health."""
    import json

    result = health_check()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "healthy" else 1)


@app.command()
def info() -> None:
    """Display server information."""
    import json

    info_data = get_server_info()
    print(json.dumps(info_data, indent=2))
    sys.exit(0)


@app.command()
def schema(json_output: bool = False) -> None:
    """Display server schema."""
    import json

    import anyio

    from task_runner.mcp.wrapper import create_mcp_server

    mcp = create_mcp_server()

    if mcp is None:
        print(json.dumps({"error": "Failed to create MCP server"}, indent=2))
        sys.exit(1)

    # Get tools using anyio
    tools = anyio.run(mcp.get_tools)

    # Format into a schema-like structure for compatibility
    schema_data: Dict[str, Any] = {"functions": {}}

    for tool_name, tool in tools.items():
        tool_info: Dict[str, Any] = {
            "description": tool.description or "No description",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

        # Process parameters if available
        if hasattr(tool, "parameters"):
            # In FastMCP 2.3.5, the parameters structure is different:
            # It has 'properties', 'required', and 'type' at the top level
            if isinstance(tool.parameters, dict):
                # Copy the properties if they exist
                if "properties" in tool.parameters and isinstance(
                    tool.parameters["properties"], dict
                ):
                    for param_name, param_info in tool.parameters["properties"].items():
                        param_type = param_info.get("type", "string")
                        param_desc = param_info.get(
                            "description", param_info.get("title", "No description")
                        )

                        tool_info["parameters"]["properties"][param_name] = {
                            "type": param_type,
                            "description": param_desc,
                        }

                # Copy the required fields if they exist
                if "required" in tool.parameters and isinstance(tool.parameters["required"], list):
                    tool_info["parameters"]["required"] = tool.parameters["required"]

        schema_data["functions"][tool_name] = tool_info

    if json_output:
        print(json.dumps(schema_data, indent=2))
    else:
        print("Available functions:")
        for function_name, function_info in schema_data["functions"].items():
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

    sys.exit(0)


if __name__ == "__main__":
    app()
