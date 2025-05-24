#!/usr/bin/env python3
"""
Comprehensive Tests for MCP Server Module

This module provides additional test coverage for the server.py module,
specifically targeting areas with low coverage as identified in the
coverage report:
- Lines 27-48: Server initialization
- Lines 83-84: Error handling
- Lines 99->122, 102->122, 104->119, 119->122: Branch conditions
- Line 125: Conditional or error handling
- Line 136->128: Branch condition

This test file focuses on server initialization and startup, exception 
handling in various code paths, and conditional branches in function execution.
"""

import json
import os
import tempfile
import uvicorn
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call, ANY, PropertyMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from task_runner.mcp.server import (
    app, configure_logging, get_server_info, health_check, 
    create_mcp_server, mcp_request_handler, start, health, info, schema
)
from task_runner.mcp.schema import MCPRequest, MCPResponse


class TestServerInitialization:
    """Tests for server initialization code (lines 27-48)."""

    @patch("task_runner.mcp.server.logger")
    def test_configure_logging_with_debug(self, mock_logger):
        """Test logging configuration with debug mode."""
        configure_logging("DEBUG")
        
        # Verify logger configuration
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count >= 2  # Should add at least file and stderr loggers
        
        # Check that DEBUG level was used
        for call_args in mock_logger.add.call_args_list:
            if "stderr" in str(call_args):
                assert "DEBUG" in str(call_args) or "level='DEBUG'" in str(call_args)

    @patch("task_runner.mcp.server.logger")
    def test_configure_logging_default(self, mock_logger):
        """Test logging configuration with default settings."""
        configure_logging()
        
        # Verify logger configuration
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count >= 2
        
        # Check that INFO level was used by default
        for call_args in mock_logger.add.call_args_list:
            if "stderr" in str(call_args):
                assert "INFO" in str(call_args) or "level='INFO'" in str(call_args)

    @patch("task_runner.mcp.server.os.makedirs")
    @patch("task_runner.mcp.server.logger")
    def test_configure_logging_creates_directory(self, mock_logger, mock_makedirs):
        """Test that logging configuration creates log directory."""
        configure_logging()
        
        # Verify logs directory creation
        mock_makedirs.assert_called_once_with("logs", exist_ok=True)

    @patch("task_runner.mcp.wrapper.create_mcp_server")
    def test_create_mcp_server_success(self, mock_wrapper_create_mcp):
        """Test MCP server creation when successful."""
        # Mock the wrapper function to return a server
        mock_server = Mock()
        mock_wrapper_create_mcp.return_value = mock_server
        
        result = create_mcp_server()
        
        # Verify successful server creation
        assert result == mock_server
        mock_wrapper_create_mcp.assert_called_once()

    @patch("task_runner.mcp.wrapper.create_mcp_server")
    @patch("task_runner.mcp.server.logger")
    def test_create_mcp_server_failure(self, mock_logger, mock_wrapper_create_mcp):
        """Test MCP server creation when it fails."""
        # Mock the wrapper function to return None (failure)
        mock_wrapper_create_mcp.return_value = None
        
        result = create_mcp_server()
        
        # Verify failure handling
        assert result is None
        mock_logger.error.assert_called_once()
        assert "Failed to create MCP server" in mock_logger.error.call_args[0][0]


