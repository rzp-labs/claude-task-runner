#!/usr/bin/env python3
"""
Validators for Task Runner CLI

This module provides validation functions for CLI inputs,
ensuring parameters are validated before being passed to core functions.

This module is part of the CLI Layer and should only depend on
Core Layer components, not on Integration Layer.

Sample input:
- CLI parameter values

Expected output:
- Validated parameters or error messages
"""

from pathlib import Path
from typing import Optional, Any

import typer
from rich.console import Console

console = Console()

def validate_task_list_file(value: Optional[Path]) -> Optional[Path]:
    """
    Validate that a task list file exists
    
    Args:
        value: Path to the task list file
        
    Returns:
        Validated path or None
        
    Raises:
        typer.BadParameter: If the file does not exist
    """
    if value and not value.exists():
        raise typer.BadParameter(f"Task list file not found: {value}")
    return value

def validate_base_dir(value: Path) -> Path:
    """
    Validate base directory
    
    Args:
        value: Base directory path
        
    Returns:
        Validated path
    """
    # Expand user directory
    if str(value).startswith("~"):
        value = Path(str(value).replace("~", str(Path.home())))
    return value

def validate_timeout(value: int) -> int:
    """
    Validate timeout value
    
    Args:
        value: Timeout in seconds
        
    Returns:
        Validated timeout
        
    Raises:
        typer.BadParameter: If timeout is negative
    """
    if value < 0:
        raise typer.BadParameter("Timeout cannot be negative")
    return value

def validate_pool_size(value: int) -> int:
    """
    Validate pool size
    
    Args:
        value: Pool size
        
    Returns:
        Validated pool size
        
    Raises:
        typer.BadParameter: If pool size is negative
    """
    if value < 0:
        raise typer.BadParameter("Pool size cannot be negative")
    return value

def validate_json_output(value: bool) -> bool:
    """
    Validate json output option
    
    Args:
        value: JSON output flag
        
    Returns:
        Validated JSON output flag
    """
    return value


if __name__ == "__main__":
    """Validate validators"""
    import sys
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Validate task list file
    total_tests += 1
    try:
        # Existing file
        test_file = Path(__file__)
        result = validate_task_list_file(test_file)
        if result != test_file:
            all_validation_failures.append("Failed to validate existing file")
        
        # Non-existent file - should raise exception
        try:
            validate_task_list_file(Path("non_existent_file.md"))
            all_validation_failures.append("Failed to reject non-existent file")
        except typer.BadParameter:
            pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Validate task list file test failed: {e}")
    
    # Test 2: Validate base directory
    total_tests += 1
    try:
        # Regular path
        test_dir = Path("/tmp")
        result = validate_base_dir(test_dir)
        if result != test_dir:
            all_validation_failures.append("Failed to validate regular directory")
        
        # User home directory
        home_dir = Path("~/test")
        result = validate_base_dir(home_dir)
        if result != Path.home() / "test":
            all_validation_failures.append("Failed to expand user directory")
    except Exception as e:
        all_validation_failures.append(f"Validate base directory test failed: {e}")
    
    # Test 3: Validate timeout
    total_tests += 1
    try:
        # Valid timeout
        result = validate_timeout(300)
        if result != 300:
            all_validation_failures.append("Failed to validate valid timeout")
        
        # Negative timeout - should raise exception
        try:
            validate_timeout(-1)
            all_validation_failures.append("Failed to reject negative timeout")
        except typer.BadParameter:
            pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Validate timeout test failed: {e}")
    
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
