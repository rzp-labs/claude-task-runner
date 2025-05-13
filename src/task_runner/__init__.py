"""
Task Runner for Claude

This package provides functionality for running Claude tasks in isolated contexts,
allowing better management of long task lists with proper state tracking.

Core components:
- Core layer: Pure business logic for task management
- Presentation layer: CLI and formatting for user interaction
- MCP layer: Integration with Model Context Protocol

Usage examples:
```python
from task_runner.core.task_manager import TaskManager
from pathlib import Path

# Initialize task manager
manager = TaskManager(Path("~/claude_task_runner").expanduser())

# Parse a task list
task_files = manager.parse_task_list(Path("tasks.md"))

# Run all tasks
results = manager.run_all_tasks()

# Check task status
status = manager.get_task_status()
```

For CLI usage, see the README.md file.
"""

__version__ = "0.1.0"