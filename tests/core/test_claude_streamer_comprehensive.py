#!/usr/bin/env python3
"""
Comprehensive Tests for Claude Streamer Module

This module provides additional test coverage for the claude_streamer.py module,
specifically targeting areas with low coverage as identified in the
coverage report. It focuses on:

1. Streaming initialization and configuration (lines 115->119)
2. Error handling in streaming operations (lines 172-173, 195, 205->210, 207, 220-223, 230)
3. Specific branch conditions (lines 241->248, 245, 249->261, 252->261, 262-264, 279, 283-287)
4. Error propagation (lines 364, 368->371, 372, 375->378, 384, 390)
5. Cleanup operations (lines 411-418)
"""

import asyncio
import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call, ANY, AsyncMock, PropertyMock

import pytest

from task_runner.core.claude_streamer import (
    ClaudeStreamer, ClaudeStreamerError, ClaudeAPIError
)


class TestStreamerInitialization:
    """Tests for streamer initialization and configuration (lines 115->119)."""

    @patch("task_runner.core.claude_streamer.ClaudeStreamer._validate_api_key")
    def test_init_with_api_key(self, mock_validate):
        """Test initialization with API key."""
        # Mock the validation to avoid actual API calls
        mock_validate.return_value = True
        
        # Initialize with API key
        streamer = ClaudeStreamer(api_key="test_api_key")
        
        # Verify initialization
        assert streamer.api_key == "test_api_key"
        assert streamer.initialized is True
        mock_validate.assert_called_once()

    @patch("task_runner.core.claude_streamer.ClaudeStreamer._validate_api_key")
    def test_init_with_env_var(self, mock_validate):
        """Test initialization with environment variable."""
        # Mock the validation
        mock_validate.return_value = True
        
        # Mock environment variable
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env_api_key"}):
            # Initialize without explicit API key
            streamer = ClaudeStreamer()
            
            # Verify initialization
            assert streamer.api_key == "env_api_key"
            assert streamer.initialized is True
            mock_validate.assert_called_once()

    @patch("task_runner.core.claude_streamer.ClaudeStreamer._validate_api_key")
    def test_init_without_api_key(self, mock_validate):
        """Test initialization without API key (should fail initialization)."""
        # Mock the validation to return False (invalid API key)
        mock_validate.return_value = False
        
        # Initialize without API key and with empty environment
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True):
            streamer = ClaudeStreamer()
            
            # Verify initialization failed
            assert streamer.initialized is False
            mock_validate.assert_not_called()  # Should not validate if no key provided

    @patch("task_runner.core.claude_streamer.ClaudeStreamer._validate_api_key")
    def test_init_with_invalid_api_key(self, mock_validate):
        """Test initialization with invalid API key."""
        # Mock the validation to return False (invalid API key)
        mock_validate.return_value = False
        
        # Initialize with invalid API key
        streamer = ClaudeStreamer(api_key="invalid_key")
        
        # Verify initialization failed
        assert streamer.initialized is False
        mock_validate.assert_called_once()


