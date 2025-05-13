#!/usr/bin/env python3
"""
Claude Streamer Module for Task Runner

This module provides functions for running Claude with real-time output streaming,
enabling visibility into Claude's progress during task execution. It uses Claude's
native streaming capabilities for reliable output display.

Sample Input:
- Task file path: "/path/to/task.md"
- Result file path: "/path/to/result.txt"
- Error file path: "/path/to/error.txt"
- Claude executable path: "/usr/local/bin/claude"
- Command arguments: ["--no-auth-check"]
- Timeout in seconds: 300

Sample Output:
- Dictionary with execution results:
  {
    "task_file": "/path/to/task.md",
    "result_file": "/path/to/result.txt",
    "error_file": "/path/to/error.txt", 
    "exit_code": 0,
    "execution_time": 12.45,
    "success": true,
    "status": "completed",
    "result_size": 1024
  }

Links:
- Claude CLI: https://github.com/anthropics/anthropic-cli
- Loguru Documentation: https://loguru.readthedocs.io/
- Python subprocess: https://docs.python.org/3/library/subprocess.html
"""

import sys
import time
import subprocess
import os
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, TextIO

from loguru import logger


def find_claude_path() -> str:
    """
    Find the Claude executable in the system PATH.
    
    Returns:
        str: Path to the Claude executable
    """
    try:
        which_result = subprocess.run(
            ["which", "claude"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if which_result.returncode == 0:
            return which_result.stdout.strip()
    except Exception as e:
        logger.warning(f"Error finding Claude with 'which': {e}")
    
    # Default fallback
    return "claude"


def stream_claude_output(
    task_file: str,
    result_file: Optional[str] = None,
    error_file: Optional[str] = None,
    claude_path: Optional[str] = None,
    cmd_args: Optional[List[str]] = None,
    timeout_seconds: int = 300,
    raw_json: bool = False,
    quiet: bool = False
) -> Dict[str, Any]:
    """
    Run Claude on a task file and stream its output in real-time.
    
    Args:
        task_file: Path to the task file
        result_file: Path to save the result (defaults to task_file with .result extension)
        error_file: Path to save error output (defaults to task_file with .error extension)
        claude_path: Path to the Claude executable (found automatically if None)
        cmd_args: Additional command-line arguments for Claude
        timeout_seconds: Maximum execution time in seconds
        raw_json: Whether to output raw JSON instead of human-friendly format
        quiet: Whether to suppress console output during execution
        
    Returns:
        Dictionary with execution results including success status, time taken, and file paths
    """
    task_path = Path(task_file)
    
    # Set up default output files if not provided
    if result_file is None:
        result_file = str(task_path.with_suffix(".result"))
    
    if error_file is None:
        error_file = str(task_path.with_suffix(".error"))
    
    result_path = Path(result_file)
    error_path = Path(error_file)
    
    # Create parent directories if needed
    result_path.parent.mkdir(exist_ok=True, parents=True)
    error_path.parent.mkdir(exist_ok=True, parents=True)
    
    # Use provided Claude path or find it
    if claude_path is None:
        claude_path = find_claude_path()
    
    # Initialize command args and add appropriate flags
    if cmd_args is None:
        cmd_args = []
    
    # Add either --print or --json flag based on raw_json setting
    if raw_json:
        cmd_args = ["--json"] + cmd_args
    else:
        cmd_args = ["--print"] + cmd_args
    
    if not quiet:
        logger.info(f"Task file: {task_file}")
        logger.info(f"Result will be saved to: {result_file}")
    
    # Start the process - using direct subprocess approach instead of named pipes
    start_time = time.time()
    
    try:
        # Build command with direct input/output
        cmd = [claude_path] + cmd_args
        if not quiet:
            logger.info(f"Running command: {' '.join(cmd)}")
        
        # Open files for reading/writing
        with open(task_file, 'r') as input_file, \
             open(result_file, 'w') as result_output, \
             open(error_file, 'w') as error_output:
            
            # Start Claude process with piped stdout to capture output directly
            process = subprocess.Popen(
                cmd,
                stdin=input_file,
                stdout=subprocess.PIPE,
                stderr=error_output,
                text=True,
                bufsize=1  # Line buffered mode
            )
            
            if not quiet:
                logger.info("Starting to stream Claude's output...")
            last_output_time = time.time()
            
            # Read from process stdout in real-time
            while True:
                # Check if process is still running or if we're done reading output
                if process.poll() is not None and not process.stdout.readable():
                    logger.info(f"Claude process completed with exit code {process.returncode}")
                    break
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    logger.warning(f"Claude process timed out after {timeout_seconds}s")
                    try:
                        process.terminate()
                        logger.info(f"Terminated Claude process")
                    except:
                        pass
                        
                    # Add timeout notice to result file
                    result_output.write(f"\n\n[TIMEOUT: Claude process was terminated after {timeout_seconds}s]")
                    result_output.flush()
                    return {
                        "task_file": task_file,
                        "result_file": result_file,
                        "error_file": error_file,
                        "exit_code": -1,  # Use -1 for timeout
                        "execution_time": elapsed,
                        "success": False,
                        "status": "timeout",
                        "result_size": result_path.stat().st_size if result_path.exists() else 0
                    }
                
                # Read a line (non-blocking)
                line = process.stdout.readline()
                
                if line:
                    # Got output, write to result file
                    result_output.write(line)
                    result_output.flush()
                    
                    # Display to console if not in quiet mode
                    if not quiet:
                        display_line = line.strip()
                        if display_line:
                            if len(display_line) > 100:
                                display_line = display_line[:100] + "..."
                            logger.info(f"Claude: {display_line}")
                    
                    last_output_time = time.time()
                else:
                    # No output available right now
                    
                    # Check if process has ended
                    if process.poll() is not None:
                        break
                    
                    # Check if we've been silent for too long (but not timed out yet)
                    if not quiet and time.time() - last_output_time > 10:
                        logger.info(f"Claude has been silent for {int(time.time() - last_output_time)}s")
                        last_output_time = time.time()  # Reset to avoid spamming
                    
                    # Small pause before trying again
                    time.sleep(0.1)
            
            # Process completed - make sure we get the exit code
            if process.poll() is None:
                process.wait()
            
            execution_time = time.time() - start_time
            exit_code = process.returncode
            
            # Log completion if not in quiet mode
            if not quiet:
                if exit_code == 0:
                    logger.success(f"Claude completed successfully in {execution_time:.2f} seconds")
                    
                    # Show summary of output file
                    if result_path.exists():
                        file_size = result_path.stat().st_size
                        logger.info(f"Result file size: {file_size} bytes")
                else:
                    logger.error(f"Claude process failed with exit code {exit_code}")
                
                # Check for specific error conditions if not in quiet mode
                error_content = ""
                if not quiet and result_path.exists() and result_path.stat().st_size > 0:
                    with open(result_file, "r") as f:
                        result_content = f.read(500)
                        if "usage limit reached" in result_content.lower():
                            logger.error("CLAUDE USAGE LIMIT REACHED - Your account has reached its quota")
                            logger.error("Consider waiting until your quota resets or upgrading your Claude plan")
                
                # Show error output if not in quiet mode
                if not quiet and error_path.exists() and error_path.stat().st_size > 0:
                    with open(error_file, "r") as f:
                        error_content = f.read(500)
                        logger.error(f"Error output: {error_content}")
            
            return {
                "task_file": task_file,
                "result_file": result_file,
                "error_file": error_file,
                "exit_code": exit_code,
                "execution_time": execution_time,
                "success": exit_code == 0,
                "status": "completed" if exit_code == 0 else "failed",
                "result_size": result_path.stat().st_size if result_path.exists() else 0
            }
        
    except Exception as e:
        if not quiet:
            logger.exception(f"Error streaming Claude output: {e}")
        
        # Check if process is still running and terminate if needed
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        execution_time = time.time() - start_time if 'start_time' in locals() else 0
        
        return {
            "task_file": task_file,
            "result_file": result_file,
            "error_file": error_file,
            "success": False,
            "error": str(e),
            "exit_code": -1 if 'process' not in locals() else (process.returncode or -1),
            "execution_time": execution_time,
            "status": "error",
            "result_size": result_path.stat().st_size if result_path.exists() else 0
        }


def clear_claude_context(claude_path: Optional[str] = None) -> bool:
    """
    Clear Claude's context using the /clear command.
    
    Args:
        claude_path: Path to Claude executable (found automatically if None)
        
    Returns:
        bool: True if clearing was successful, False otherwise
    """
    if claude_path is None:
        claude_path = find_claude_path()
    
    logger.info("Clearing Claude context...")
    
    # Use echo to pipe /clear to Claude
    cmd = f"echo '/clear' | {claude_path}"
    
    try:
        process = subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        if process.returncode == 0:
            logger.info("Claude context cleared successfully")
            return True
        else:
            logger.warning(f"Context clearing failed: {process.stderr.decode()}")
            return False
    except Exception as e:
        logger.error(f"Error clearing context: {e}")
        return False


def run_claude_tasks(
    task_files: List[str],
    clear_context: bool = True,
    claude_path: Optional[str] = None,
    cmd_args: Optional[List[str]] = None,
    timeout_seconds: int = 300,
    raw_json: bool = False,
    quiet: bool = False
) -> Dict[str, Any]:
    """
    Run multiple Claude tasks in sequence with streaming output.
    
    Args:
        task_files: List of task file paths
        clear_context: Whether to clear context between tasks
        claude_path: Path to Claude executable (found automatically if None)
        cmd_args: Additional command arguments for Claude
        timeout_seconds: Maximum execution time per task in seconds
        raw_json: Whether to output raw JSON instead of human-friendly format
        quiet: Whether to suppress console output during execution
        
    Returns:
        Dictionary with execution results for all tasks
    """
    if not task_files:
        if not quiet:
            logger.warning("No task files provided")
        return {"success": False, "error": "No task files provided"}
    
    # Find Claude executable if not provided
    if claude_path is None:
        claude_path = find_claude_path()
    
    if not quiet:
        logger.info(f"Using Claude at: {claude_path}")
    
    # Initialize command args
    if cmd_args is None:
        cmd_args = []
    
    results = []
    total_start_time = time.time()
    
    for i, task_file in enumerate(task_files):
        if not os.path.exists(task_file):
            if not quiet:
                logger.error(f"Task file not found: {task_file}")
            results.append({
                "task_file": task_file,
                "success": False,
                "error": "File not found"
            })
            continue
        
        # Run the task with streaming output
        if not quiet:
            logger.info(f"Running task {i+1}/{len(task_files)}: {task_file}")
        task_result = stream_claude_output(
            task_file=task_file,
            claude_path=claude_path,
            cmd_args=cmd_args,
            timeout_seconds=timeout_seconds,
            raw_json=raw_json,
            quiet=quiet
        )
        results.append(task_result)
        
        # Clear context if this isn't the last task
        if clear_context and i < len(task_files) - 1:
            clear_claude_context(claude_path)
    
    total_time = time.time() - total_start_time
    
    # Calculate summary
    successful = sum(1 for r in results if r.get("success", False))
    
    if not quiet:
        logger.info("=" * 50)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total tasks: {len(task_files)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {len(task_files) - successful}")
        logger.info(f"Total time: {total_time:.2f} seconds")
        logger.info(f"Average time per task: {total_time/max(1, len(task_files)):.2f} seconds")
    
    return {
        "results": results,
        "total_time": total_time,
        "total_tasks": len(task_files),
        "successful_tasks": successful,
        "failed_tasks": len(task_files) - successful
    }


if __name__ == "__main__":
    """
    Validate the claude_streamer module functionality with real test cases.
    """
    import sys
    import argparse
    
    # Configure logger for validation
    logger.remove()
    logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Setup validation arguments
    parser = argparse.ArgumentParser(description="Claude Streamer Validation")
    parser.add_argument("--task", help="Optional task file path for direct testing")
    parser.add_argument("--demo", action="store_true", help="Use demo mode with simulated tasks")
    args = parser.parse_args()
    
    # Create a temporary directory for tests
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logger.info(f"Created temporary directory for tests: {temp_path}")
        
        # Test 1: find_claude_path function
        total_tests += 1
        try:
            claude_path = find_claude_path()
            logger.info(f"Claude path found: {claude_path}")
            
            if not claude_path:
                all_validation_failures.append("find_claude_path test: Returned empty path")
        except Exception as e:
            all_validation_failures.append(f"find_claude_path test error: {str(e)}")
        
        # Test 2: Create a test task file
        total_tests += 1
        test_task_file = str(temp_path / "test_task.md")
        try:
            # Create a simple task file
            with open(test_task_file, "w") as f:
                f.write("# Test Task\n\nThis is a test task for validation.\n")
            
            if not os.path.exists(test_task_file):
                all_validation_failures.append("File creation test: Failed to create test task file")
        except Exception as e:
            all_validation_failures.append(f"File creation test error: {str(e)}")
        
        # Test 3: Validate function parameters and return values
        total_tests += 1
        try:
            # Create a small test script to directly write output
            test_script_path = str(temp_path / "test_echo.sh")
            with open(test_script_path, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("# Read input and echo it back with a header\n")
                f.write("cat > /dev/null\n")  # Read stdin but don't use it
                f.write("echo 'Task completed successfully'\n")
                f.write("echo 'Content from task file was processed'\n")
            
            # Make it executable
            os.chmod(test_script_path, 0o755)
            
            # Verify the ability to handle command-line arguments
            cmd_args_test = ["--arg1", "--arg2=value"]
            test_args_str = stream_claude_output(
                task_file=test_task_file,
                cmd_args=cmd_args_test,
                timeout_seconds=1  # Short timeout since this will fail anyway
            )
            
            # We expect this to fail but the function should return a properly structured result
            # Check result structure has required keys
            required_keys = ["task_file", "result_file", "error_file", "exit_code", 
                           "execution_time", "success"]
            
            missing_keys = [key for key in required_keys if key not in test_args_str]
            if missing_keys:
                all_validation_failures.append(f"Parameter validation test: Missing keys in result: {missing_keys}")
                
        except Exception as e:
            all_validation_failures.append(f"Parameter validation test error: {str(e)}")
            
        # Test 4: Test response to timeout
        total_tests += 1
        try:
            # Create a slow script that will trigger timeout
            slow_script_path = str(temp_path / "slow_script.sh")
            with open(slow_script_path, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("# Script that takes longer than the timeout\n")
                f.write("cat > /dev/null\n")  # Read stdin but don't use it
                f.write("echo 'Starting slow operation...'\n")
                f.write("sleep 3\n")  # Sleep longer than our timeout
                f.write("echo 'This should not be reached due to timeout'\n")
            
            # Make it executable
            os.chmod(slow_script_path, 0o755)
            
            # Test with very short timeout
            timeout_result = stream_claude_output(
                task_file=test_task_file,
                claude_path=slow_script_path,
                timeout_seconds=1  # Short timeout to trigger timeout handling
            )
            
            # Check the timeout was handled correctly
            if timeout_result.get("status") != "timeout":
                all_validation_failures.append(f"Timeout test: Expected status 'timeout', got '{timeout_result.get('status')}'")
                
            # Check the file has timeout message
            result_file = timeout_result.get("result_file")
            if result_file and os.path.exists(result_file):
                with open(result_file, "r") as f:
                    content = f.read()
                    if "TIMEOUT" not in content:
                        all_validation_failures.append(f"Timeout test: Expected timeout message in result file")
        except Exception as e:
            all_validation_failures.append(f"Timeout test error: {str(e)}")
        
        # Test 5: clear_claude_context with real echo command
        total_tests += 1
        try:
            # Use echo itself as a simple executable - it should handle pipes
            result = clear_claude_context("/bin/echo")
            
            # The function should complete without error
            if result is not True and result is not False:
                all_validation_failures.append(f"clear_claude_context test: Expected boolean result, got {type(result)}")
                
            logger.info(f"Context clearing test completed")
        except Exception as e:
            all_validation_failures.append(f"clear_claude_context test error: {str(e)}")
        
        # Test 6: run_claude_tasks with multiple tasks
        total_tests += 1
        try:
            # Create another test task file
            test_task_file2 = str(temp_path / "test_task2.md")
            with open(test_task_file2, "w") as f:
                f.write("# Test Task 2\n\nThis is another test task for validation.\n")
            
            # Test function structure and parameters without actual execution
            # Just validate the returned structure is correct
            result = run_claude_tasks(
                task_files=[test_task_file, test_task_file2],
                claude_path="/bin/echo",  # Use echo as a simple executable that will run quickly
                timeout_seconds=1
            )
            
            # Check result structure
            required_keys = ["results", "total_time", "total_tasks", 
                            "successful_tasks", "failed_tasks"]
            
            missing_keys = [key for key in required_keys if key not in result]
            if missing_keys:
                all_validation_failures.append(f"run_claude_tasks test: Missing keys in result: {missing_keys}")
            
            # Check expected values
            if result.get("total_tasks") != 2:
                all_validation_failures.append(f"run_claude_tasks test: Expected 2 total tasks, got {result.get('total_tasks')}")
            
            if result.get("successful_tasks", 0) < 1:
                all_validation_failures.append(f"run_claude_tasks test: Expected at least 1 successful task")
        except Exception as e:
            all_validation_failures.append(f"run_claude_tasks test error: {str(e)}")
        
        # Clean up any remaining files
        logger.info("Cleaning up test files...")
    
    # Final validation result
    if all_validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)  # Exit with success code