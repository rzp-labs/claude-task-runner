"""
Claude Task Runner

A specialized tool to manage context isolation and focused task execution with Claude Code,
solving the critical challenge of context length limitations and task focus when working
with Claude on complex, multi-step projects.
"""

from task_runner.cli.app import app as app  # Explicit re-export

__version__ = "0.1.0"
