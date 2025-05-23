.PHONY: clean install dev lint test format help

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  make clean       - Remove build artifacts and cache directories"
	@echo "  make install     - Install the package in development mode"
	@echo "  make dev         - Install development dependencies"
	@echo "  make lint        - Run linting checks with black, isort, and mypy"
	@echo "  make test        - Run tests with pytest"
	@echo "  make format      - Format code with black and isort"
	@echo "  make mcp-server  - Start the MCP server"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .mypy_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

lint:
	black --check src tests
	isort --check-only src tests
	mypy src
	ruff check src tests
	pylint src tests --rcfile=pyproject.toml

test:
	pytest

format:
	black src tests
	isort src tests

mcp-server:
	python -m task_runner.mcp.server start