# Claude Task Runner Quick Start Guide

This guide will help you get started with Claude Task Runner quickly.

## Prerequisites

Ensure you have:
- Python 3.10+ installed
- Claude Desktop installed
- Claude Code (`claude` command-line tool) accessible in your PATH
- Desktop Commander installed and visible in Claude Desktop (hammer icon)

### Installing Desktop Commander

Desktop Commander is required for file system access:

```bash
# Using npx (recommended)
npx @wonderwhy-er/desktop-commander@latest setup

# Or using Smithery
npx -y @smithery/cli install @wonderwhy-er/desktop-commander --client claude
```

After installation, restart Claude Desktop and ensure you see the hammer icon in the chat interface.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/grahama1970/claude_task_runner.git
   cd claude_task_runner
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the package**:
   ```bash
   pip install -e .
   ```

## Basic Commands

Here are the core commands you'll use with Claude Task Runner:

### Creating a Project

```bash
# Using module syntax
python -m task_runner create <project_name> <task_list_file>

# Using installed script (after pip install)
task-runner create <project_name> <task_list_file>
```

Parameters:
- `<project_name>`: Name of your project folder
- `<task_list_file>`: Path to your markdown file containing tasks

Example:
```bash
python -m task_runner create my_project input/sample_tasks.md
```

### Running Tasks

```bash
# Using module syntax
python -m task_runner run [--base-dir <directory>] [--timeout <seconds>] [--quick-demo] [--debug-claude] [--no-streaming]

# Using installed script (after pip install)
task-runner run [--base-dir <directory>] [--timeout <seconds>] [--quick-demo] [--debug-claude] [--no-streaming]
```

Parameters:
- `--base-dir`: Base directory containing the tasks (default: ~/claude_task_runner)
- `--timeout`: Maximum execution time per task in seconds (default: 300)
- `--quick-demo`: Use simulated responses instead of actual Claude API
- `--debug-claude`: Enable detailed Claude debugging and timing logs
- `--no-pool`: Disable Claude process pooling (creates new process for each task)
- `--pool-size`: Maximum number of Claude processes to keep in the pool (default: 3)
- `--no-streaming`: Disable real-time output streaming (uses simple file redirection)

Examples:
```bash
# Run with real-time streaming output (default)
python -m task_runner run input/sample_tasks.md --base-dir ./debug_project --debug-claude

# Run with simple file redirection (faster, but no real-time output)
python -m task_runner run input/sample_tasks.md --base-dir ./debug_project --no-streaming
```

The first command:
1. Runs tasks from the task list in input/sample_tasks.md
2. Uses ./debug_project as the base directory
3. Enables detailed Claude timing and debugging logs
4. Uses real-time streaming output to see Claude's progress line-by-line

The second command:
1. Runs tasks with faster simple file redirection
2. Output is only visible when each task is complete
3. May be 10-15% faster but doesn't show real-time progress

### Checking Status

```bash
# Using module syntax
python -m task_runner status [--base-dir <directory>] [--json]

# Using installed script (after pip install)
task-runner status [--base-dir <directory>] [--json]
```

Parameters:
- `--base-dir`: Base directory containing the tasks (default: ~/claude_task_runner)
- `--json`: Output status in JSON format

Example:
```bash
python -m task_runner status --base-dir ./debug_project
```

### Cleaning Up Processes

```bash
# Using module syntax
python -m task_runner clean [--base-dir <directory>]

# Using installed script (after pip install)
task-runner clean [--base-dir <directory>]
```

Parameters:
- `--base-dir`: Base directory containing the tasks (default: ~/claude_task_runner)

Example:
```bash
python -m task_runner clean --base-dir ./debug_project
```

## Real-time Output Streaming

Claude Task Runner provides real-time streaming of Claude's output, which gives:
- Immediate visibility into Claude's thinking process
- Line-by-line output as it's being generated
- Better diagnostics for issues or errors
- More informative progress updates

