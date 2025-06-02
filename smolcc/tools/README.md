# SmolCC Tools

This directory contains Python implementations of various tools for use with SmolCC.

## GlobTool

The GlobTool allows finding files using glob pattern matching. It supports standard glob patterns and returns matching files sorted by modification time.

### Features

- Fast file pattern matching that works with any codebase size
- Supports glob patterns like "**/*.js" or "src/**/*.ts"
- Returns matching file paths sorted by modification time
- Handles both recursive (**) and non-recursive patterns
- Limits results to 100 files maximum to prevent overwhelming output

### Usage

```python
from glob_tool import glob_tool

# Search for files with a specific pattern
result = glob_tool.forward(pattern="**/*.py")
print(result)

# Search in a specific directory
result = glob_tool.forward(pattern="*.js", path="/path/to/search")
print(result)
```

### Testing

Run the included test script to test the GlobTool against example inputs:

```
python test_glob_tool.py
```

## LSTool

The LSTool lists files and directories in a specified path. It displays a tree-like structure of the directory contents, filtering out hidden files and directories.

### Features

- Lists files and directories in a given path
- Presents content in a tree-like structure
- Filters out hidden files (starting with `.`) and `__pycache__` directories
- Limits results to 1000 files to prevent overwhelming output
- Provides meaningful error messages for invalid paths

### Usage

```python
from ls_tool import ls_tool

# List files in the current directory
result = ls_tool.forward(path="/path/to/directory")
print(result)

# List files with specific patterns to ignore
result = ls_tool.forward(path="/path/to/directory", ignore=["*.tmp", "node_modules"])
print(result)
```

### Testing

Run the included test script to test the LSTool against example inputs:

```
python test_ls_tool.py
```

## ViewTool

The ViewTool (File Reading Tool) allows reading files from the local filesystem. It supports text files with various encodings, and provides specialized handling for binary files and images.

### Features

- Reads files from the local filesystem with proper encoding detection
- Supports line offset and limit parameters for reading parts of large files
- Truncates long lines (>2000 characters) to prevent overwhelming output
- Adds line numbers to output for easier reference
- Special handling for image files and Jupyter notebooks

### Usage

```python
from view_tool import view_tool

# Read an entire file
result = view_tool.forward(file_path="/path/to/file.txt")
print(result)

# Read a portion of a file (lines 10-20)
result = view_tool.forward(file_path="/path/to/file.txt", offset=10, limit=10)
print(result)
```

### Testing

Run the included test script to test the ViewTool against example inputs:

```
python test_view_tool.py
```

## GrepTool

The GrepTool allows searching file contents using regular expressions. It provides functionality similar to the Unix `grep` command, targeting specific patterns in code and text files.

### Features

- Searches file contents using regular expressions
- Supports full regex syntax for complex pattern matching
- Filters files by pattern with the include parameter
- Returns matching file paths and line content sorted by modification time
- Skips binary files and handles different text encodings
- Limits results to prevent overwhelming output

### Usage

```python
from grep_tool import grep_tool

# Search for a pattern in all files
result = grep_tool.forward(pattern="TODO:")
print(result)

# Search in specific file types
result = grep_tool.forward(pattern="console\\.log", include="**/*.js")
print(result)

# Search in a specific directory
result = grep_tool.forward(pattern="import", path="/path/to/search")
print(result)
```

### Testing

Run the included test script to test the GrepTool against example inputs:

```
# Activate the virtual environment first
source /Users/allanniemerg/dev2/smolclaude/.venv/bin/activate
# Or use the full path to the Python interpreter
/Users/allanniemerg/dev2/smolclaude/.venv/bin/python test_grep_tool.py
```

## FileEditTool

The FileEditTool allows editing files in the local filesystem by replacing specific text with new content. It can also create new files if they don't exist.

### Features

- Edits files by replacing specific text strings with new content
- Creates new files when the old_string is empty
- Provides detailed error messages for common issues
- Ensures old_string uniquely identifies the text to replace
- Generates a unified diff to show the changes
- Handles different file encodings and creates backups
- Provides safety checks for file existence and writability

### Usage

```python
from edit_tool import file_edit_tool

# Edit an existing file
result = file_edit_tool.forward(
    file_path="/path/to/file.py",
    old_string="def function_name():\n    # TODO: Implement this\n    pass",
    new_string="def function_name():\n    # Implementation added\n    return 'Implemented!'"
)
print(result)

# Create a new file
result = file_edit_tool.forward(
    file_path="/path/to/new_file.txt",
    old_string="",  # Empty string indicates file creation
    new_string="This is the content of the new file."
)
print(result)
```

### Testing

Run the included test script to test the FileEditTool against example inputs:

```
python test_edit_tool.py
```

## Integration with SmolCC

