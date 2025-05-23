#!/bin/bash
# Demo script to test the task runner with streaming
# This script creates a sample task and runs it with our updated implementation

# Ensure we're running from the project root
cd "$(dirname "$0")" || exit 1

# Create sample directories
mkdir -p demo_project/tasks
mkdir -p demo_project/results

# Create a sample task
cat << EOF > demo_project/tasks/001_test_task.md
# Test Task

Please analyze the task runner structure and provide a summary of its components.

List all the key modules and their responsibilities.
EOF

echo "Created sample task in demo_project/tasks/001_test_task.md"

# Run the task runner with our updated implementation
echo "Running the task runner with streaming..."
python -m task_runner.cli.app run --base-dir ./demo_project

echo "Done! Check demo_project/results for output."