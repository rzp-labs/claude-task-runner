#!/bin/bash

# Run the Claude Task Runner demo
# This script demonstrates the basic usage of the task runner

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Virtual environment is not activated."
    echo "Please run 'source .venv/bin/activate' first."
    exit 1
fi

# Create a project and parse tasks
echo "Creating a project and parsing tasks..."
python -m task_runner create sample_project input/sample_tasks.md --base-dir ./

# Show the task status (should be all pending)
echo "Initial task status:"
python -m task_runner status --base-dir ./sample_project --json | python -m json.tool

# Run all tasks with quick-demo mode (using simulated responses instead of actual Claude)
echo "Running all tasks in quick demo mode..."
python -m task_runner run --base-dir ./sample_project --quick-demo

# Show final status after tasks complete
echo "Final task status:"
python -m task_runner status --base-dir ./sample_project --json | python -m json.tool

echo "Demo completed! Check the 'results' directory for task outputs."