class TestErrorHandling:
    """Tests for error handling in streaming operations (lines 172-173, 195, 205->210, 207, 220-223, 230)."""

    @pytest.fixture
    def mock_streamer(self):
        """Create a mock streamer with initialization bypassed."""
        with patch("task_runner.core.claude_streamer.ClaudeStreamer._validate_api_key", return_value=True):
            streamer = ClaudeStreamer(api_key="test_api_key")
            yield streamer

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_api_call_timeout(self, mock_client_class, mock_streamer):
        """Test API call timeout handling (lines 172-173)."""
        # Mock httpx client to raise a timeout exception
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = asyncio.TimeoutError("Request timed out")
        
        # Call the API with a timeout
        with pytest.raises(ClaudeAPIError) as excinfo:
            await mock_streamer._api_call("/messages", {}, timeout=1.0)
        
        # Verify error handling
        assert "Request timed out" in str(excinfo.value)
        mock_client.post.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_api_call_connection_error(self, mock_client_class, mock_streamer):
        """Test API connection error handling (lines 195)."""
        # Mock httpx client to raise a connection exception
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Connection refused")
        
        # Call the API with a connection error
        with pytest.raises(ClaudeAPIError) as excinfo:
            await mock_streamer._api_call("/messages", {})
        
        # Verify error handling
        assert "Connection refused" in str(excinfo.value)
        mock_client.post.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_api_call_error_response(self, mock_client_class, mock_streamer):
        """Test API error response handling (lines 205->210, 207)."""
        # Mock httpx client to return an error response
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create a mock response with an error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "type": "invalid_request_error",
                "message": "Invalid request parameters"
            }
        }
        mock_client.post.return_value = mock_response
        
        # Call the API
        with pytest.raises(ClaudeAPIError) as excinfo:
            await mock_streamer._api_call("/messages", {})
        
        # Verify error handling
        assert "Invalid request parameters" in str(excinfo.value)
        mock_client.post.assert_called_once()
        mock_response.json.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_api_call_malformed_error_response(self, mock_client_class, mock_streamer):
        """Test API malformed error response handling (lines 220-223)."""
        # Mock httpx client to return a malformed error response
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create a mock response with a malformed error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"unexpected_format": "Something went wrong"}
        mock_client.post.return_value = mock_response
        
        # Call the API
        with pytest.raises(ClaudeAPIError) as excinfo:
            await mock_streamer._api_call("/messages", {})
        
        # Verify error handling
        assert "Unknown error" in str(excinfo.value)
        assert "500" in str(excinfo.value)  # Should include status code
        mock_client.post.assert_called_once()
        mock_response.json.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_api_call_json_decode_error(self, mock_client_class, mock_streamer):
        """Test API JSON decode error handling (line 230)."""
        # Mock httpx client to return a response that raises a JSON decode error
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create a mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_client.post.return_value = mock_response
        
        # Call the API
        with pytest.raises(ClaudeAPIError) as excinfo:
            await mock_streamer._api_call("/messages", {})
        
        # Verify error handling
        assert "Invalid JSON response" in str(excinfo.value)
        mock_client.post.assert_called_once()
        mock_response.json.assert_called_once()


