#!/usr/bin/env python3
"""
Task Manager Core Functionality

This module provides the core business logic for managing isolated Claude tasks.
It handles task breakdown, execution, and state management with no UI dependencies.

Links:
- Path handling: https://docs.python.org/3/library/pathlib.html
- Process management: https://docs.python.org/3/library/subprocess.html
- Signal handling: https://docs.python.org/3/library/signal.html

Sample Input:
- Task list file with multiple task definitions
- Configuration parameters for execution

Expected Output:
- Parsed task files
- Execution results for each task
- State tracking information
"""

import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple, Union

from loguru import logger


class TaskState:
    """Task state enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskManager:
    """Core task management functionality with no UI dependencies"""
    
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
        
        # Process tracking
        self.active_processes: Dict[int, Set[int]] = {}  # Map of task PIDs to child process PIDs
        
        # Task state
        self.task_state: Dict[str, Dict[str, Any]] = self._load_state()
        
        # Current running task information
        self.current_task: Optional[str] = None
        self.current_task_start_time: Optional[float] = None
        
        # Find Claude executable
        self.claude_path = self._find_claude_executable()
    
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
    
    def _update_task_state(self, task_name: str, status: str, **kwargs) -> None:
        """
        Update state for a task
        
        Args:
            task_name: Name of the task
            status: Status to set
            **kwargs: Additional task state properties
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
    
    def _find_claude_executable(self) -> Path:
        """
        Find the Claude executable in the system PATH or common locations
        
        Returns:
            Path to the Claude executable

        Raises:
            SystemExit: If Claude executable is not found
        """
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
                    logger.info(f"Found Claude at: {claude_path}")
                    return Path(claude_path)
        except Exception as e:
            logger.warning(f"Error finding Claude with 'which': {e}")
        
        # If 'which' failed, check common locations
        logger.info("Checking common installation locations...")
        possible_paths = [
            Path.home() / ".npm-global" / "bin" / "claude",
            Path.home() / "node_modules" / ".bin" / "claude",
            Path("/usr/local/bin/claude"),
            Path("/opt/homebrew/bin/claude"),
            Path(os.environ.get("CLAUDE_PATH", ""))
        ]
        
        for path in possible_paths:
            if path.exists() and os.access(path, os.X_OK):
                logger.info(f"Found Claude at: {path}")
                return path
        
        # If we get here, we couldn't find Claude
        logger.error("Claude executable not found")
        logger.error("Please install Claude or specify the path using --claude-path")
        logger.error("You can install Claude Code with: npm install -g @anthropic/claude-code")
        sys.exit(1)
    
    def get_child_processes(self, parent_pid: int) -> Set[int]:
        """
        Get all child process IDs for a given parent process ID
        
        Args:
            parent_pid: Parent process ID
            
        Returns:
            Set of child process IDs
        """
        child_pids = set()
        
        try:
            # Get all processes and their parent PIDs
            ps_output = subprocess.check_output(
                ["ps", "-eo", "pid,ppid"], text=True
            )
            
            # Parse the output
            for line in ps_output.strip().split('\n')[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 2:
                    pid, ppid = int(parts[0]), int(parts[1])
                    if ppid == parent_pid:
                        child_pids.add(pid)
                        # Recursively get children of this child
                        child_pids.update(self.get_child_processes(pid))
        except Exception as e:
            logger.warning(f"Error getting child processes: {e}")
        
        return child_pids
    
    def kill_process_tree(self, parent_pid: int) -> bool:
        """
        Kill a process and all its children
        
        Args:
            parent_pid: Parent process ID
            
        Returns:
            True if all processes were successfully killed
        """
        success = True
        
        # Get all children first (before we kill the parent)
        children = self.get_child_processes(parent_pid)
        
        # Kill parent
        try:
            os.kill(parent_pid, signal.SIGKILL)
            logger.info(f"Killed parent process: {parent_pid}")
        except ProcessLookupError:
            # Process already gone
            pass
        except Exception as e:
            logger.warning(f"Error killing process {parent_pid}: {e}")
            success = False
        
        # Kill children
        for pid in children:
            try:
                os.kill(pid, signal.SIGKILL)
                logger.debug(f"Killed child process: {pid}")
            except ProcessLookupError:
                # Process already gone
                pass
            except Exception as e:
                logger.warning(f"Error killing process {pid}: {e}")
                success = False
        
        return success
    
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
    
    def run_task(self, task_file: Path, timeout_seconds: int = 300) -> Tuple[bool, Dict[str, Any]]:
        """
        Run a single task with Claude
        
        Args:
            task_file: Path to the task file
            timeout_seconds: Maximum execution time in seconds
            
        Returns:
            Tuple of (success, task_state)
        """
        task_name = task_file.stem
        result_file = self.results_dir / f"{task_name}.result"
        error_file = self.results_dir / f"{task_name}.error"
        
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
            # Launch Claude process
            with open(task_file, 'r') as task_input:
                with open(result_file, 'w') as result_output:
                    with open(error_file, 'w') as error_output:
                        process = subprocess.Popen(
                            [str(self.claude_path), "--print"],
                            stdin=task_input,
                            stdout=result_output,
                            stderr=error_output,
                            text=True
                        )
                        
                        # Record process ID
                        process_id = process.pid
                        logger.info(f"Claude process started with PID: {process_id}")
                        
                        # Update state with process info
                        self._update_task_state(
                            task_name,
                            TaskState.RUNNING,
                            process_id=process_id
                        )
                        
                        # Wait a moment for child processes to start
                        time.sleep(2)
                        
                        # Get all child processes
                        child_pids = self.get_child_processes(process_id)
                        self.active_processes[process_id] = child_pids
                        logger.info(f"Monitoring {len(child_pids)} child processes")
                        
                        # Update state with child processes
                        self._update_task_state(
                            task_name,
                            TaskState.RUNNING,
                            child_processes=list(child_pids)  # Convert set to list for JSON
                        )
                        
                        # Wait for completion with timeout
                        start_time = time.time()
                        
                        while process.poll() is None:
                            if time.time() - start_time > timeout_seconds:
                                logger.warning(f"Task {task_name} timed out after {timeout_seconds} seconds")
                                
                                # Kill the process tree
                                termination_success = self.kill_process_tree(process_id)
                                
                                # Clean up
                                if process_id in self.active_processes:
                                    del self.active_processes[process_id]
                                
                                with open(result_file, 'a') as f:
                                    f.write(f"\n\nTASK TIMED OUT AFTER {timeout_seconds} SECONDS")
                                
                                # Update state
                                self._update_task_state(
                                    task_name,
                                    TaskState.TIMEOUT,
                                    completed_at=datetime.now().isoformat(),
                                    execution_time=int(time.time() - start_time),
                                    clean_termination=termination_success
                                )
                                
                                # Clear current task
                                self.current_task = None
                                self.current_task_start_time = None
                                
                                return False, self.task_state[task_name]
                            
                            time.sleep(1)
                        
                        exit_code = process.returncode
                        execution_time = time.time() - start_time
                        
                        # Clean up process tracking
                        if process_id in self.active_processes:
                            del self.active_processes[process_id]
                        
                        # Kill any remaining child processes (helper processes, etc.)
                        termination_success = True
                        for pid in child_pids:
                            try:
                                os.kill(pid, signal.SIGKILL)
                            except ProcessLookupError:
                                # Process already gone
                                pass
                            except Exception:
                                termination_success = False
            
            if exit_code == 0:
                logger.info(f"Task {task_name} completed successfully")
                
                # Update state
                result_size = result_file.stat().st_size if result_file.exists() else 0
                self._update_task_state(
                    task_name,
                    TaskState.COMPLETED,
                    completed_at=datetime.now().isoformat(),
                    exit_code=exit_code,
                    execution_time=execution_time,
                    result_size=result_size,
                    clean_termination=termination_success
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
                    error=error_content[:500],  # Store first 500 chars of error
                    clean_termination=termination_success
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
    
    def run_all_tasks(self) -> Dict[str, Any]:
        """
        Run all tasks in the tasks directory
        
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
        
        for task_file in task_files:
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
            success, task_result = self.run_task(task_file)
            results["task_results"][task_name] = task_result
            
            if success:
                results["success"] += 1
            elif task_result.get("status") == TaskState.TIMEOUT:
                results["timeout"] += 1
            else:
                results["failed"] += 1
            
            # Wait between tasks
            time.sleep(5)
        
        return results
    
    def cleanup(self) -> None:
        """Clean up any remaining processes"""
        for parent_pid, child_pids in self.active_processes.items():
            self.kill_process_tree(parent_pid)
        
        self.active_processes.clear()


if __name__ == "__main__":
    """Validate task manager functionality"""
    import sys
    
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level="INFO")
    logger.add("task_manager.log", rotation="10 MB")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Task manager initialization
    total_tests += 1
    try:
        test_dir = Path("./test_task_manager")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
            
        manager = TaskManager(test_dir)
        
        # Check directories were created
        if not test_dir.exists() or not (test_dir / "tasks").exists() or not (test_dir / "results").exists():
            all_validation_failures.append("Task manager did not create expected directories")
    except Exception as e:
        all_validation_failures.append(f"Task manager initialization failed: {e}")
    
    # Test 2: Parse task list
    total_tests += 1
    try:
        # Create a test task list file
        test_task_list = test_dir / "test_tasks.md"
        with open(test_task_list, "w") as f:
            f.write("""# Test Tasks

## Task 1: First Task
This is the first task.

## Task 2: Second Task
This is the second task.
""")
        
        # Parse the task list
        task_files = manager.parse_task_list(test_task_list)
        
        # Check that task files were created
        if len(task_files) != 2:
            all_validation_failures.append(f"Expected 2 task files, got {len(task_files)}")
        
        # Check that task state was updated
        task_names = [path.stem for path in task_files]
        for name in task_names:
            if name not in manager.task_state:
                all_validation_failures.append(f"Task state not found for {name}")
    except Exception as e:
        all_validation_failures.append(f"Task list parsing failed: {e}")
    
    # Test 3: Get task summary
    total_tests += 1
    try:
        summary = manager.get_task_summary()
        expected_keys = ["total", "completed", "failed", "timeout", "pending", "running", "completion_pct"]
        
        for key in expected_keys:
            if key not in summary:
                all_validation_failures.append(f"Summary missing key: {key}")
        
        if summary["total"] != 2:
            all_validation_failures.append(f"Expected 2 total tasks, got {summary['total']}")
        
        if summary["pending"] != 2:
            all_validation_failures.append(f"Expected 2 pending tasks, got {summary['pending']}")
    except Exception as e:
        all_validation_failures.append(f"Get task summary failed: {e}")
    
    # Clean up test directory
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)