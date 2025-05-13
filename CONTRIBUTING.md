# Contributing to Claude Task Runner

Thank you for your interest in contributing to Claude Task Runner! This document provides guidelines and instructions for contributing to this project.

## Development Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/grahama1970/claude_task_runner.git
   cd claude_task_runner
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   make dev
   ```

   Or manually:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests to verify setup**:
   ```bash
   make test
   ```

## Project Structure

The project follows a three-layer architecture:

- **Core Layer** (`src/task_runner/core/`): Pure business logic with no UI or framework dependencies
- **Presentation Layer** (`src/task_runner/presentation/`): CLI and formatting for user interaction
- **MCP Layer** (`src/task_runner/mcp/`): Integration with Model Context Protocol

## Development Workflow

1. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below

3. **Run tests** to ensure your changes don't break existing functionality:
   ```bash
   make test
   ```

4. **Format your code** using the project's formatting tools:
   ```bash
   make format
   ```

5. **Run linting checks**:
   ```bash
   make lint
   ```

6. **Submit a pull request** with your changes

## Coding Standards

- **Follow PEP 8** style guidelines
- **Use type hints** for all function parameters and return values
- **Write docstrings** for all modules, classes, and functions
- **Keep files under 500 lines** of code
- **Write tests** for all new functionality
- **Follow the layered architecture** design:
  - Core layer should have no dependencies on presentation or MCP layers
  - Presentation layer can depend on core layer but not on MCP layer
  - MCP layer can depend on both core and presentation layers

## Testing

- Write unit tests for core functionality
- Write integration tests for the CLI interface
- Write MCP tests for the MCP integration

Run tests with:
```bash
pytest
```

Or with coverage:
```bash
pytest --cov=task_runner
```

## Documentation

- Update the README.md file with any changes to installation or usage instructions
- Add docstrings to all modules, classes, and functions
- Update the docs/TASK_FORMAT.md file with any changes to the task format

## Pull Request Process

1. Ensure your code follows the coding standards
2. Update the documentation if necessary
3. Run all tests and linting checks
4. Squash your commits into logical units
5. Submit a pull request with a clear description of your changes

## Development Tips

- Use the `make help` command to see available Make targets
- Run `python -m task_runner run --help` to see CLI documentation
- Start the MCP server with `make mcp-server` for testing MCP integration

## Project Organization

```
claude_task_runner/
├── src/
│   └── task_runner/
│       ├── core/           # Core business logic
│       │   └── task_manager.py
│       ├── presentation/   # UI components
│       │   └── formatters.py
│       ├── cli.py          # CLI interface
│       └── mcp/            # MCP integration
│           ├── schema.py
│           ├── wrapper.py
│           └── mcp_server.py
├── scripts/                # Utility scripts
├── tests/                  # Test files
├── docs/                   # Documentation
├── examples/               # Example files
└── pyproject.toml          # Project configuration
```

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

## Questions and Support

If you have questions or need help, please open an issue on the GitHub repository.