class TestBranchConditions:
    """Tests for specific branch conditions (lines 241->248, 245, 249->261, 252->261, 262-264, 279, 283-287)."""

    @pytest.fixture
    def mock_streamer(self):
        """Create a mock streamer with initialization bypassed."""
        with patch("task_runner.core.claude_streamer.ClaudeStreamer._validate_api_key", return_value=True):
            streamer = ClaudeStreamer(api_key="test_api_key")
            yield streamer

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_stream_response_with_metadata(self, mock_client_class, mock_streamer):
        """Test streaming response with metadata (lines 241->248, 245)."""
        # Mock httpx client to return a streaming response with metadata
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create mock response events
        events = [
            b'event: message_start\ndata: {"type":"message_start","message":{"id":"msg_01","model":"claude-3-opus-20240229","role":"assistant"}}\n\n',
            b'event: content_block_start\ndata: {"type":"content_block_start","index":0,"content_block":{"type":"text"}}\n\n',
            b'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hello"}}\n\n',
            b'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":", world!"}}\n\n',
            b'event: content_block_stop\ndata: {"type":"content_block_stop","index":0}\n\n',
            b'event: message_delta\ndata: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null}}\n\n',
            b'event: message_stop\ndata: {"type":"message_stop"}\n\n',
        ]
        
        # Mock the response streaming
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value.__aiter__.return_value = events
        mock_client.stream.return_value.__aenter__.return_value = mock_response
        
        # Call the stream method
        result = []
        metadata = {}
        async for chunk, meta in mock_streamer.stream_response("Hello", metadata=metadata):
            result.append(chunk)
        
        # Verify streaming behavior
        assert len(result) == 2  # Two text delta events
        assert result[0] == "Hello"
        assert result[1] == ", world!"
        assert "message_id" in metadata
        assert metadata["message_id"] == "msg_01"
        assert metadata["model"] == "claude-3-opus-20240229"
        mock_client.stream.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_stream_response_tool_use(self, mock_client_class, mock_streamer):
        """Test streaming response with tool use events (lines 249->261, 252->261)."""
        # Mock httpx client to return a streaming response with tool use
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create mock response events for tool use
        events = [
            b'event: message_start\ndata: {"type":"message_start","message":{"id":"msg_01","model":"claude-3-opus-20240229","role":"assistant"}}\n\n',
            b'event: content_block_start\ndata: {"type":"content_block_start","index":0,"content_block":{"type":"tool_use","id":"tool_1","name":"calculator"}}\n\n',
            b'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"tool_use_delta","input":{"expression":"2+2"}}}\n\n',
            b'event: content_block_stop\ndata: {"type":"content_block_stop","index":0}\n\n',
            b'event: message_delta\ndata: {"type":"message_delta","delta":{"stop_reason":"tool_use","stop_sequence":null}}\n\n',
            b'event: message_stop\ndata: {"type":"message_stop"}\n\n',
        ]
        
        # Mock the response streaming
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value.__aiter__.return_value = events
        mock_client.stream.return_value.__aenter__.return_value = mock_response
        
        # Call the stream method
        result = []
        metadata = {}
        async for chunk, meta in mock_streamer.stream_response("What is 2+2?", metadata=metadata):
            result.append(chunk)
        
        # Verify tool use handling
        assert len(result) == 1  # One tool use event
        assert isinstance(result[0], dict)  # Tool use is returned as a dictionary
        assert result[0].get("name") == "calculator"
        assert result[0].get("input", {}).get("expression") == "2+2"
        assert "message_id" in metadata
        assert metadata.get("stop_reason") == "tool_use"
        mock_client.stream.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_stream_malformed_events(self, mock_client_class, mock_streamer):
        """Test handling of malformed events (lines 262-264)."""
        # Mock httpx client to return a streaming response with malformed events
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create mock response events with some malformed data
        events = [
            b'event: message_start\ndata: {"type":"message_start","message":{"id":"msg_01","model":"claude-3-opus-20240229","role":"assistant"}}\n\n',
            b'event: content_block_start\ndata: {"type":"content_block_start","index":0,"content_block":{"type":"text"}}\n\n',
            b'event: content_block_delta\ndata: {"malformed_json": "missing fields"}\n\n',  # Malformed event
            b'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Valid content"}}\n\n',
            b'event: content_block_stop\ndata: {"type":"content_block_stop","index":0}\n\n',
            b'event: message_delta\ndata: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null}}\n\n',
            b'event: message_stop\ndata: {"type":"message_stop"}\n\n',
        ]
        
        # Mock the response streaming
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value.__aiter__.return_value = events
        mock_client.stream.return_value.__aenter__.return_value = mock_response
        
        # Call the stream method
        result = []
        metadata = {}
        async for chunk, meta in mock_streamer.stream_response("Hello", metadata=metadata):
            result.append(chunk)
        
        # Verify handling of malformed events (should skip malformed but continue with valid)
        assert len(result) == 1  # Only one valid content delta
        assert result[0] == "Valid content"
        mock_client.stream.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_stream_empty_response(self, mock_client_class, mock_streamer):
        """Test handling of empty stream response (lines 279, 283-287)."""
        # Mock httpx client to return an empty streaming response
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create an empty events list
        events = []
        
        # Mock the response streaming
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value.__aiter__.return_value = events
        mock_client.stream.return_value.__aenter__.return_value = mock_response
        
        # Call the stream method
        result = []
        metadata = {}
        async for chunk, meta in mock_streamer.stream_response("Hello", metadata=metadata):
            result.append(chunk)
        
        # Verify handling of empty response
        assert len(result) == 0  # No content received
        mock_client.stream.assert_called_once()


