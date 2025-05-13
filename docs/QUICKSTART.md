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

## Quick Demo

For a quick demonstration of Claude Task Runner, we've included a sample demo:

```bash
# Make the demo script executable
chmod +x run_demo.sh

# Run the demo
./run_demo.sh
```

This will:
- Create a sample project called "sample_project"
- Parse a task list from input/sample_tasks.md into individual task files
- Run all tasks with Claude (this may take several minutes)
- Show results and task status

**Note:** If you want to stop the task execution early, you can press Ctrl+C at any time. The system will clean up any running processes.

## Step by Step Usage

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
python -m task_runner create my_project tasks.md
```

This will:
- Create a project directory structure
- Parse the task list into individual task files
- Set up tracking for task status

### 3. Run the Tasks

```bash
python -m task_runner run --base-dir ./my_project
```

This will:
- Execute each task in sequence with Claude
- Display a progress dashboard (may not render properly in all terminals)
- Store the results for each task in the results directory

Alternatively, you can use the JSON output format for more reliable output:
```bash
python -m task_runner run --base-dir ./my_project --json
```

### 4. Check Status

```bash
python -m task_runner status --base-dir ./my_project
```

This will show the status of all tasks, including which are completed, failed, or pending.

For a more reliable output format, especially in CI/CD environments or when scripting, use the JSON output:

```bash
python -m task_runner status --base-dir ./my_project --json | python -m json.tool
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

## JSON Output

You can get machine-readable JSON output by adding the `--json` flag:

```bash
python -m task_runner status --json
python -m task_runner run --json
```

## Using the MCP Server

1. **Start the MCP server**:
   ```bash
   python scripts/run_task_runner_server.py start
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
- **Task execution fails**: Check the error logs in the results directory
- **Layout doesn't render properly**: Some terminals may not display Rich layouts correctly. Use the `--json` flag for a more reliable output
- **Task execution times out**: Claude may take longer than expected to process complex tasks. You can modify the timeout in the code if needed
- **Processes remain after interruption**: Run `python -m task_runner clean --base-dir ./my_project` to clean up any remaining processes