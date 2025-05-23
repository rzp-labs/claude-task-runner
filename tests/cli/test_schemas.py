"""Tests for CLI schemas module"""

from task_runner.cli.schemas import TaskState, format_cli_response, generate_cli_schema


def test_format_cli_response_success_with_data():
    """Test that format_cli_response returns correct dict for success with data"""
    data = {"result": "success", "details": {"id": 123}}
    response = format_cli_response(True, data)
    assert isinstance(response, dict)
    assert response["success"] is True
    assert "data" in response
    assert response["data"] == data
    assert "error" not in response


def test_generate_cli_schema_includes_all_commands():
    """Test that generate_cli_schema returns a schema with all expected CLI commands"""
    schema = generate_cli_schema()
    assert isinstance(schema, dict)
    assert "commands" in schema
    commands = schema["commands"]
    expected_commands = {"run", "status", "create", "clean"}
    assert expected_commands.issubset(commands.keys())


def test_task_state_enum_values():
    """Test that TaskState enum contains all expected task states as string values"""
    expected_states = {
        "PENDING": "pending",
        "RUNNING": "running",
        "COMPLETED": "completed",
        "FAILED": "failed",
        "TIMEOUT": "timeout",
    }
    for attr, value in expected_states.items():
        assert hasattr(TaskState, attr)
        assert getattr(TaskState, attr).value == value


def test_generate_cli_schema_parameter_types_and_help():
    """Test that generate_cli_schema returns correct parameter types and help texts
    for each command"""
    schema = generate_cli_schema()
    commands = schema["commands"]

    # Expected structure: {command: {param: {"type": ..., "help": ...}}}
    expected_params = {
        "run": {
            "task_list": {
                "type": "path",
                "help": "Path to task list file. If not provided, uses existing task files",
            },
            "base_dir": {"type": "path", "help": "Base directory for tasks and results"},
            "claude_path": {"type": "string", "help": "Path to Claude executable"},
            "resume": {"type": "boolean", "help": "Resume from previously interrupted tasks"},
            "json_output": {"type": "boolean", "help": "Output results as JSON"},
            "timeout": {
                "type": "integer",
                "help": "Timeout in seconds for each task (default: 300s)",
            },
            "quick_demo": {"type": "boolean", "help": "Run a quick demo with simulated responses"},
            "debug_claude": {
                "type": "boolean",
                "help": "Debug Claude launch performance with detailed timing logs",
            },
            "no_pool": {
                "type": "boolean",
                "help": "Disable Claude process pooling (new process per task)",
            },
            "pool_size": {
                "type": "integer",
                "help": "Maximum number of Claude processes to keep in the pool",
            },
            "reuse_context": {
                "type": "boolean",
                "help": "Reuse Claude processes with /clear command between tasks",
            },
            "no_streaming": {
                "type": "boolean",
                "help": "Disable real-time output streaming (uses simple file redirection)",
            },
            "no_table_repeat": {
                "type": "boolean",
                "help": "Display table only once, no repeat after each task (better with streaming)",
            },
            "dangerous": {
                "type": "boolean",
                "help": "Use --dangerously-skip-permissions to bypass Claude permission checks",
            },
        },
        "status": {
            "base_dir": {"type": "path", "help": "Base directory for tasks and results"},
            "json_output": {"type": "boolean", "help": "Output results as JSON"},
        },
        "create": {
            "project_name": {"type": "string", "help": "Name of the project"},
            "task_list": {"type": "path", "help": "Path to task list file"},
            "base_dir": {"type": "path", "help": "Base directory for tasks and results"},
            "json_output": {"type": "boolean", "help": "Output results as JSON"},
        },
        "clean": {
            "base_dir": {"type": "path", "help": "Base directory for tasks and results"},
            "json_output": {"type": "boolean", "help": "Output results as JSON"},
        },
    }

    for command, params in expected_params.items():
        assert command in commands, f"Command '{command}' missing from schema"
        command_params = commands[command]["parameters"]
        for param, expected in params.items():
            assert param in command_params, f"Parameter '{param}' missing in command '{command}'"
            assert command_params[param]["type"] == expected["type"], (
                f"Parameter '{param}' in command '{command}' has type '{command_params[param]['type']}', "
                f"expected '{expected['type']}'"
            )
            assert command_params[param]["help"] == expected["help"], (
                f"Parameter '{param}' in command '{command}' has help '{command_params[param]['help']}', "
                f"expected '{expected['help']}'"
            )


def test_format_cli_response_error_case():
    """Test that format_cli_response returns a dict with 'error' key and
    success=False when called with an error message"""
    error_message = "Something went wrong"
    response = format_cli_response(False, error=error_message)
    assert isinstance(response, dict)
    assert response["success"] is False
    assert "error" in response
    assert response["error"] == error_message
    assert "data" not in response


def test_generate_cli_schema_default_parameter_values():
    """Test that generate_cli_schema returns default parameter values for commands
    when optional parameters are omitted"""
    schema = generate_cli_schema()
    commands = schema["commands"]

    # Check 'run' command defaults
    run_params = commands["run"]["parameters"]
    assert run_params["base_dir"]["default"] == "~/claude_task_runner"
    assert run_params["resume"]["default"] is False
    assert run_params["json_output"]["default"] is False
    assert run_params["timeout"]["default"] == 300
    assert run_params["quick_demo"]["default"] is False
    assert run_params["debug_claude"]["default"] is False
    assert run_params["no_pool"]["default"] is False
    assert run_params["pool_size"]["default"] == 3
    assert run_params["reuse_context"]["default"] is True
    assert run_params["no_streaming"]["default"] is False
    assert run_params["no_table_repeat"]["default"] is False
    assert run_params["dangerous"]["default"] is False

    # Check 'status' command defaults
    status_params = commands["status"]["parameters"]
    assert status_params["base_dir"]["default"] == "~/claude_task_runner"
    assert status_params["json_output"]["default"] is False

    # Check 'create' command defaults
    create_params = commands["create"]["parameters"]
    assert create_params["base_dir"]["default"] == "~/claude_task_runner"
    assert create_params["json_output"]["default"] is False

    # Check 'clean' command defaults
    clean_params = commands["clean"]["parameters"]
    assert clean_params["base_dir"]["default"] == "~/claude_task_runner"
    assert clean_params["json_output"]["default"] is False


def test_format_cli_response_minimal_input():
    """Test that format_cli_response returns only the 'success' key when neither
    data nor error is provided"""
    response = format_cli_response(True)
    assert isinstance(response, dict)
    assert set(response.keys()) == {"success"}
    assert response["success"] is True


def test_format_cli_response_with_data_and_error():
    """Test that format_cli_response handles both data and error arguments simultaneously"""
    data = {"foo": "bar"}
    error_message = "Something went wrong"
    response = format_cli_response(False, data=data, error=error_message)
    assert isinstance(response, dict)
    assert response["success"] is False
    assert "data" in response
    assert response["data"] == data
    assert "error" in response
    assert response["error"] == error_message


def test_format_cli_response_with_empty_data():
    """Test that format_cli_response handles empty data dictionaries correctly"""
    response = format_cli_response(True, data={})
    assert isinstance(response, dict)
    assert response["success"] is True
    assert "data" not in response  # Empty data is not included
    assert "error" not in response
