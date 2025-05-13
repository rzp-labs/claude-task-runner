# Claude Task Runner

A specialized tool to manage context isolation and focused task execution with Claude Code, solving the critical challenge of context length limitations and task focus when working with Claude on complex, multi-step projects.

## What is Claude Task Runner?

Claude Task Runner solves a fundamental challenge when working with Large Language Models like Claude on complex projects: context length limitations and maintaining focus on the current task.

## The Problem

When working with Claude Code (or any LLM) on complex projects, you typically face several challenges:

- **Context Length Limitations**: Claude has a limited context window. Long, complex projects can exceed this limit.
- **Task Switching Confusion**: When handling multiple tasks in a single conversation, Claude may get confused about which task it's currently working on.
- **Project Organization**: Large projects need structure and organization to track progress.
- **Effective Prompting**: Each task requires specific, focused instructions to get optimal results.

## The Solution: Boomerang Mode

Claude Task Runner implements a "Boomerang" approach:

- **Task Breakdown**: It analyzes a large project specification and intelligently breaks it down into smaller, self-contained tasks.
- **Context Isolation**: Each task is executed in a clean context window, ensuring Claude focuses solely on that task.
- **Project Organization**: Tasks are organized into projects with proper sequencing and metadata.
- **Execution Management**: Tasks can be run individually or in sequence, with results captured and organized.

## Why Use Claude Task Runner?

- **Overcome Context Limitations**: Break down large projects into manageable chunks that fit within Claude's context window.
- **Maintain Focus**: Ensure Claude stays focused on the current task without being distracted by previous context.
- **Improve Quality**: Get better results by providing Claude with clear, focused instructions for each task.
- **Organize Complex Projects**: Manage multi-step projects with proper structure and sequencing.
- **Track Progress**: Monitor task completion and project status.
- **MCP Integration**: Seamlessly integrate with agent workflows through the Model Context Protocol.

## Prerequisites

This package requires the following to be installed on your system:

- **Claude Desktop** - You need to have Claude Desktop application installed
- **Claude Code** - The `claude` command-line tool must be accessible in your PATH
- **Desktop Commander** - Required for file system access (see installation instructions below)

### Installing Desktop Commander

Desktop Commander is a critical dependency that enables Claude to access your file system and execute commands. To install:

```bash
# Using npx (recommended)
npx @wonderwhy-er/desktop-commander@latest setup

# Or using Smithery
npx -y @smithery/cli install @wonderwhy-er/desktop-commander --client claude
```

After installation, restart Claude Desktop and ensure you see the hammer icon in the chat interface, indicating that Desktop Commander is properly connected.

## Core Features

- **Task Breakdown**: Parse complex projects into focused, self-contained tasks
- **Context Isolation**: Execute each task with a clean context window
- **Project Management**: Organize tasks into projects with proper metadata
- **Execution Control**: Run tasks individually or in sequence, with result management
- **Status Tracking**: Monitor project progress and task completion status
- **Modern CLI**: Intuitive command-line interface with rich formatting
- **MCP Integration**: Seamless integration with agent workflows via FastMCP

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/grahama1970/claude_task_runner.git
cd claude_task_runner

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

For FastMCP integration, you'll need to install the `fastmcp` package:

```bash
pip install fastmcp
```

### Basic Usage

1. **Create a task list** (see `examples/sample_task_list.md` for a template)
2. **Create a project and parse tasks**:
   ```bash
   python -m task_runner create my_project /path/to/task_list.md
   ```
3. **Run all tasks**:
   ```bash
   python -m task_runner run --base-dir ~/claude_task_runner
   ```
4. **Check status**:
   ```bash
   python -m task_runner status
   ```

### Quick Demo

For a quick demonstration of Claude Task Runner, we've included a sample demo:

```bash
# Make the demo script executable
chmod +x run_demo.sh

# Run the demo
./run_demo.sh
```

This will:
- Create a sample project
- Parse a task list into individual task files
- Run all tasks with Claude
- Show real-time progress and results

For more detailed instructions, see the [Quick Start Guide](docs/QUICKSTART.md).

## Command Line Interface

```bash
# Create a new project
python -m task_runner create my_project /path/to/task_list.md

# Run all tasks in a project
python -m task_runner run --base-dir ~/claude_task_runner

# Show status of all tasks
python -m task_runner status --base-dir ~/claude_task_runner

# Clean up any running processes
python -m task_runner clean --base-dir ~/claude_task_runner

# JSON output for machine-readable results
python -m task_runner status --json
```

## Python API

```python
from task_runner.core.task_manager import TaskManager
from pathlib import Path

# Initialize the task manager
manager = TaskManager(Path('~/claude_task_runner').expanduser())

# Parse a task list
task_files = manager.parse_task_list(Path('tasks.md'))

# Run all tasks
results = manager.run_all_tasks()

# Get task status
status = manager.get_task_status()
```

## MCP Server

The Task Runner can be used as an MCP server, allowing it to be accessed by Claude and other AI agents:

```bash
# Start the server with default settings
python scripts/run_task_runner_server.py start

# Start with custom settings
python scripts/run_task_runner_server.py start --host 0.0.0.0 --port 5000 --debug

# Check server health
python scripts/run_task_runner_server.py health

# Show server info
python scripts/run_task_runner_server.py info

# Display server schema
python scripts/run_task_runner_server.py schema
```

The server exposes the following MCP functions:

- `run_task` - Run a single task with context isolation
- `run_all_tasks` - Run all tasks in a project
- `parse_task_list` - Break down a task list into individual task files
- `create_project` - Create a new project
- `get_task_status` - Get the status of all tasks
- `get_task_summary` - Get summary statistics of all tasks
- `clean` - Clean up any running processes

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Task Format Guide](docs/TASK_FORMAT.md)
- [Contributing Guide](CONTRIBUTING.md)

## Project Structure

```
claude_task_runner/
├── src/
│   └── task_runner/
│       ├── core/           # Core business logic
│       │   └── task_manager.py
│       ├── presentation/   # UI components
│       │   └── formatters.py
│       ├── cli.py          # CLI interface
│       └── mcp/            # MCP integration
│           ├── schema.py
│           ├── wrapper.py
│           └── mcp_server.py
├── scripts/                # Utility scripts
├── tests/                  # Test files
├── docs/                   # Documentation
├── examples/               # Example files
└── pyproject.toml          # Project configuration
```

## Development

```bash
# Set up development environment
make dev

# Run tests
make test

# Format code
make format

# Run linting checks
make lint

# Start MCP server
make mcp-server
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Requirements

- Python 3.10+
- Claude Desktop with Desktop Commander enabled
- `claude` command-line tool accessible in your PATH
- `typer` and `rich` Python packages (automatically installed)
- `fastmcp` package (for MCP integration)

## License

This project is licensed under the MIT License - see the LICENSE file for details.