class TestErrorPropagation:
    """Tests for error propagation in streaming operations (lines 364, 368->371, 372, 375->378, 384, 390)."""

    @pytest.fixture
    def mock_streamer(self):
        """Create a mock streamer with initialization bypassed."""
        with patch("task_runner.core.claude_streamer.ClaudeStreamer._validate_api_key", return_value=True):
            streamer = ClaudeStreamer(api_key="test_api_key")
            yield streamer

    @patch("task_runner.core.claude_streamer.ClaudeStreamer._api_call")
    @pytest.mark.asyncio
    async def test_get_response_error_propagation(self, mock_api_call, mock_streamer):
        """Test error propagation in get_response method (lines 364)."""
        # Mock the API call to raise an error
        mock_api_call.side_effect = ClaudeAPIError("API connection error")
        
        # Call get_response method
        with pytest.raises(ClaudeStreamerError) as excinfo:
            await mock_streamer.get_response("Hello")
        
        # Verify error propagation
        assert "API connection error" in str(excinfo.value)
        mock_api_call.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_stream_response_error_propagation(self, mock_client_class, mock_streamer):
        """Test error propagation in stream_response method (lines 368->371, 372)."""
        # Mock httpx client to raise an error during streaming
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.stream.side_effect = Exception("Connection error during streaming")
        
        # Call stream_response method
        with pytest.raises(ClaudeStreamerError) as excinfo:
            async for chunk, meta in mock_streamer.stream_response("Hello"):
                pass  # This should not execute due to the exception
        
        # Verify error propagation
        assert "Connection error during streaming" in str(excinfo.value)
        mock_client.stream.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_stream_error_response_propagation(self, mock_client_class, mock_streamer):
        """Test error response propagation in streaming (lines 375->378)."""
        # Mock httpx client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create a mock error response
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "type": "invalid_request_error",
                "message": "Invalid request parameters"
            }
        }
        mock_client.stream.return_value.__aenter__.return_value = mock_response
        
        # Call stream_response method
        with pytest.raises(ClaudeStreamerError) as excinfo:
            async for chunk, meta in mock_streamer.stream_response("Hello"):
                pass  # This should not execute due to the exception
        
        # Verify error propagation
        assert "Invalid request parameters" in str(excinfo.value)
        mock_client.stream.assert_called_once()

    @patch("task_runner.core.claude_streamer.ClaudeStreamer._format_messages")
    @pytest.mark.asyncio
    async def test_input_validation_error_propagation(self, mock_format_messages, mock_streamer):
        """Test input validation error propagation (lines 384, 390)."""
        # Mock the format messages method to raise an exception
        mock_format_messages.side_effect = ValueError("Invalid message format")
        
        # Call get_response method
        with pytest.raises(ClaudeStreamerError) as excinfo:
            await mock_streamer.get_response("Hello")
        
        # Verify error propagation
        assert "Invalid message format" in str(excinfo.value)
        mock_format_messages.assert_called_once()


class TestCleanupOperations:
    """Tests for cleanup operations (lines 411-418)."""

    @pytest.fixture
    def mock_streamer(self):
        """Create a mock streamer with initialization bypassed."""
        with patch("task_runner.core.claude_streamer.ClaudeStreamer._validate_api_key", return_value=True):
            streamer = ClaudeStreamer(api_key="test_api_key")
            yield streamer

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self, mock_client_class, mock_streamer):
        """Test cleanup in context manager (lines 411-418)."""
        # Mock httpx client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create a mock session that can be tracked for cleanup
        mock_session = AsyncMock()
        
        # Patch the streamer to use our mock session
        with patch.object(mock_streamer, "_session", mock_session):
            # Use streamer as context manager
            async with mock_streamer:
                # Do some operation
                pass
            
            # Verify session was closed on exit
            mock_session.aclose.assert_called_once()

    @patch("task_runner.core.claude_streamer.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_cleanup_with_exception(self, mock_client_class, mock_streamer):
        """Test cleanup when exception occurs (lines 411-418)."""
        # Mock httpx client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create a mock session that can be tracked for cleanup
        mock_session = AsyncMock()
        
        # Patch the streamer to use our mock session
        with patch.object(mock_streamer, "_session", mock_session):
            # Use streamer as context manager with an exception
            with pytest.raises(ValueError):
                async with mock_streamer:
                    # Raise an exception
                    raise ValueError("Test exception")
            
            # Verify session was still closed despite the exception
            mock_session.aclose.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