This streaming functionality is enabled by default for all task executions. If you prefer faster execution with slightly less overhead, you can disable streaming with the `--no-streaming` flag, which uses simple file redirection instead. This approach may be 10-15% faster but won't show real-time progress.

## Running With Simulated Responses

If you've reached Claude's usage limit or want to test without using API quota:

```bash
python -m task_runner run --base-dir ./debug_project --quick-demo
```

This will generate realistic simulated responses for each task type based on the task name.

## Step By Step Workflow

### 1. Create a Task List

Create a Markdown file with your tasks:

```markdown
# My Project

## Task 1: First Task
Details for the first task...

## Task 2: Second Task
Details for the second task...
```

Save this as `tasks.md`.

### 2. Create a Project

```bash
# Using module syntax
python -m task_runner create my_project tasks.md

# Using installed script
task-runner create my_project tasks.md
```

This will:
- Create a project directory structure
- Parse the task list into individual task files
- Set up tracking for task status

### 3. Run the Tasks

```bash
# Using module syntax
python -m task_runner run --base-dir ./my_project

# Using installed script
task-runner run --base-dir ./my_project
```

This will:
- Execute each task in sequence with Claude
- Display a progress dashboard with real-time streaming output
- Store the results for each task in the results directory

For debugging Claude timing issues:
```bash
# Using module syntax
python -m task_runner run --base-dir ./my_project --debug-claude

# Using installed script
task-runner run --base-dir ./my_project --debug-claude
```

### 4. Check Status

```bash
# Using module syntax
python -m task_runner status --base-dir ./my_project

# Using installed script
task-runner status --base-dir ./my_project
```

This will show the status of all tasks, including which are completed, failed, or pending.

## JSON Output for Integration

For machine-readable output format:

```bash
# Using module syntax
python -m task_runner status --base-dir ./my_project --json | python -m json.tool

# Using installed script
task-runner status --base-dir ./my_project --json | python -m json.tool
```

## Task List Format

Task lists are Markdown files with a simple structure:

```markdown
# Project Title

Project description and overview...

## Task 1: Task Title
Task details and instructions...

## Task 2: Another Task Title
More task details...
```

The format requirements are:
- Start with a project title using a single # heading
- Each task should start with a ## heading
- Task headings should follow the format: `## Task N: Title`
- Tasks will be processed in order

## Using the MCP Server

1. **Start the MCP server**:
   ```bash
   # Using module syntax
   python -m task_runner mcp start

   # Using installed script
   task-runner mcp start
   ```

2. **Add to your .mcp.json file**:
   ```json
   {
     "mcpServers": {
       "task_runner": {
         "command": "/usr/bin/env",
         "args": [
           "python",
           "scripts/run_task_runner_server.py",
           "start"
         ]
       }
     }
   }
   ```

3. **Use from Claude**:
   You can now access Task Runner functions directly from Claude.

## Next Steps

- Review the [Task Format Guide](TASK_FORMAT.md) to learn how to structure your tasks effectively
- Explore the [README.md](../README.md) for more advanced usage
- See the [CONTRIBUTING.md](../CONTRIBUTING.md) if you want to contribute to the project

## Troubleshooting

- **Claude not found**: Ensure the `claude` command is available in your PATH
- **Desktop Commander not connected**: Restart Claude Desktop and check for the hammer icon
- **Claude usage limit reached**: Use `--quick-demo` flag to test with simulated output
- **Task execution fails**: Check the error logs in the results directory
- **Task execution times out**: Claude may take longer than expected to process complex tasks; adjust timeout with `--timeout` option
- **Processes remain after interruption**: Run `python -m task_runner clean --base-dir ./my_project` to clean up any remaining processes
- **Slow performance**: Try the `--no-streaming` flag for faster execution, or adjust process pooling and context reuse options
- **Unexpected task order**: Ensure your task numbering is correct in the task list file