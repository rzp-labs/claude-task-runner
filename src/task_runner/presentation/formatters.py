#!/usr/bin/env python3
"""
Formatters for Task Runner CLI

This module provides rich formatting utilities for the CLI presentation layer.
It includes tables, panels, progress indicators, and other UI components
for a better user experience.

This module is part of the Presentation Layer and should only depend on
Core Layer components, not on Integration Layer.

Links:
- Rich library documentation: https://rich.readthedocs.io/
- Rich tables: https://rich.readthedocs.io/en/stable/tables.html
- Rich panels: https://rich.readthedocs.io/en/stable/panel.html
- Rich progress: https://rich.readthedocs.io/en/stable/progress.html

Sample input:
- Task status dictionaries
- Execution results
- Error messages

Expected output:
- Rich formatted tables, panels, and progress indicators
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Sequence

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from loguru import logger


# Initialize console
console = Console()


# Color scheme
COLORS = {
    "completed": "green",
    "failed": "red",
    "timeout": "yellow",
    "running": "blue",
    "pending": "white",
    "highlight": "cyan",
    "dim": "grey70",
}


def create_status_table(task_state: Dict[str, Dict[str, Any]], current_task: Optional[str] = None,
                        current_task_start_time: Optional[float] = None) -> Table:
    """
    Create a rich table with current task status
    
    Args:
        task_state: Dictionary of task states
        current_task: Name of the currently running task
        current_task_start_time: Start time of the current task
        
    Returns:
        Rich table with task status
    """
    table = Table(title="Task Status")
    # Enable hyperlinks in the table
    table.caption = "[dim]Tasks are clickable links to their files[/dim]"
    
    table.add_column("Task", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Started", style="green")
    table.add_column("Completed", style="green")
    table.add_column("Time (s)", justify="right")
    table.add_column("Exit Code", justify="right")
    table.add_column("Result", style="blue", justify="center")
    
    for task_name, state in sorted(task_state.items()):
        status = state.get("status", "unknown")
        started = state.get("started_at", "")
        completed = state.get("completed_at", "")
        
        # Format timestamps for display
        if started:
            try:
                started = datetime.fromisoformat(started).strftime("%H:%M:%S")
            except:
                pass
            
        if completed:
            try:
                completed = datetime.fromisoformat(completed).strftime("%H:%M:%S")
            except:
                pass
        
        # Calculate current execution time for running tasks
        execution_time = state.get("execution_time", "")
        if status == "running" and current_task == task_name and current_task_start_time:
            execution_time = float(datetime.now().timestamp() - current_task_start_time)
            execution_time = f"{execution_time:.1f}"
        elif execution_time != "":
            execution_time = f"{execution_time:.1f}"
        
        # Determine row style based on status
        if status == "completed":
            status_style = COLORS["completed"]
        elif status == "failed":
            status_style = COLORS["failed"]
        elif status == "timeout":
            status_style = COLORS["timeout"]
        elif status == "running":
            status_style = COLORS["running"]
        else:
            status_style = COLORS["pending"]
        
        # Format task name with link and status highlighting
        file_path = state.get("task_file", "")
        if file_path:
            # Make task name a clickable link to the file
            task_display = f"[link=file://{file_path}]{task_name}[/link]"
        else:
            task_display = task_name
            
        # Add bold styling for running task
        if status == "running":
            task_display = f"[bold blue]{task_display}[/bold blue]"
        
        exit_code = state.get("exit_code", "")
        if exit_code == "":
            exit_code = ""
            
        # Add result link if completed
        result_link = ""
        result_file = state.get("result_file", "")
        if status == "completed" and result_file:
            result_link = f"[link=file://{result_file}]View[/link]"
        
        table.add_row(
            task_display,
            f"[{status_style}]{status}[/{status_style}]",
            started,
            completed,
            execution_time,
            str(exit_code),
            result_link
        )
    
    return table


def create_current_task_panel(task_state: Dict[str, Dict[str, Any]], current_task: Optional[str] = None,
                              current_task_start_time: Optional[float] = None) -> Panel:
    """
    Create a panel showing details of the current task
    
    Args:
        task_state: Dictionary of task states
        current_task: Name of the currently running task
        current_task_start_time: Start time of the current task
        
    Returns:
        Rich panel with current task details
    """
    if not current_task or current_task not in task_state:
        return Panel("No task is currently running", title="Current Task")
    
    state = task_state[current_task]
    task_title = state.get("title", current_task)
    
    # Calculate execution time
    execution_time = "0.0"
    if current_task_start_time:
        execution_time = f"{float(datetime.now().timestamp() - current_task_start_time):.1f}"
    
    # Get process info
    process_id = state.get("process_id", "")
    child_count = len(state.get("child_processes", []))
    
    content = f"""
