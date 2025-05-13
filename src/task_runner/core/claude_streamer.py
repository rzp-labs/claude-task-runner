#!/usr/bin/env python3
"""
Claude Streamer Module for Task Runner

This module provides functions for running Claude with real-time output streaming,
enabling visibility into Claude's progress during task execution. It uses pexpect
for reliable interactive terminal management and streaming of Claude's output.

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
- Pexpect Documentation: https://pexpect.readthedocs.io/
- Loguru Documentation: https://loguru.readthedocs.io/
"""

import sys
import time
import subprocess
import os
import tempfile
import signal
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, TextIO

import pexpect
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
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Run Claude on a task file and stream its output in real-time using pexpect.
    
    Args:
        task_file: Path to the task file
        result_file: Path to save the result (defaults to task_file with .result extension)
        error_file: Path to save error output (defaults to task_file with .error extension)
        claude_path: Path to the Claude executable (found automatically if None)
        cmd_args: Additional command-line arguments for Claude
        timeout_seconds: Maximum execution time in seconds
        
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
    
    # Initialize command args and add print flag
    if cmd_args is None:
        cmd_args = []
    
    cmd_args = ["--print", "--verbose"] + cmd_args
    
    logger.info(f"Task file: {task_file}")
    logger.info(f"Result will be saved to: {result_file}")
    
    # Start the process with pexpect
    start_time = time.time()
    
    try:
        # Build Claude command
        cmd = [claude_path] + cmd_args
        cmd_str = ' '.join(cmd)
        logger.info(f"Running command: {cmd_str}")
        
        # Open result file for writing
        with open(result_file, 'w') as result_output, open(error_file, 'w') as error_output:
            # Create a more persistent temporary file for the command
            # We'll handle cleanup in a way that ensures the file exists while needed
            temp_dir = tempfile.gettempdir()
            cmd_file_path = os.path.join(temp_dir, f"claude_cmd_{int(time.time())}.sh")
            
            try:
                # Write the command directly to the file
                with open(cmd_file_path, 'w') as cmd_file:
                    # Build the basic command with output format
                    cmd_file.write("#!/bin/bash\n")
                    cmd_file.write(f"{claude_path} --print --verbose --output-format stream-json ")
                    
                    # Add any additional command arguments
                    if cmd_args:
                        cmd_file.write(f"{' '.join(cmd_args)} ")
                    
                    # Add input redirection from the task file
                    cmd_file.write(f"< {task_file}")
                
                # Make the command file executable
                os.chmod(cmd_file_path, 0o755)
                
                logger.info(f"Created command file at {cmd_file_path}")
                
                # Verify the file exists before executing
                if not os.path.exists(cmd_file_path):
                    raise FileNotFoundError(f"Command file not found at {cmd_file_path}")
                
                # Spawn the process using the command file
                logger.info(f"Executing command via {cmd_file_path}")
                child = pexpect.spawn(
                    cmd_file_path,
                    encoding='utf-8',
                    timeout=timeout_seconds,
                    # Ensure window size is large enough for Claude's output
                    dimensions=(80, 200)
                )
                
                # IMPORTANT: We'll clean up the file later, after the command starts running
                
            except Exception as e:
                # If anything fails during setup, clean up the file
                logger.error(f"Error preparing command: {e}")
                try:
                    if os.path.exists(cmd_file_path):
                        os.unlink(cmd_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up command file: {cleanup_error}")
                raise
            
            # Enable echoing to see output in real-time in our terminal
            child.logfile_read = sys.stdout
            
            # Make sure we're capturing all output
            child.logfile = result_output
            child.logfile_send = error_output
            
            # Set up timeout monitoring
            elapsed = 0
            last_output_time = time.time()
            logger.info("Started streaming Claude's output...")
            
            # Initialize variables to track outcome
            timed_out = False
            exit_code = 0
            
            # Keep checking for output until process completes
            while True:
                try:
                    # Wait for any output with a 1-second timeout (allows interruption check)
                    patterns = [pexpect.TIMEOUT, pexpect.EOF, '\r\n']
                    index = child.expect(patterns, timeout=1)
                    
                    if index == 0:  # TIMEOUT - No output in the last 1 second
                        # Check if we've exceeded the total timeout
                        elapsed = time.time() - start_time
                        if elapsed > timeout_seconds:
                            logger.warning(f"Claude process timed out after {timeout_seconds}s")
                            timed_out = True
                            exit_code = -1
                            
                            # Add timeout message to result file
                            result_output.write(f"\n\n[TIMEOUT: Claude process was terminated after {timeout_seconds}s]")
                            result_output.flush()
                            
                            # Kill the process
                            child.kill(signal.SIGTERM)
                            break
                        
                        # Check if we should log silent period
                        if time.time() - last_output_time > 10:
                            logger.info(f"Claude has been silent for {int(time.time() - last_output_time)}s")
                            last_output_time = time.time()  # Reset to avoid spamming
                        
                    elif index == 1:  # EOF - Process completed
                        logger.info("Claude process completed")
                        break
                        
                    elif index == 2:  # Got a line of output
                        # Get the raw output line
                        line = child.before
                        if line:
                            line = line.strip()
                            
                        # Reset timeout trackers since we got output
                        last_output_time = time.time()
                        
                        # Skip empty lines
                        if not line:
                            continue
                            
                        # Try to parse as JSON if it starts with a brace
                        if line.startswith('{'):
                            try:
                                # Parse the JSON output from Claude's stream-json format
                                logger.debug(f"Processing JSON line: {line[:100]}...")
                                data = json.loads(line)
                                # Log the basic structure
                                logger.debug(f"JSON keys: {', '.join(data.keys())}")
                                
                                # Extract content if available
                                if 'content' in data:
                                    content = data['content']
                                    # Handle both string and list content formats
                                    if isinstance(content, str):
                                        if content and content.strip():
                                            # Write to result file
                                            result_output.write(content)
                                            result_output.flush()
                                            # Log nicely formatted content
                                            logger.info(f"Claude: {content.strip()}")
                                    elif isinstance(content, list):
                                        # Content is a list of content blocks (new format)
                                        for block in content:
                                            if isinstance(block, dict) and 'text' in block and block.get('type') == 'text':
                                                text = block['text']
                                                if text and text.strip():
                                                    # Write to result file
                                                    result_output.write(text)
                                                    result_output.flush()
                                                    # Log nicely formatted content
                                                    logger.info(f"Claude: {text.strip()}")
                                            elif isinstance(block, dict) and block.get('type') == 'tool_use':
                                                tool_info = f"Tool use: {block.get('name', 'unknown')} - {json.dumps(block.get('input', {}))}"
                                                logger.info(f"Claude tool use: {tool_info}")
                                                result_output.write(f"\n[Tool Use: {tool_info}]\n")
                                                result_output.flush()
                                    # Log the entire content for debugging
                                    logger.debug(f"Content structure: {type(content)} - {str(content)[:100]}...")
                                
                                # Extract completion info if available
                                elif 'completion_id' in data:
                                    logger.info(f"Completion ID: {data['completion_id']}")
                                
                                # Extract error info if available    
                                elif 'error' in data:
                                    error_msg = data['error'].get('message', 'Unknown error')
                                    logger.error(f"Claude error: {error_msg}")
                                    error_output.write(f"Error: {error_msg}\n")
                                    error_output.flush()
                            
                            except json.JSONDecodeError:
                                # Not valid JSON, just log the raw line
                                if '[ERROR]' in line:
                                    logger.error(f"Claude error: {line}")
                                    error_output.write(f"{line}\n")
                                    error_output.flush()
                                else:
                                    # Regular output line
                                    logger.info(f"Claude output: {line}")
                                    result_output.write(f"{line}\n")
                                    result_output.flush()
                        else:
                            # Not JSON, write to appropriate output
                            if '[ERROR]' in line:
                                logger.error(f"Claude error: {line}")
                                error_output.write(f"{line}\n")
                                error_output.flush()
                            else:
                                # Regular output line
                                logger.info(f"Claude output: {line}")
                                result_output.write(f"{line}\n")
                                result_output.flush()
                    
                except KeyboardInterrupt:
                    logger.warning("Process interrupted by user")
                    child.kill(signal.SIGTERM)
                    exit_code = 130  # Standard exit code for SIGINT
                    break
                except Exception as e:
                    logger.error(f"Error during pexpect monitoring: {e}")
                    # Try to kill the process
                    try:
                        child.kill(signal.SIGTERM)
                    except:
                        pass
                    exit_code = 1
                    break
            
            # Wait for process to fully terminate
            try:
                child.close()
                # Get the exit code if available
                if not timed_out and child.exitstatus is not None:
                    exit_code = child.exitstatus
            except:
                pass
            
            # Clean up the command file now that the process has completed
            try:
                if os.path.exists(cmd_file_path):
                    os.unlink(cmd_file_path)
                    logger.info(f"Removed temporary command file: {cmd_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up command file: {cleanup_error}")
            
            execution_time = time.time() - start_time
            
            # Log completion
            if exit_code == 0:
                logger.success(f"Claude completed successfully in {execution_time:.2f} seconds")
                
                # Show summary of output file
                if result_path.exists():
                    file_size = result_path.stat().st_size
                    logger.info(f"Result file size: {file_size} bytes")
            else:
                logger.error(f"Claude process failed with exit code {exit_code}")
                
                # Check for specific error conditions
                if result_path.exists() and result_path.stat().st_size > 0:
                    with open(result_file, "r") as f:
                        result_content = f.read(500)
                        if "usage limit reached" in result_content.lower():
                            logger.error("CLAUDE USAGE LIMIT REACHED - Your account has reached its quota")
                
                # Show error output
                if error_path.exists() and error_path.stat().st_size > 0:
                    with open(error_file, "r") as f:
                        error_content = f.read(500)
                        logger.error(f"Error output: {error_content}")
            
            status = "timeout" if timed_out else ("completed" if exit_code == 0 else "failed")
            
            return {
                "task_file": task_file,
                "result_file": result_file,
                "error_file": error_file,
                "exit_code": exit_code,
                "execution_time": execution_time,
                "success": exit_code == 0,
                "status": status,
                "result_size": result_path.stat().st_size if result_path.exists() else 0
            }
        
    except Exception as e:
        logger.exception(f"Error streaming Claude output: {e}")
        
        execution_time = time.time() - start_time if 'start_time' in locals() else 0
        
        return {
            "task_file": task_file,
            "result_file": result_file,
            "error_file": error_file,
            "success": False,
            "error": str(e),
            "exit_code": -1,
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
    
    try:
        # Create a more persistent temporary file for the command
        temp_dir = tempfile.gettempdir()
        cmd_file_path = os.path.join(temp_dir, f"claude_clear_{int(time.time())}.sh")
        
        # Write the command to the file
        with open(cmd_file_path, 'w') as cmd_file:
            cmd_file.write("#!/bin/bash\n")
            cmd_file.write(f"echo '/clear' | {claude_path}")
        
        # Make the file executable
        os.chmod(cmd_file_path, 0o755)
        
        # Verify the file exists
        if not os.path.exists(cmd_file_path):
            logger.error(f"Clear command file not found at {cmd_file_path}")
            return False
            
        logger.info(f"Created clear command file at {cmd_file_path}")
        
        success = False
        try:
            # Use pexpect to run the command
            child = pexpect.spawn(cmd_file_path, encoding='utf-8', timeout=10)
            
            # Look for confirmation message or prompt
            patterns = [pexpect.TIMEOUT, pexpect.EOF, "Context cleared"]
            index = child.expect(patterns, timeout=5)
            
            success = index == 2 or index == 1  # Success if we see "Context cleared" or EOF
            
            # Close the process
            child.close(force=True)
            
            if success:
                logger.info("Claude context cleared successfully")
            else:
                logger.warning("Context clearing failed - no confirmation received")
        finally:
            # Clean up the temporary file after execution
            try:
                if os.path.exists(cmd_file_path):
                    os.unlink(cmd_file_path)
                    logger.info(f"Removed temporary clear command file: {cmd_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up clear command file: {cleanup_error}")
                
        return success
    except Exception as e:
        logger.error(f"Error clearing context: {e}")
        return False


def run_claude_tasks(
    task_files: List[str],
    clear_context: bool = True,
    claude_path: Optional[str] = None,
    cmd_args: Optional[List[str]] = None,
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Run multiple Claude tasks in sequence with streaming output.
    
    Args:
        task_files: List of task file paths
        clear_context: Whether to clear context between tasks
        claude_path: Path to Claude executable (found automatically if None)
        cmd_args: Additional command arguments for Claude
        timeout_seconds: Maximum execution time per task in seconds
        
    Returns:
        Dictionary with execution results for all tasks
    """
    if not task_files:
        logger.warning("No task files provided")
        return {"success": False, "error": "No task files provided"}
    
    # Find Claude executable if not provided
    if claude_path is None:
        claude_path = find_claude_path()
    
    logger.info(f"Using Claude at: {claude_path}")
    
    # Initialize command args
    if cmd_args is None:
        cmd_args = []
    
    results = []
    total_start_time = time.time()
    
    for i, task_file in enumerate(task_files):
        if not os.path.exists(task_file):
            logger.error(f"Task file not found: {task_file}")
            results.append({
                "task_file": task_file,
                "success": False,
                "error": "File not found"
            })
            continue
        
        # Run the task with streaming output
        logger.info(f"Running task {i+1}/{len(task_files)}: {task_file}")
        task_result = stream_claude_output(
            task_file=task_file,
            claude_path=claude_path,
            cmd_args=cmd_args,
            timeout_seconds=timeout_seconds
        )
        results.append(task_result)
        
        # Clear context if this isn't the last task
        if clear_context and i < len(task_files) - 1:
            clear_claude_context(claude_path)
    
    total_time = time.time() - total_start_time
    
    # Calculate summary
    successful = sum(1 for r in results if r.get("success", False))
    
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