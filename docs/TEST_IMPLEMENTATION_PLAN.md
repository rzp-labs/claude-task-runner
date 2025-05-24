# Test Implementation Plan for Claude Task Runner

## Goal

Increase test coverage from **30.30%** to **80%** minimum, focusing on critical functionality first.

## Test Priority Levels

- **P0 (Critical)**: Core business logic that affects all operations
- **P1 (High)**: User-facing functionality and main workflows
- **P2 (Medium)**: Supporting utilities and edge cases
- **P3 (Low)**: Nice-to-have tests for completeness

## Implementation Tasks

### Phase 1: Core Functionality Tests (P0)

**Target Coverage: 30% → 55%**

#### Task 1.1: Claude Streamer Tests

- **Priority**: P0
- **Module**: `core/claude_streamer.py` (0% → 80%)
- **Focus Areas**:
  - Claude executable detection and validation
  - Stream output processing and buffering
  - Process lifecycle management
  - Timeout handling and cancellation
  - Error scenarios (missing executable, process failures)
- **Dependencies**: Mock subprocess module

#### Task 1.2: Task Manager Enhanced Tests

- **Priority**: P0
- **Module**: `core/task_manager.py` (42.19% → 85%)
- **Focus Areas**:
  - Task execution workflow
  - State management and transitions
  - File I/O operations
  - Error recovery mechanisms
  - Edge cases (empty tasks, malformed files)
- **Dependencies**: Existing test fixtures

### Phase 2: CLI Integration Tests (P1)

**Target Coverage: 55% → 70%**

#### Task 2.1: CLI App Command Tests

- **Priority**: P1
- **Module**: `cli/app.py` (11.24% → 75%)
- **Focus Areas**:
  - `run` command with various options
  - `status` command output formatting
  - `create` command file generation
  - `clean` command safety checks
  - Error handling and user feedback
- **Dependencies**: Typer testing client

#### Task 2.2: Validator Complete Coverage

- **Priority**: P1
- **Module**: `cli/validators.py` (32.26% → 90%)
- **Focus Areas**:
  - All validation functions with valid/invalid inputs
  - Boundary conditions
  - Error message clarity
- **Dependencies**: None

### Phase 3: MCP Integration Tests (P1)

**Target Coverage: 70% → 80%**

#### Task 3.1: MCP Server Tests

- **Priority**: P1
- **Modules**: `mcp/*.py` (0-31% → 70%)
- **Focus Areas**:
  - Server initialization and configuration
  - Request/response handling
  - Schema validation
  - FastMCP wrapper integration
- **Dependencies**: Mock FastMCP, asyncio testing

### Phase 4: Supporting Tests (P2)

**Target Coverage: 80% → 85%**

#### Task 4.1: Entry Point Tests

- **Priority**: P2
- **Module**: `__main__.py` (0% → 80%)
- **Focus Areas**:
  - CLI invocation
  - Error handling at startup

#### Task 4.2: Edge Cases and Error Scenarios

- **Priority**: P2
- **All Modules**
- **Focus Areas**:
  - Network failures
  - File permission issues
  - Concurrent execution
  - Resource cleanup

## Test Implementation Guidelines

### 1. Test Structure

```python
# Standard test file structure
class TestModuleName:
    """Tests for module_name functionality."""

    def test_feature_happy_path(self):
        """Test normal operation of feature."""

    def test_feature_edge_case(self):
        """Test boundary conditions."""

    def test_feature_error_handling(self):
        """Test error scenarios."""
```

### 2. Mocking Strategy

- Mock external dependencies (Claude executable, file system where appropriate)
- Use real implementations for core business logic
- Create reusable fixtures for common test data

### 3. Coverage Requirements

- Each module must have ≥70% line coverage
- Critical paths must have 100% branch coverage
- All error handlers must be tested

## Resource Requirements

### Tools

- pytest and pytest-cov (already configured)
- pytest-mock for mocking
- pytest-asyncio for async tests
- typer[testing] for CLI tests

### Test Data

- Sample task files in various formats
- Mock Claude responses
- Error condition simulations

## Success Metrics

1. Overall test coverage ≥ 80%
2. All P0 and P1 tasks completed
3. No critical paths untested
4. CI/CD pipeline passes all tests
5. Test execution time < 5 minutes

## Timeline

- **Week 1**: Complete Phase 1 (Core Functionality)
- **Week 2**: Complete Phase 2 (CLI Integration)
- **Week 3**: Complete Phase 3 (MCP Integration)
- **Week 4**: Complete Phase 4 (Supporting Tests) and documentation

## Dependencies

- No blockers identified
- All test frameworks already installed
- Mock data can be generated as needed

## Risks and Mitigation

1. **Risk**: Mocking Claude executable behavior accurately

   - **Mitigation**: Create comprehensive mock responses based on actual Claude output

2. **Risk**: Async testing complexity for MCP

   - **Mitigation**: Use pytest-asyncio and established patterns

3. **Risk**: Test maintenance overhead
   - **Mitigation**: Keep tests simple and focused on behavior, not implementation