[bold cyan]Task:[/bold cyan] {task_title}
[bold cyan]Status:[/bold cyan] [blue]RUNNING[/blue]
[bold cyan]Started:[/bold cyan] {datetime.fromisoformat(state.get('started_at', datetime.now().isoformat())).strftime('%H:%M:%S')}
[bold cyan]Running for:[/bold cyan] {execution_time} seconds
[bold cyan]Process ID:[/bold cyan] {process_id} (with {child_count} child processes)
    """
    
    return Panel(content, title=f"Current Task: {current_task}")


def create_summary_panel(task_state: Dict[str, Dict[str, Any]]) -> Panel:
    """
    Create a panel with summary statistics
    
    Args:
        task_state: Dictionary of task states
        
    Returns:
        Rich panel with summary statistics
    """
    total = len(task_state)
    completed = sum(1 for state in task_state.values() if state.get("status") == "completed")
    failed = sum(1 for state in task_state.values() if state.get("status") == "failed")
    timeout = sum(1 for state in task_state.values() if state.get("status") == "timeout")
    pending = sum(1 for state in task_state.values() if state.get("status") == "pending")
    running = sum(1 for state in task_state.values() if state.get("status") == "running")
    
    content = f"""
[bold green]Completed:[/bold green] {completed}
[bold red]Failed:[/bold red] {failed}
[bold yellow]Timed out:[/bold yellow] {timeout}
[bold blue]Running:[/bold blue] {running}
[bold]Pending:[/bold] {pending}
[bold]Total:[/bold] {total}
    """
    
    completion_pct = 0
    if total > 0:
        completion_pct = int((completed + failed + timeout) / total * 100)
    
    return Panel(content, title=f"Summary: {completion_pct}% Complete")


def create_progress() -> Progress:
    """
    Create a progress indicator
    
    Returns:
        Rich progress indicator
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold green]{task.completed}/{task.total}"),
        TimeElapsedColumn(),
    )


def print_error(message: str, title: str = "Error") -> None:
    """
    Format and print error message to the console
    
    Args:
        message: Error message
        title: Panel title
    """
    panel = Panel(
        Text(message, style=COLORS["failed"]),
        title=f"[bold {COLORS['failed']}]{title}",
        border_style=COLORS["failed"],
        padding=(1, 2)
    )
    
    console.print(panel)


def print_warning(message: str, title: str = "Warning") -> None:
    """
    Format and print warning message to the console
    
    Args:
        message: Warning message
        title: Panel title
    """
    panel = Panel(
        Text(message, style=COLORS["timeout"]),
        title=f"[bold {COLORS['timeout']}]{title}",
        border_style=COLORS["timeout"],
        padding=(1, 2)
    )
    
    console.print(panel)


def print_info(message: str, title: str = "Info") -> None:
    """
    Format and print info message to the console
    
    Args:
        message: Info message
        title: Panel title
    """
    panel = Panel(
        Text(message, style=COLORS["running"]),
        title=f"[bold {COLORS['running']}]{title}",
        border_style=COLORS["running"],
        padding=(1, 2)
    )
    
    console.print(panel)


def print_success(message: str, title: str = "Success") -> None:
    """
    Format and print success message to the console
    
    Args:
        message: Success message
        title: Panel title
    """
    panel = Panel(
        Text(message, style=COLORS["completed"]),
        title=f"[bold {COLORS['completed']}]{title}",
        border_style=COLORS["completed"],
        padding=(1, 2)
    )
    
    console.print(panel)


