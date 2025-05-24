#!/usr/bin/env python3
"""
Tests for CLI Validators Module

This module tests the validation functions used in the CLI.

Test Coverage Target: 100%
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from task_runner.cli.validators import (
    validate_base_dir,
    validate_json_output,
    validate_pool_size,
    validate_task_list_file,
    validate_timeout,
)


class TestValidators:
    """Tests for validator functions."""

    def test_validate_pool_size_valid(self):
        """Test pool size validation with valid values."""
        assert validate_pool_size(1) == 1
        assert validate_pool_size(5) == 5
        assert validate_pool_size(10) == 10
        assert validate_pool_size(0) == 0  # 0 is actually valid

    def test_validate_pool_size_invalid(self):
        """Test pool size validation with invalid values."""
        import typer
        with pytest.raises(typer.BadParameter):
            validate_pool_size(-1)
        
        with pytest.raises(typer.BadParameter):
            validate_pool_size(-10)

    def test_validate_timeout_valid(self):
        """Test timeout validation with valid values."""
        assert validate_timeout(1) == 1
        assert validate_timeout(300) == 300
        assert validate_timeout(3600) == 3600
        assert validate_timeout(0) == 0  # 0 is actually valid

    def test_validate_timeout_invalid(self):
        """Test timeout validation with invalid values."""
        import typer
        with pytest.raises(typer.BadParameter):
            validate_timeout(-1)
        
        with pytest.raises(typer.BadParameter):
            validate_timeout(-100)

    def test_validate_base_dir_valid(self, tmp_path):
        """Test base directory validation with valid path."""
        # Existing directory should be valid
        result = validate_base_dir(tmp_path)
        assert result == tmp_path

    def test_validate_base_dir_home_expansion(self):
        """Test base directory validation with home directory."""
        # Test tilde expansion
        home_path = Path("~/test_dir")
        result = validate_base_dir(home_path)
        assert result == Path.home() / "test_dir"
        
    def test_validate_base_dir_regular_path(self):
        """Test base directory validation with regular path."""
        # Regular path should pass through unchanged
        test_path = tempfile.NamedTemporaryFile(delete=False).name
        result = validate_base_dir(test_path)
        assert result == test_path

    def test_validate_task_list_file_valid(self, tmp_path):
        """Test task list file validation with valid file."""
        # Create a test file
        test_file = tmp_path / "tasks.md"
        test_file.write_text("# Tasks")
        
        result = validate_task_list_file(test_file)
        assert result == test_file

    def test_validate_task_list_file_none(self):
        """Test task list file validation with None."""
        # None should be acceptable (optional parameter)
        result = validate_task_list_file(None)
        assert result is None

    def test_validate_task_list_file_invalid(self):
        """Test task list file validation with non-existent file."""
        import typer
        with pytest.raises(typer.BadParameter):
            validate_task_list_file(Path("/non/existent/file.md"))

    def test_validate_json_output_valid(self):
        """Test JSON output validation."""
        # Any boolean value should be valid
        assert validate_json_output(True) is True
        assert validate_json_output(False) is False


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])