class TestExceptionHandling:
    """Tests for exception handling in various code paths."""

    @pytest.fixture
    def test_client(self):
        """Create a test client for the FastAPI app."""
        client = TestClient(app)
        return client

    @patch("task_runner.mcp.server.create_mcp_server")
    @patch("task_runner.mcp.server.logger")
    def test_mcp_request_handler_server_error(self, mock_logger, mock_create_mcp):
        """Test request handler when server creation fails (lines 83-84)."""
        # Mock server creation to fail
        mock_create_mcp.return_value = None
        
        # Create a sample request
        request = MCPRequest(method="test_method", params={})
        
        # Process the request
        response = mcp_request_handler(request)
        
        # Verify error response
        assert response.success is False
        assert "error" in response.dict()
        assert "Failed to create MCP server" in response.dict()["error"]
        mock_logger.error.assert_called()

    @patch("task_runner.mcp.server.create_mcp_server")
    @patch("task_runner.mcp.server.logger")
    def test_mcp_request_handler_method_error(self, mock_logger, mock_create_mcp):
        """Test request handler with invalid method (lines 99->122, 102->122)."""
        # Mock MCP server
        mock_server = Mock()
        mock_create_mcp.return_value = mock_server
        
        # Make server.handle_request raise an exception for invalid method
        mock_server.handle_request.side_effect = ValueError("Invalid method")
        
        # Create a sample request with invalid method
        request = MCPRequest(method="invalid_method", params={})
        
        # Process the request
        response = mcp_request_handler(request)
        
        # Verify error response
        assert response.success is False
        assert "error" in response.dict()
        assert "invalid method" in response.dict()["error"].lower()
        mock_logger.error.assert_called()

    @patch("task_runner.mcp.server.create_mcp_server")
    @patch("task_runner.mcp.server.logger")
    def test_mcp_request_handler_exception(self, mock_logger, mock_create_mcp):
        """Test request handler with unexpected exception (lines 104->119, 119->122)."""
        # Mock MCP server
        mock_server = Mock()
        mock_create_mcp.return_value = mock_server
        
        # Make server.handle_request raise an unexpected exception
        mock_server.handle_request.side_effect = Exception("Unexpected error")
        
        # Create a sample request
        request = MCPRequest(method="test_method", params={})
        
        # Process the request
        response = mcp_request_handler(request)
        
        # Verify error response
        assert response.success is False
        assert "error" in response.dict()
        assert "unexpected error" in response.dict()["error"].lower()
        mock_logger.error.assert_called()

    @patch("task_runner.mcp.server.health_check")
    def test_health_endpoint_exception(self, mock_health_check, test_client):
        """Test health endpoint with exception (line 125)."""
        # Mock health_check to raise an exception
        mock_health_check.side_effect = Exception("Health check failed")
        
        # Make the request
        response = test_client.get("/health")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
        assert "health check failed" in data["error"].lower()

    @patch("task_runner.mcp.server.create_mcp_server")
    def test_schema_endpoint_error(self, mock_create_mcp, test_client):
        """Test schema endpoint with server creation error (line 136->128)."""
        # Mock server creation to fail
        mock_create_mcp.return_value = None
        
        # Make the request
        response = test_client.get("/schema")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "failed to create mcp server" in data["error"].lower()


class TestConditionalBranches:
    """Tests for conditional branches in function execution."""

    @pytest.fixture
    def test_client(self):
        """Create a test client for the FastAPI app."""
        client = TestClient(app)
        return client

    @patch("task_runner.mcp.server.create_mcp_server")
    def test_mcp_request_handler_success(self, mock_create_mcp):
        """Test successful request handling branch."""
        # Mock MCP server
        mock_server = Mock()
        mock_create_mcp.return_value = mock_server
        
        # Mock handle_request to return a successful response
        mock_server.handle_request.return_value = {
            "success": True,
            "result": "test result"
        }
        
        # Create a sample request
        request = MCPRequest(method="test_method", params={"key": "value"})
        
        # Process the request
        response = mcp_request_handler(request)
        
        # Verify success response
        assert response.success is True
        assert response.dict()["result"] == "test result"
        # Verify method call with correct params
        mock_server.handle_request.assert_called_once_with({
            "method": "test_method",
            "params": {"key": "value"}
        })

    @patch("task_runner.mcp.server.uvicorn")
    @patch("task_runner.mcp.server.configure_logging")
    @patch("task_runner.mcp.server.logger")
    def test_start_command_debug(self, mock_logger, mock_configure_logging, mock_uvicorn):
        """Test the start command with debug mode."""
        # Call the start function with debug=True
        start(host="127.0.0.1", port=8000, debug=True)
        
        # Verify logging configuration
        mock_configure_logging.assert_called_once_with("DEBUG")
        
        # Verify server startup
        mock_uvicorn.run.assert_called_once()
        call_args = mock_uvicorn.run.call_args[1]
        assert call_args["host"] == "127.0.0.1"
        assert call_args["port"] == 8000
        assert call_args["log_level"] == "debug"

    @patch("task_runner.mcp.server.uvicorn")
    @patch("task_runner.mcp.server.configure_logging")
    @patch("task_runner.mcp.server.logger")
    def test_start_command_no_debug(self, mock_logger, mock_configure_logging, mock_uvicorn):
        """Test the start command without debug mode."""
        # Call the start function with debug=False
        start(host="0.0.0.0", port=3000, debug=False)
        
        # Verify logging configuration
        mock_configure_logging.assert_called_once_with("INFO")
        
        # Verify server startup
        mock_uvicorn.run.assert_called_once()
        call_args = mock_uvicorn.run.call_args[1]
        assert call_args["host"] == "0.0.0.0"
        assert call_args["port"] == 3000
        assert call_args["log_level"] == "info"

    @patch("task_runner.mcp.server.create_mcp_server")
    def test_schema_endpoint_success(self, mock_create_mcp, test_client):
        """Test successful schema endpoint execution."""
        # Mock MCP server with schema
        mock_server = Mock()
        mock_create_mcp.return_value = mock_server
        
        # Create a sample schema
        mock_schema = {
            "functions": {
                "test_function": {
                    "description": "Test function",
                    "parameters": {
                        "properties": {
                            "param1": {"type": "string"}
                        }
                    }
                }
            }
        }
        mock_server.get_schema.return_value = mock_schema
        
        # Make the request
        response = test_client.get("/schema")
        
        # Verify successful response
        assert response.status_code == 200
        assert response.json() == mock_schema


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

