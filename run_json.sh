#!/bin/bash
# Run script to test the raw JSON output option
# This script creates a sample task and runs it with raw JSON output

# Ensure we're running from the project root
cd "$(dirname "$0")" || exit 1

# Create sample directories
mkdir -p json_demo/tasks
mkdir -p json_demo/results

# Create sample task
cat << EOF > json_demo/tasks/001_json_test.md
# JSON Test

Please introduce yourself.
EOF

echo "Created sample task in json_demo/tasks/001_json_test.md"

# Run the task runner with raw JSON output
echo "Running the task runner with raw JSON output..."
python -m task_runner.cli.app run --base-dir ./json_demo --raw-json --no-table-repeat

echo "Done! Check json_demo/results for the raw JSON output."