#!/usr/bin/env python3
"""
Main entry point for the task_runner module.

This module is used when running the module as a script:
python -m task_runner <command> [args]
"""

import sys

from loguru import logger

from task_runner.cli.app import app

if __name__ == "__main__":
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<level>{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {function}:{line} - {message}</level>",
        level="INFO",  # Show INFO level logs to diagnose performance issues
        colorize=True,
    )

    app()
