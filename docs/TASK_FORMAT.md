# Task Format Guide

This guide explains how to structure task list files for the Claude Task Runner.

## Basic Structure

Task list files are Markdown files with a specific structure that allows the Task Runner to split them into individual task files. Here's the basic format:

```markdown
# Project Title

This is an optional project overview description.

## Task 1: First Task Title

Content for the first task...
This can include multiple paragraphs, code snippets, and other Markdown elements.

## Task 2: Second Task Title

Content for the second task...
More details about what the task should accomplish.

## Task 3: Third Task Title

Content for the third task...
```

The Task Runner will parse this file and create individual task files named:
- `001_first_task_title.md`
- `002_second_task_title.md`
- `003_third_task_title.md`

## Task Content Guidelines

Each task should be self-contained and include all the necessary context for Claude to understand and complete the task. Consider including:

1. **Clear Objective**: Start with a clear statement of what the task should accomplish
2. **Context**: Provide any background information needed
3. **Steps**: List the specific steps or requirements
4. **Examples**: Include examples where helpful
5. **Acceptance Criteria**: Define what a successful completion looks like

## Example Task

Here's an example of a well-structured task:

```markdown
## Task 2: Implement Data Processing Module

Create a Python module for processing user data from CSV files.

### Context
The application needs to import user data from various CSV formats and convert it 
to a standardized internal representation.

### Requirements
1. Create a `data_processor.py` module in the `src/utils` directory
2. Implement the following functions:
   - `load_csv(file_path)`: Load a CSV file and return a list of dictionaries
   - `validate_data(data)`: Validate that the data meets our schema requirements
   - `transform_data(data)`: Transform the data to our internal format
   - `save_processed_data(data, output_path)`: Save the processed data to a file

### Technical Details
- Use the `csv` module from the standard library
- Handle errors gracefully with appropriate error messages
- Add type hints for all functions
- Include docstrings explaining each function's purpose and parameters
- Follow the project's coding style guide

### Examples
Input CSV format:
```csv
id,name,email,signup_date
1,John Doe,john@example.com,2023-01-15
2,Jane Smith,jane@example.com,2023-02-20
```

Expected output format:
```json
[
  {
    "user_id": 1,
    "full_name": "John Doe",
    "email_address": "john@example.com",
    "metadata": {
      "signup": "2023-01-15",
      "verified": false
    }
  },
  ...
]
```
```

## Tips for Effective Tasks

1. **Be Specific**: Clearly specify what each task should accomplish
2. **Provide Context**: Include enough background information for Claude to understand the task
3. **Set Boundaries**: Clearly define the scope of the task
4. **Include Examples**: Provide examples of inputs and expected outputs
5. **Define Success**: Include acceptance criteria so Claude knows when the task is complete
6. **Break Down Complex Tasks**: If a task is too complex, break it into smaller, more manageable tasks

## Task Execution Order

Tasks are executed in the order they appear in the task list file. Make sure to structure your tasks so that dependencies are handled correctly.

## Advanced Features

### Cross-Task References

If tasks need to reference each other, you can use the task number:

```markdown
## Task 1: Create Database Schema

Design the database schema for the application...

## Task 2: Implement ORM Models

Implement ORM models based on the database schema created in Task 1.
```

### Including Code Snippets

You can include code snippets using standard Markdown code blocks:

```markdown
## Task: Implement Authentication

Create a function to authenticate users:

```python
def authenticate(username: str, password: str) -> bool:
    # Your implementation here
    pass
```
```

## Example Task List

See the `examples/sample_task_list.md` file for a complete example of a task list.