```python
from glob_tool import glob_tool
from ls_tool import ls_tool
from view_tool import view_tool
from grep_tool import grep_tool
from edit_tool import file_edit_tool
from replace_tool import file_write_tool
from bash_tool import bash_tool
from smolagents import ToolCallingAgent, LiteLLMModel

# Create a model
model = LiteLLMModel(
    model_id="claude-3-7-sonnet-20250219",
    api_key="your_api_key"
)

# Create an agent with multiple tools
agent = ToolCallingAgent(
    tools=[glob_tool, ls_tool, view_tool, grep_tool, file_edit_tool, file_write_tool, bash_tool], 
    model=model
)

# Run the agent with a prompt that might use any of the tools
result = agent.run("Find all TODO comments in Python files and update them with implementations.")
print(result)
```

## Implementation Details

### GlobTool

The GlobTool uses Python's standard library `glob` module and `pathlib` to implement the file pattern matching functionality. It handles both recursive (`**`) and non-recursive patterns, and sorts results by modification time.

Features:

1. Limits results to 100 files
2. Sorts by modification time (newest first)
3. Includes a truncation message when results exceed the limit
4. Returns "No files found" when no matches are found

### LSTool

The LSTool uses Python's `os` module to traverse directories and build a tree-like representation of the file structure. It uses a breadth-first approach to directory traversal and creates a hierarchical tree structure that is then printed in a readable format.

Features:

1. Limits results to 1000 files
2. Ignores hidden files and directories
3. Ignores `__pycache__` directories
4. Includes a truncation message when results exceed the limit
5. Includes a safety warning about potentially malicious files
6. Presents the results in a tree-like format similar to the original implementation

### ViewTool

The ViewTool uses Python's file handling capabilities to read file contents with proper encoding detection. It handles binary files and provides specialized output for images and Jupyter notebooks.

Features:

1. Limits to 2000 lines maximum
2. Truncates lines longer than 2000 characters
3. Adds line numbers to output
4. Provides special handling for image files
5. Suggests using ReadNotebook for Jupyter notebook files

### GrepTool

The GrepTool uses Python's `re` module for regex pattern matching and combines file traversal with content searching. It handles different file types and encodings, and provides formatted output with matching lines.

Features:

1. Limits search to 1000 files maximum
2. Limits results to 100 matching files
3. Shows up to 5 matching lines per file
4. Sorts results by modification time (newest first)
5. Skips binary files with intelligent detection
6. Supports multiple encodings for text files

### FileEditTool

The FileEditTool uses Python's file handling and string manipulation to implement precise edits in files. It leverages the `difflib` module to generate helpful diffs showing the changes made.

Features:

1. Requires unique context to identify the text to replace
2. Provides detailed error messages for common issues
3. Verifies file existence and writability before making changes
4. Supports multiple encodings for text files
5. Generates a unified diff to show changes
6. Creates new files when an empty string is provided as old_string
7. Ensures parent directories exist when creating new files
8. Checks for duplicate occurrences to avoid ambiguous edits

### BashTool

The BashTool uses Python's `subprocess` module to create a persistent shell process for executing bash commands. It uses a unique marker system to distinguish command output and includes safety measures to prevent abuse and incorrect usage.

Features:

1. Creates a persistent shell session that maintains state between calls
2. Implements timeout functionality (defaulting to 30 minutes, max 10 minutes if specified)
3. Implements checks for banned commands to prevent security issues
4. Checks for commands that should be replaced with specialized tools
5. Truncates output to 30,000 characters maximum
6. Handles command interruption for timed-out commands
7. Provides detailed error messages for common issues
8. Manages the shell process lifecycle (creation, cleanup, etc.)

## BashTool

The BashTool executes bash commands in a persistent shell session. It provides safety measures, timeout control, and specialized error handling.

### Features

- Executes bash commands in a persistent shell session
- Environment variables and shell state persist between commands
- Supports timeout control to prevent hanging commands
- Includes security checks for banned commands
- Prevents the use of commands that should be replaced with specialized tools
- Truncates excessive output to prevent overwhelming results
- Provides detailed error messages for common issues

### Usage

```python
from bash_tool import bash_tool

# Execute a simple command
result = bash_tool.forward("echo 'Hello world'")
print(result)

# Execute a command with environment variables
result = bash_tool.forward("TEST_VAR='Hello' && echo $TEST_VAR")
print(result)

# Execute a command with timeout (in milliseconds)
result = bash_tool.forward("sleep 2 && echo 'Done'", timeout=5000)
print(result)
```

### Testing

Run the included test script to test the BashTool:

```
# Activate the virtual environment first
source /Users/allanniemerg/dev2/smolclaude/.venv/bin/activate
# Or use the full path to the Python interpreter
/Users/allanniemerg/dev2/smolclaude/.venv/bin/python test_bash_tool.py
```