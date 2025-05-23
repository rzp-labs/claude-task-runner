#!/usr/bin/env python3
"""Script to analyze and suggest fixes for failing tests."""

import subprocess
import re

# Run pytest to get all failures
result = subprocess.run(
    ["poetry", "run", "pytest", "tests/", "--tb=short", "-q"],
    capture_output=True,
    text=True,
    cwd="/Users/stephen/Projects/rzp-labs/claude-task-runner"
)

# Parse output to find failing tests
lines = result.stdout.split('\n')
failures = []
for line in lines:
    if 'FAILED' in line or 'ERROR' in line:
        failures.append(line.strip())

print(f"Found {len(failures)} failing tests:\n")
for i, failure in enumerate(failures, 1):
    print(f"{i}. {failure}")

# Common patterns observed:
print("\nCommon failure patterns:")
print("1. 'No task files found' - Tests need to create task files")
print("2. 'AttributeError: TaskManager' - Wrong mocking approach")  
print("3. 'AssertionError: Exit code' - Tests expecting wrong exit codes")
print("4. 'ImportError' - Wrong imports or missing __all__")
print("5. 'KeyError: data' - Wrong assumptions about return values")