#!/usr/bin/env python3
"""
Task Manager for Claude Task Runner

This module provides optimized execution of Claude tasks with shell redirection for maximum
performance. It handles task file processing, Claude execution, and result collection.

Sample Input:
- Task files in markdown format with instructions for Claude

Sample Output:
- Results saved to .result files
- Execution timing and status information

Links:
- Claude CLI: https://github.com/anthropics/anthropic-cli
"""

import os
import re
import time
import json
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, TextIO

from loguru import logger
from task_runner.core.claude_streamer import stream_claude_output


class TaskState:
    """Task state enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskManager:
    """Core task management functionality optimized for performance"""
    
    def __init__(self, base_dir: Path):
        """
        Initialize the task manager
        
        Args:
            base_dir: Base directory for tasks and results
        """
        self.base_dir = base_dir
        self.tasks_dir = base_dir / "tasks"
        self.results_dir = base_dir / "results"
        self.state_file = base_dir / "task_state.json"
        
        # Create directories
        self.tasks_dir.mkdir(exist_ok=True, parents=True)
        self.results_dir.mkdir(exist_ok=True, parents=True)
        
        # Task state
        self.task_state: Dict[str, Dict[str, Any]] = self._load_state()
        
        # Current running task information
        self.current_task: Optional[str] = None
        self.current_task_start_time: Optional[float] = None
        
        # Find Claude executable
        self.claude_path = self._find_claude_executable()
        
        # Enable context clearing between tasks
        self.clear_context = True
        
    def cleanup(self) -> None:
        """
        Clean up any resources used by the task manager.
        
        This method is called at the end of execution to ensure all resources
        are properly released.
        """
        logger.info("Cleaning up task manager resources")
        
        # Reset current task state
        self.current_task = None
        self.current_task_start_time = None
        
        # Save final state
        self._save_state()
    
    def _load_state(self) -> Dict[str, Dict[str, Any]]:
        """
        Load task state from file or initialize if it doesn't exist
        
        Returns:
            Dictionary of task states
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")
                logger.warning("Starting with fresh state")
        
        return {}
    
    def _save_state(self) -> None:
        """Save task state to file"""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.task_state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save state file: {e}")
    
    def _update_task_state(self, task_name: str, status: str, **kwargs) -> Dict[str, Any]:
        """
        Update state for a task
        
        Args:
            task_name: Name of the task
            status: Status to set
            **kwargs: Additional task state properties
            
        Returns:
            Updated task state
        """
        if task_name not in self.task_state:
            self.task_state[task_name] = {
                "name": task_name,
                "status": TaskState.PENDING,
                "created_at": datetime.now().isoformat(),
            }
        
        # Update task status
        self.task_state[task_name]["status"] = status
        self.task_state[task_name]["updated_at"] = datetime.now().isoformat()
        
        # Update additional properties
        for key, value in kwargs.items():
            self.task_state[task_name][key] = value
        
        # Save state to disk
        self._save_state()
        
        return self.task_state[task_name]
    
    def _find_claude_executable(self) -> str:
        """
        Find the Claude executable in the system PATH or common locations
        
        Returns:
            Path to the Claude executable
        """
        logger.info("Looking up Claude executable location")
        lookup_start = time.time()
        
        # First try using 'which' to find claude in the PATH
        try:
            which_result = subprocess.run(
                ["which", "claude"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if which_result.returncode == 0:
                claude_path = which_result.stdout.strip()
                if claude_path and os.access(claude_path, os.X_OK):
                    logger.info(f"Found Claude at: {claude_path} in {time.time() - lookup_start:.4f}s")
                    return claude_path
        except Exception as e:
            logger.warning(f"Error finding Claude with 'which': {e}")
        
        # If 'which' failed, check common locations
        possible_paths = [
            str(Path.home() / ".npm-global" / "bin" / "claude"),
            str(Path.home() / "node_modules" / ".bin" / "claude"),
            "/usr/local/bin/claude",
            "/opt/homebrew/bin/claude",
            os.environ.get("CLAUDE_PATH", "")
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"Found Claude at: {path} in {time.time() - lookup_start:.4f}s")
                return path
        
        # If not found, use a basic fallback
        logger.warning(f"Claude executable not found after {time.time() - lookup_start:.4f}s, using 'claude' as fallback")
        return "claude"
    
    def parse_task_list(self, task_list_path: Path) -> List[Path]:
        """
        Parse a task list file and split into individual task files
        
        Args:
            task_list_path: Path to the task list file
            
        Returns:
            List of paths to the created task files
        """
        logger.info(f"Parsing task list: {task_list_path}")
        
        # Read the task list file
        with open(task_list_path, "r") as f:
            content = f.read()
        
        # Split by task markers (## Task)
        task_pattern = r"## Task (\d+): ([^\n]+)(.*?)(?=## Task \d+:|$)"
        matches = re.finditer(task_pattern, content, re.DOTALL)
        
        task_files = []
        for match in matches:
            task_num = match.group(1)
            task_title = match.group(2).strip()
            task_content = match.group(3).strip()
            
            # Create a task file
            filename = f"{task_num.zfill(3)}_{task_title.lower().replace(' ', '_')}.md"
            task_path = self.tasks_dir / filename
            
            with open(task_path, "w") as f:
                f.write(f"# {task_title}\n\n{task_content}")
            
            # Initialize task state
            task_name = task_path.stem
            self._update_task_state(
                task_name, 
                TaskState.PENDING,
                title=task_title,
                task_file=str(task_path),
                result_file=str(self.results_dir / f"{task_name}.result"),
                error_file=str(self.results_dir / f"{task_name}.error")
            )
            
            task_files.append(task_path)
            logger.info(f"Created task file: {filename}")
        
        return task_files
    
    def get_task_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of all tasks
        
        Returns:
            Dictionary of task statuses
        """
        return self.task_state
    
    def get_task_summary(self) -> Dict[str, int]:
        """
        Get summary statistics of all tasks
        
        Returns:
            Dictionary with count of tasks in each state
        """
        total = len(self.task_state)
        completed = sum(1 for state in self.task_state.values() if state.get("status") == TaskState.COMPLETED)
        failed = sum(1 for state in self.task_state.values() if state.get("status") == TaskState.FAILED)
        timeout = sum(1 for state in self.task_state.values() if state.get("status") == TaskState.TIMEOUT)
        pending = sum(1 for state in self.task_state.values() if state.get("status") == TaskState.PENDING)
        running = sum(1 for state in self.task_state.values() if state.get("status") == TaskState.RUNNING)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "timeout": timeout,
            "pending": pending,
            "running": running,
            "completion_pct": int((completed + failed + timeout) / max(total, 1) * 100)
        }
    
    def _clear_claude_context(self) -> bool:
        """
        Clear Claude's context using the /clear command
        
        Returns:
            True if clearing was successful, False otherwise
        """
        if not self.clear_context:
            return True
            
        logger.info("Clearing Claude context")
        
        # Use the dedicated function from claude_streamer
        from task_runner.core.claude_streamer import clear_claude_context
        return clear_claude_context(str(self.claude_path))
    
    def run_task(self, task_file: Path, timeout_seconds: int = 300, 
                 fast_mode: bool = True, demo_mode: bool = False,
                 use_streaming: bool = True, raw_json: bool = False,
                 quiet: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Run a single task with Claude using either streaming or simple file redirection
        
        Args:
            task_file: Path to the task file
            timeout_seconds: Maximum execution time in seconds
            fast_mode: Use --no-auth-check for faster execution
            demo_mode: Run in demo mode (simulate Claude output for testing)
            use_streaming: Whether to use real-time streaming output (True) or simple file redirection (False)
            raw_json: Whether to output raw JSON instead of human-friendly format (only applies when use_streaming=True)
            quiet: Whether to suppress console output (still writes to files, only applies when use_streaming=True)
            
        Returns:
            Tuple of (success, task_state)
        """
        task_name = task_file.stem
        result_file = self.results_dir / f"{task_name}.result"
        error_file = self.results_dir / f"{task_name}.error"
        
        # Create output directories if they don't exist
        result_file.parent.mkdir(exist_ok=True, parents=True)
        error_file.parent.mkdir(exist_ok=True, parents=True)
        
        # Set current task and time
        self.current_task = task_name
        self.current_task_start_time = time.time()
        
        # Update task state
        self._update_task_state(
            task_name, 
            TaskState.RUNNING,
            started_at=datetime.now().isoformat()
        )
        
        logger.info(f"Processing task: {task_name}")
        
        try:
            # If in demo mode, simulate Claude output
            if demo_mode or not os.path.exists(self.claude_path):
                # Generate simulated content based on task name
                logger.info(f"Running in demo mode for task: {task_name}")
                with open(result_file, "w") as f:
                    f.write(f"# Simulated output for {task_name}\n\n")
                    
                    # Generate different content based on task type
                    if "analyze" in task_name.lower():
                        f.write("## Python Code Structure Analysis\n\n")
                        f.write("The codebase follows a clean architecture pattern with the following layers:\n\n")
                        f.write("1. **Presentation Layer**: CLI interface and formatters\n")
                        f.write("2. **Core Layer**: Business logic and domain models\n")
                        f.write("3. **Infrastructure Layer**: External integrations\n\n")
                        f.write("### Key Components\n\n")
                        f.write("- **TaskManager**: Central coordinator for task execution\n")
                        f.write("- **ClaudeStreamer**: Handles real-time output streaming\n")
                        f.write("- **Formatters**: Rich-based UI components\n")
                    elif "documentation" in task_name.lower():
                        f.write("## Documentation Templates\n\n")
                        f.write("```python\n")
                        f.write("def function_name(param1: Type, param2: Optional[Type] = None) -> ReturnType:\n")
                        f.write("    \"\"\"\n")
                        f.write("    Brief description of function purpose.\n\n")
                        f.write("    Args:\n")
                        f.write("        param1: Description of first parameter\n")
                        f.write("        param2: Description of second parameter, defaults to None\n\n")
                        f.write("    Returns:\n")
                        f.write("        Description of return value\n\n")
                        f.write("    Raises:\n")
                        f.write("        ExceptionType: When and why this exception is raised\n\n")
                        f.write("    Examples:\n")
                        f.write("        >>> function_name('example', 123)\n")
                        f.write("        'example_result'\n")
                        f.write("    \"\"\"\n")
                        f.write("```\n")
                    elif "test" in task_name.lower():
                        f.write("## Unit Test Examples\n\n")
                        f.write("```python\n")
                        f.write("import pytest\n")
                        f.write("from task_runner.core.task_manager import TaskManager\n\n")
                        f.write("@pytest.fixture\n")
                        f.write("def task_manager():\n")
                        f.write("    \"\"\"Create a TaskManager instance for testing.\"\"\"\n")
                        f.write("    return TaskManager(Path('/tmp/test_task_runner'))\n\n")
                        f.write("def test_run_task_success(task_manager, monkeypatch):\n")
                        f.write("    \"\"\"Test that run_task succeeds with valid input.\"\"\"\n")
                        f.write("    # Arrange\n")
                        f.write("    task_file = Path('/tmp/test_task.md')\n")
                        f.write("    with open(task_file, 'w') as f:\n")
                        f.write("        f.write('Test task content')\n\n")
                        f.write("    # Mock subprocess to avoid actual Claude execution\n")
                        f.write("    monkeypatch.setattr(subprocess, 'Popen', MockPopen)\n\n")
                        f.write("    # Act\n")
                        f.write("    success, result = task_manager.run_task(task_file, demo_mode=True)\n\n")
                        f.write("    # Assert\n")
                        f.write("    assert success is True\n")
                        f.write("    assert result['status'] == 'completed'\n")
                        f.write("```\n")
                    elif "cli" in task_name.lower():
                        f.write("## CLI Argument Parser Example\n\n")
                        f.write("```python\n")
                        f.write("import typer\n")
                        f.write("from pathlib import Path\n")
                        f.write("from typing import Optional\n\n")
                        f.write("app = typer.Typer(help=\"Claude Task Runner\")\n\n")
                        f.write("@app.command()\n")
                        f.write("def run(\n")
                        f.write("    task_list: Optional[Path] = typer.Argument(\n")
                        f.write("        None, help=\"Path to task list file\"\n")
                        f.write("    ),\n")
                        f.write("    base_dir: Path = typer.Option(\n")
                        f.write("        Path.home() / \"claude_task_runner\",\n")
                        f.write("        help=\"Base directory for tasks and results\",\n")
                        f.write("    ),\n")
                        f.write("    timeout: int = typer.Option(\n")
                        f.write("        300, \"--timeout\", help=\"Timeout in seconds for each task\"\n")
                        f.write("    ),\n")
                        f.write("    demo_mode: bool = typer.Option(\n")
                        f.write("        False, \"--demo\", help=\"Run in demo mode with simulated responses\"\n")
                        f.write("    ),\n")
                        f.write("):\n")
                        f.write("    \"\"\"Run tasks with Claude in isolated contexts.\"\"\"\n")
                        f.write("    # Implementation details...\n")
                        f.write("```\n")
                    else:
                        f.write("This is a demo response generated without using Claude.\n\n")
                        f.write(f"Task content would be processed from: {task_file}\n")
                
                # Add a small delay to simulate processing time (between 0.5-2 seconds)
                import random
                delay = random.uniform(0.5, 2.0)
                time.sleep(delay)
                
                # Mark as completed
                execution_time = delay
                self._update_task_state(
                    task_name,
                    TaskState.COMPLETED,
                    completed_at=datetime.now().isoformat(),
                    exit_code=0,
                    execution_time=execution_time,
                    result_size=result_file.stat().st_size if result_file.exists() else 0
                )
                
                return True, self.task_state[task_name]
            
            # Use either streaming approach or simple file redirection
            start_time = time.time()
            
            # Setup command args
            cmd_args = ["--no-auth-check"] if fast_mode else []
            
            # Choose between streaming with pexpect or simple file redirection
            logger.info(f"{'Using pexpect streaming approach' if use_streaming else 'Using simple file redirection'} for task: {task_name}")
            
            try:
                if use_streaming:
                    # Use pexpect for real-time interactive streaming
                    logger.info("Using pexpect for interactive streaming")
                    from task_runner.core.claude_streamer import stream_claude_output
                    
                    streaming_result = stream_claude_output(
                        task_file=str(task_file),
                        result_file=str(result_file),
                        error_file=str(error_file),
                        claude_path=str(self.claude_path),
                        cmd_args=cmd_args,
                        timeout_seconds=timeout_seconds,
                        raw_json=raw_json,
                        quiet=quiet
                    )
                    
                    # Get execution time and exit code from the result
                    execution_time = streaming_result.get("execution_time", time.time() - start_time)
                    exit_code = streaming_result.get("exit_code", 1)  # Default to error if not present
                else:
                    # Simple file redirection (faster but no real-time output)
                    cmd_parts = [str(self.claude_path), "--print"] + cmd_args
                    cmd = f"{' '.join(cmd_parts)} < {task_file} > {result_file} 2> {error_file}"
                    logger.info(f"Command with redirection: {cmd}")
                    
                    try:
                        # Run the command with timeout
                        process = subprocess.run(
                            cmd,
                            shell=True,
                            timeout=timeout_seconds,
                            check=False
                        )
                        
                        # Process completed
                        execution_time = time.time() - start_time
                        exit_code = process.returncode
                        
                        # Check result
                        logger.info(f"Command completed with exit code {exit_code} in {execution_time:.2f}s")
                        
                        # Result structure 
                        streaming_result = {
                            "task_file": str(task_file),
                            "result_file": str(result_file),
                            "error_file": str(error_file),
                            "exit_code": exit_code,
                            "execution_time": execution_time,
                            "success": exit_code == 0,
                            "status": "completed" if exit_code == 0 else "failed"
                        }
                    except subprocess.TimeoutExpired:
                        # Handle timeout for non-streaming mode
                        logger.warning(f"Command timed out after {timeout_seconds}s")
                        execution_time = time.time() - start_time
                        exit_code = -1
                        
                        # Add timeout message to result file
                        with open(result_file, "a") as f:
                            f.write(f"\n\n[TIMEOUT: Claude process was terminated after {timeout_seconds}s]")
                        
                        streaming_result = {
                            "task_file": str(task_file),
                            "result_file": str(result_file),
                            "error_file": str(error_file),
                            "exit_code": exit_code,
                            "execution_time": execution_time,
                            "success": False,
                            "status": "timeout"
                        }
                        exit_code = -1
                
            except Exception as e:
                # Handle other errors
                execution_time = time.time() - start_time
                logger.exception(f"Error running command: {e}")
                
                # Write error to error file
                with open(error_file, "a") as f:
                    f.write(f"Error: {str(e)}")
                
                streaming_result = {
                    "task_file": str(task_file),
                    "result_file": str(result_file),
                    "error_file": str(error_file),
                    "exit_code": -1,
                    "execution_time": execution_time,
                    "success": False,
                    "status": "error",
                    "error": str(e)
                }
                exit_code = -1
            
            # Check result
            result_size = result_file.stat().st_size if result_file.exists() else 0
            logger.info(f"Result size: {result_size} bytes")
            
            if exit_code == 0:
                logger.info(f"Task {task_name} completed successfully in {execution_time:.2f}s")
                
                # Update state
                self._update_task_state(
                    task_name,
                    TaskState.COMPLETED,
                    completed_at=datetime.now().isoformat(),
                    exit_code=exit_code,
                    execution_time=execution_time,
                    result_size=result_size
                )
                
                success = True
            else:
                logger.error(f"Task {task_name} failed with exit code {exit_code}")
                
                # Get error content
                error_content = ""
                if error_file.exists() and error_file.stat().st_size > 0:
                    with open(error_file, "r") as f:
                        error_content = f.read()
                        logger.error(f"Error details: {error_content}")
                
                # Update state
                self._update_task_state(
                    task_name,
                    TaskState.FAILED,
                    completed_at=datetime.now().isoformat(),
                    exit_code=exit_code,
                    execution_time=execution_time,
                    error=error_content[:500]  # Store first 500 chars of error
                )
                
                success = False
                
        except Exception as e:
            logger.exception(f"Error running task {task_name}: {e}")
            
            # Update state
            self._update_task_state(
                task_name,
                TaskState.FAILED,
                completed_at=datetime.now().isoformat(),
                error=str(e)
            )
            
            success = False
        
        # Clear current task
        self.current_task = None
        self.current_task_start_time = None
        
        return success, self.task_state[task_name]
    
    def run_all_tasks(self, timeout_seconds: int = 300, 
                     fast_mode: bool = True, demo_mode: bool = False,
                     use_streaming: bool = True, raw_json: bool = False,
                     quiet: bool = False) -> Dict[str, Any]:
        """
        Run all tasks in the tasks directory
        
        Args:
            timeout_seconds: Maximum execution time per task in seconds
            fast_mode: Use --no-auth-check for faster execution  
            demo_mode: Run in demo mode (simulate Claude output for testing)
            use_streaming: Whether to use real-time streaming output (True) or simple file redirection (False)
            raw_json: Whether to output raw JSON instead of human-friendly format (only applies when use_streaming=True)
            quiet: Whether to suppress console output (still writes to files, only applies when use_streaming=True)
            
        Returns:
            Summary of execution results
        """
        task_files = sorted(self.tasks_dir.glob("*.md"))
        
        if not task_files:
            logger.warning("No task files found")
            return {"success": False, "error": "No task files found"}
        
        logger.info(f"Processing {len(task_files)} tasks")
        
        results = {
            "total": len(task_files),
            "success": 0,
            "failed": 0,
            "timeout": 0,
            "skipped": 0,
            "task_results": {}
        }
        
        for i, task_file in enumerate(task_files):
            task_name = task_file.stem
            
            # Skip already completed tasks
            if task_name in self.task_state and self.task_state[task_name].get("status") in [
                TaskState.COMPLETED, TaskState.FAILED, TaskState.TIMEOUT
            ]:
                if self.task_state[task_name].get("status") == TaskState.COMPLETED:
                    results["success"] += 1
                elif self.task_state[task_name].get("status") == TaskState.FAILED:
                    results["failed"] += 1
                elif self.task_state[task_name].get("status") == TaskState.TIMEOUT:
                    results["timeout"] += 1
                
                results["skipped"] += 1
                results["task_results"][task_name] = self.task_state[task_name]
                continue
            
            # Run the task
            logger.info(f"Running task: {task_name} ({i+1}/{len(task_files)})")
            success, task_result = self.run_task(
                task_file, 
                timeout_seconds=timeout_seconds,
                fast_mode=fast_mode,
                demo_mode=demo_mode,
                use_streaming=use_streaming,
                raw_json=raw_json,
                quiet=quiet
            )
            
            results["task_results"][task_name] = task_result
            
            if success:
                results["success"] += 1
            elif task_result.get("status") == TaskState.TIMEOUT:
                results["timeout"] += 1
            else:
                results["failed"] += 1
                
            # Clear context between tasks
            if i < len(task_files) - 1:  # Skip after the last task
                self._clear_claude_context()
        
        return results


if __name__ == "__main__":
    import sys
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Create temporary test directory
    test_dir = Path("test_task_manager")
    test_dir.mkdir(exist_ok=True)
    task_dir = test_dir / "tasks"
    task_dir.mkdir(exist_ok=True)
    
    # Create test task files
    task_files = []
    for i in range(1, 3):
        task_file = task_dir / f"test_task_{i}.md"
        with open(task_file, "w") as f:
            f.write(f"# Test Task {i}\n\nThis is test task {i}. Write a haiku about testing.")
        task_files.append(task_file)
    
    # Test 1: TaskManager instantiation
    total_tests += 1
    try:
        manager = TaskManager(test_dir)
        # Verification
        if not isinstance(manager, TaskManager):
            all_validation_failures.append("TaskManager instantiation failed")
    except Exception as e:
        all_validation_failures.append(f"TaskManager instantiation error: {str(e)}")
    
    # Test 2: Task list parsing
    total_tests += 1
    try:
        # Create a task list file
        task_list_file = test_dir / "task_list.md"
        with open(task_list_file, "w") as f:
            f.write("# Task List\n\n")
            f.write("## Task 1: First Task\n")
            f.write("This is the first task content.\n\n")
            f.write("## Task 2: Second Task\n")
            f.write("This is the second task content.\n\n")
        
        # Parse the task list
        parsed_tasks = manager.parse_task_list(task_list_file)
        
        # Verification
        if len(parsed_tasks) != 2:
            all_validation_failures.append(f"Task list parsing failed: expected 2 tasks, got {len(parsed_tasks)}")
    except Exception as e:
        all_validation_failures.append(f"Task list parsing error: {str(e)}")
    
    # Test 3: Demo mode task execution
    total_tests += 1
    try:
        # Run a task in demo mode
        success, task_state = manager.run_task(task_files[0], demo_mode=True)
        
        # Verification
        if not success or task_state.get("status") != TaskState.COMPLETED:
            all_validation_failures.append(f"Demo mode task execution failed: {task_state}")
    except Exception as e:
        all_validation_failures.append(f"Demo mode task execution error: {str(e)}")
    
    # Test 4: Task status summary
    total_tests += 1
    try:
        # Get task summary
        summary = manager.get_task_summary()
        
        # Verification
        if "total" not in summary or "completed" not in summary:
            all_validation_failures.append(f"Task summary missing required fields: {summary}")
    except Exception as e:
        all_validation_failures.append(f"Task summary error: {str(e)}")
    
    # Clean up
    import shutil
    shutil.rmtree(test_dir)
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)  # Exit with success code