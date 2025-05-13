#!/usr/bin/env python3
"""
Command Line Interface for Task Runner

This module provides a CLI for the task runner functionality using Typer and Rich,
allowing users to manage and run isolated Claude tasks.

This module is part of the Presentation Layer and should only depend on
Core Layer components, not on Integration Layer.

Links:
- Typer: https://typer.tiangolo.com/
- Rich: https://rich.readthedocs.io/

Sample input:
- CLI command-line parameters

Expected output:
- Rich-formatted console output
- Task execution results
- Status information
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console

from task_runner.core.task_manager import TaskManager
from task_runner.presentation.formatters import (
    create_dashboard,
    print_error,
    print_info,
    print_success,
    print_warning,
    print_json
)


# Initialize typer app and rich console
app = typer.Typer(
    help="Claude Task Runner",
    rich_markup_mode="rich"
)

console = Console()


@app.command()
def run(
    task_list: Optional[Path] = typer.Argument(
        None, help="Path to task list file. If not provided, uses existing task files."
    ),
    base_dir: Path = typer.Option(
        Path.home() / "claude_task_runner",
        help="Base directory for tasks and results",
    ),
    claude_path: Optional[str] = typer.Option(
        None, help="Path to Claude executable"
    ),
    resume: bool = typer.Option(
        False, "--resume", help="Resume from previously interrupted tasks"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
    timeout: int = typer.Option(
        300, "--timeout", help="Timeout in seconds for each task (default: 300s)"
    ),
    quick_demo: bool = typer.Option(
        False, "--quick-demo", help="Run a quick demo with simulated responses"
    ),
    # Removed no_auth flag as it's not supported in the current Claude version
    debug_claude: bool = typer.Option(
        False, "--debug-claude", help="Debug Claude launch performance with detailed timing logs"
    ),
    no_pool: bool = typer.Option(
        False, "--no-pool", help="Disable Claude process pooling (creates new process for each task)"
    ),
    pool_size: int = typer.Option(
        3, "--pool-size", help="Maximum number of Claude processes to keep in the pool"
    ),
    reuse_context: bool = typer.Option(
        True, "--reuse-context", help="Reuse Claude processes with /clear command between tasks"
    ),
):
    """
    Run tasks with Claude in isolated contexts.
    
    This command can take a task list file, break it into separate tasks,
    and execute each with Claude in an isolated context.
    """
    if not json_output:
        print_info("Claude Task Runner", "Starting")
    
    # Initialize task manager
    manager = TaskManager(base_dir)
    
    # Override Claude path if provided
    if claude_path:
        manager.claude_path = Path(claude_path)
        
    # Set debug flag if provided
    if debug_claude:
        manager.debug_claude_launch = True
        logger.info("Debug mode enabled - detailed timing logs will be generated")
        
    # Set process pooling settings
    manager.use_process_pool = not no_pool
    TaskManager._max_pool_size = pool_size
    manager.reuse_context = reuse_context
    # Fast mode is no longer available with --no-auth-check removed
    
    # Log the process pooling configuration
    if not no_pool:
        logger.info(f"Using process pool with size {pool_size}, context reuse: {reuse_context}")
    else:
        logger.info("Process pooling disabled")
    
    try:
        # Parse task list if provided
        if task_list and not resume:
            if not task_list.exists():
                if json_output:
                    print_json({"error": f"Task list file not found: {task_list}"})
                else:
                    print_error(f"Task list file not found: {task_list}")
                raise typer.Exit(1)
            
            task_files = manager.parse_task_list(task_list)
            if not json_output:
                print_info(f"Created {len(task_files)} task files")
        
        # Run all tasks
        if json_output:
            # Run and output as JSON
            results = manager.run_all_tasks()
            print_json(results)
        else:
            # Run with interactive display
            task_files = sorted(manager.tasks_dir.glob("*.md"))
            
            if not task_files:
                print_error("No task files found")
                raise typer.Exit(1)
            
            print_info(f"Processing {len(task_files)} tasks:")
            
            # Process tasks with status updates
            for task_file in task_files:
                task_name = task_file.stem
                
                # Skip already processed tasks
                if task_name in manager.task_state and manager.task_state[task_name].get("status") in [
                    "completed", "failed", "timeout"
                ]:
                    continue
                
                # Show current status before running
                components = create_dashboard(
                    manager.task_state,
                    manager.current_task,
                    manager.current_task_start_time
                )
                
                # Display each component
                for component in components:
                    console.print(component)
                
                # Run the task
                # Use appropriate configuration based on options
                task_timeout = 30 if quick_demo else timeout
                success, _ = manager.run_task(task_file, task_timeout, fast_mode=False, demo_mode=quick_demo)
                
                # Show updated status after task completes
                print("\n\n")
                components = create_dashboard(
                    manager.task_state,
                    manager.current_task,
                    manager.current_task_start_time
                )
                
                # Display each component
                for component in components:
                    console.print(component)
                    
                    # Wait between tasks
                    import time
                    time.sleep(1)
            
            # Final status
            summary = manager.get_task_summary()
            print_success(
                f"Task execution complete: {summary['completed']}/{summary['total']} succeeded, "
                f"{summary['failed']} failed, {summary['timeout']} timed out"
            )
    
    except KeyboardInterrupt:
        if not json_output:
            print_warning("Interrupted by user")
        manager.cleanup()
        raise typer.Exit(130)
    
    except Exception as e:
        if json_output:
            print_json({"error": str(e)})
        else:
            print_error(f"Error: {str(e)}")
        manager.cleanup()
        raise typer.Exit(1)
    
    finally:
        # Always clean up processes
        manager.cleanup()


@app.command()
def status(
    base_dir: Path = typer.Option(
        Path.home() / "claude_task_runner",
        help="Base directory for tasks and results",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
):
    """Show status of all tasks"""
    # Initialize task manager
    manager = TaskManager(base_dir)
    
    # Get task status
    task_state = manager.get_task_status()
    summary = manager.get_task_summary()
    
    if json_output:
        print_json({
            "tasks": task_state,
            "summary": summary
        })
    else:
        # Display dashboard components
        components = create_dashboard(
            task_state,
            manager.current_task,
            manager.current_task_start_time
        )
        
        # Print each component separately
        for component in components:
            console.print(component)


@app.command()
def create(
    project_name: str = typer.Argument(..., help="Name of the project"),
    task_list: Optional[Path] = typer.Argument(
        None, help="Path to task list file"
    ),
    base_dir: Path = typer.Option(
        Path.home() / "claude_task_runner",
        help="Base directory for tasks and results",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
):
    """Create a new project from a task list"""
    # Create project directory
    project_dir = base_dir / project_name
    
    # Initialize task manager for this project
    manager = TaskManager(project_dir)
    
    try:
        if task_list:
            if not task_list.exists():
                if json_output:
                    print_json({"error": f"Task list file not found: {task_list}"})
                else:
                    print_error(f"Task list file not found: {task_list}")
                raise typer.Exit(1)
            
            # Parse task list
            task_files = manager.parse_task_list(task_list)
            
            if json_output:
                print_json({
                    "success": True,
                    "project": project_name,
                    "project_dir": str(project_dir),
                    "task_files": [str(f) for f in task_files],
                    "count": len(task_files)
                })
            else:
                print_success(
                    f"Project '{project_name}' created at {project_dir}\n"
                    f"Created {len(task_files)} task files"
                )
        else:
            # Just create the project structure
            if json_output:
                print_json({
                    "success": True,
                    "project": project_name,
                    "project_dir": str(project_dir),
                    "message": "Project structure created. Use a task list to add tasks."
                })
            else:
                print_success(
                    f"Project '{project_name}' created at {project_dir}\n"
                    f"Use a task list to add tasks."
                )
    
    except Exception as e:
        if json_output:
            print_json({"success": False, "error": str(e)})
        else:
            print_error(f"Error creating project: {str(e)}")
        raise typer.Exit(1)


@app.command()
def clean(
    base_dir: Path = typer.Option(
        Path.home() / "claude_task_runner",
        help="Base directory for tasks and results",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
):
    """Clean up any running processes"""
    # Initialize task manager
    manager = TaskManager(base_dir)
    
    # Cleanup processes
    manager.cleanup()
    
    if json_output:
        print_json({"success": True, "message": "Cleaned up all processes"})
    else:
        print_success("Cleaned up all processes")


if __name__ == "__main__":
    """CLI entry point for the task runner"""
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<level>{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {function}:{line} - {message}</level>",
        level="INFO",  # Show INFO level logs to diagnose performance issues
        colorize=True
    )
    
    app()