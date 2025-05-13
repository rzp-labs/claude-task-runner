#!/usr/bin/env python3
"""
Main entry point for running the task_runner module as a script.

This redirects to the CLI interface for ease of use.
"""

from task_runner.cli import app

if __name__ == "__main__":
    app()