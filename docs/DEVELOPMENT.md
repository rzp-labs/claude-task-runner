# Development Setup

## Environment Management

This project uses:
- **Poetry** for dependency management and packaging
- **uv** for virtual environment creation (faster than standard venv)
- **Codacy** for automated code review on commits/PRs

## Initial Setup

1. **Create virtual environment with uv:**
   ```bash
   uv venv .venv
   source .venv/bin/activate  # On macOS/Linux
   ```

2. **Install dependencies with Poetry:**
   ```bash
   poetry install
   ```

3. **Configure Codacy:**
   - Connect your repository to Codacy (via GitHub integration)
   - Codacy will automatically analyze code on push/PR
   - Install IDE extension to view results inline

## Daily Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Add new dependency
poetry add package-name

# Add dev dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Format code
poetry run black src/ tests/

# Lint code locally
poetry run ruff check src/
poetry run pylint src/

# Security checks
poetry run bandit -r src/
poetry run safety check

# Type checking
poetry run mypy src/

# Run tests
poetry run pytest
```

## Code Quality Workflow

### 1. **Local Development (Fast Feedback)**
   ```bash
   # Format on save (configure in IDE)
   black src/
   
   # Quick lint check
   ruff check src/
   
   # Run before commit
   poetry run pre-commit run --all-files
   ```

### 2. **Pre-commit Hooks**
   ```bash
   # Install hooks
   poetry run pre-commit install
   
   # Runs automatically on git commit:
   # - Black (formatting)
   # - Ruff (fast linting)
   # - Mypy (type checking)
   ```

### 3. **Codacy Analysis (On Push/PR)**
   - Comprehensive analysis including:
     - Code patterns and anti-patterns
     - Security vulnerabilities
     - Code complexity
     - Duplication detection
     - Test coverage integration
   - Results visible in:
     - Pull request comments
     - Codacy dashboard
     - IDE (via extension)

### 4. **Manual Codacy CLI Usage (Optional)**
   ```bash
   # Run analysis locally and upload to Codacy
   codacy-cli analyze --tool eslint --format sarif -o results.sarif
   codacy-cli upload -r results.sarif
   ```

## Tool Responsibilities

| Tool | Purpose | When it Runs |
|------|---------|--------------|
| Black | Code formatting | On save / pre-commit |
| Ruff | Fast linting (E, W, F, I, N, B, S) | Local / pre-commit |
| Pylint | Comprehensive linting | Local / CI |
| Mypy | Type checking | Local / pre-commit |
| Bandit | Security scanning | Local / CI |
| Safety | Dependency vulnerabilities | Local / CI |
| Pytest | Test execution | Local / CI |
| Codacy | Complete analysis & reporting | On push/PR |

## Why This Setup?

- **Local tools**: Fast feedback during development
- **Pre-commit**: Catch issues before commit
- **Codacy**: Comprehensive analysis without slowing down local development
- **Poetry + uv**: Best-in-class dependency management with fast environments

This approach provides immediate feedback during development while ensuring comprehensive quality checks through Codacy on every push.