def print_json(data: Dict[str, Any]) -> None:
    """
    Print formatted JSON data
    
    Args:
        data: Data to print as JSON
    """
    console.print(json.dumps(data, indent=2))


def create_dashboard(task_state: Dict[str, Dict[str, Any]], current_task: Optional[str] = None,
                     current_task_start_time: Optional[float] = None) -> List[Any]:
    """
    Create dashboard components for display
    
    Args:
        task_state: Dictionary of task states
        current_task: Name of the currently running task
        current_task_start_time: Start time of the current task
        
    Returns:
        List of Rich components (panels and tables)
    """
    # Create components
    current_task_panel = create_current_task_panel(task_state, current_task, current_task_start_time)
    status_table = create_status_table(task_state, current_task, current_task_start_time)
    summary_panel = create_summary_panel(task_state)
    
    # Return components as a list for individual rendering
    return [current_task_panel, status_table, summary_panel]


if __name__ == "__main__":
    """Validate formatters"""
    import sys
    import time
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Create status table
    total_tests += 1
    try:
        # Sample task state
        task_state = {
            "001_task_one": {
                "status": "completed",
                "started_at": "2023-01-01T10:00:00",
                "completed_at": "2023-01-01T10:05:00",
                "execution_time": 300,
                "exit_code": 0
            },
            "002_task_two": {
                "status": "running",
                "started_at": "2023-01-01T10:10:00"
            },
            "003_task_three": {
                "status": "pending"
            }
        }
        
        # Test with current task
        status_table = create_status_table(task_state, "002_task_two", time.time() - 60)
        
        # Verify table has expected columns
        expected_columns = ["Task", "Status", "Started", "Completed", "Time (s)", "Exit Code"]
        if len(status_table.columns) != len(expected_columns):
            all_validation_failures.append(f"Status table has {len(status_table.columns)} columns, expected {len(expected_columns)}")
        
        # Test without current task
        status_table_no_current = create_status_table(task_state)
        
        console.print("\nTest status table:")
        console.print(status_table)
    except Exception as e:
        all_validation_failures.append(f"Create status table test failed: {e}")
    
    # Test 2: Create current task panel
    total_tests += 1
    try:
        current_task_panel = create_current_task_panel(task_state, "002_task_two", time.time() - 60)
        
        # Test with no current task
        no_task_panel = create_current_task_panel(task_state)
        
        console.print("\nTest current task panel:")
        console.print(current_task_panel)
        console.print("\nTest no task panel:")
        console.print(no_task_panel)
    except Exception as e:
        all_validation_failures.append(f"Create current task panel test failed: {e}")
    
    # Test 3: Create summary panel
    total_tests += 1
    try:
        summary_panel = create_summary_panel(task_state)
        
        console.print("\nTest summary panel:")
        console.print(summary_panel)
    except Exception as e:
        all_validation_failures.append(f"Create summary panel test failed: {e}")
    
    # Test 4: Print messages
    total_tests += 1
    try:
        print_error("This is an error message")
        print_warning("This is a warning message")
        print_info("This is an info message")
        print_success("This is a success message")
        
        sample_data = {
            "tasks": {
                "001_task_one": {"status": "completed"},
                "002_task_two": {"status": "running"}
            },
            "summary": {
                "total": 2,
                "completed": 1,
                "running": 1
            }
        }
        
        console.print("\nTest JSON output:")
        print_json(sample_data)
    except Exception as e:
        all_validation_failures.append(f"Print messages test failed: {e}")
    
    # Test 5: Create dashboard
    total_tests += 1
    try:
        dashboard = create_dashboard(task_state, "002_task_two", time.time() - 60)
        
        console.print("\nTest dashboard:")
        console.print(dashboard)
    except Exception as e:
        all_validation_failures.append(f"Create dashboard test failed: {e}")
    
    # Test 6: Create progress
    total_tests += 1
    try:
        with create_progress() as progress:
            task = progress.add_task("Testing progress...", total=100)
            for i in range(101):
                progress.update(task, completed=i)
                time.sleep(0.01)
    except Exception as e:
        all_validation_failures.append(f"Create progress test failed: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"L VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f" VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)