# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmolCC is a lightweight code assistant built on HuggingFace's smolagents framework. It provides a command-line interface for code assistance with tool-using capabilities, designed to work with DeepSeek Chat API.

## Architecture

### Core Components

- **`main.py`**: Entry point that handles CLI arguments and orchestrates the agent
- **`smolcc/agent.py`**: Central agent creation and tool loading logic with platform-specific tool selection
- **`smolcc/system_prompt.py`**: Dynamic system prompt generation with directory structure, git status, and platform detection
- **`smolcc/tools/`**: Collection of tool implementations that extend the agent's capabilities

### Agent Architecture

The system uses a `ToolCallingAgent` from smolagents with a `LiteLLMModel` configured for DeepSeek Chat. The agent dynamically loads platform-specific tools:

- **Unix/Linux**: Uses `bash_tool` for command execution
- **Windows**: Uses `powershell_tool` for command execution
- **Cross-platform tools**: edit, glob, grep, ls, replace, view, user_input

### Tool Loading System

Tools are dynamically imported using `importlib.util` with safe error handling. The `get_available_tools()` function in `agent.py:28` manages tool discovery and loading, providing feedback on successful/failed tool imports.

### System Prompt Generation

The system prompt is dynamically generated with:
- Current working directory structure (via `get_directory_structure()`)
- Git repository status and recent commits (if applicable)
- Platform detection (Windows/Unix)
- Current date in platform-appropriate format

## Common Development Commands

### Running the Application

```bash
# Basic usage with a query
python main.py "What files are in the current directory?"

# Interactive mode
python main.py -i

# Set custom working directory
python main.py --cwd /path/to/directory "your query"
```

### Testing

```bash
# Run all tool tests
./run_tool_tests.sh

# Run tests from project root (alternative)
python smolcc/run_tool_tests.py

# Run tests for specific tool
python smolcc/run_tool_tests.py --tool bash

# Verbose test output
python smolcc/run_tool_tests.py --verbose
```

### Installation

```bash
# Development installation
pip install -e .

# Or with uv (faster)
uv pip install -e .
```

### Environment Setup

Required environment variable in `.env`:
```
DEEPSEEK_API_KEY=your_api_key_here
```

## Tool System

### Available Tools

Each tool follows the smolagents `Tool` interface:

- **BashTool/PowerShellTool**: Execute shell commands (platform-specific)
- **EditTool**: Edit files by replacing specific text strings
- **GlobTool**: Find files using glob patterns  
- **GrepTool**: Search file contents with regex
- **LSTool**: List directory contents in tree format
- **ReplaceTool**: Create or overwrite entire files
- **ViewTool**: Read file contents with line numbers
- **UserInputTool**: Get input from user during execution

### Tool Implementation Pattern

Tools are implemented as instances following this pattern:
```python
from smolagents import Tool

tool_name = Tool(
    name="ToolName",
    description="Tool description",
    inputs={"param": {"type": "string", "description": "Parameter description"}},
    output_type="string"
)
```

### Testing Infrastructure

- Test data located in `smolcc/tools/tests/testdata/`
- Individual test files for each tool in `smolcc/tools/tests/`
- Test runner with selective tool testing capability
- Uses pytest-style assertions and test discovery

## Key Design Decisions

- **Platform-specific tool loading**: Automatically selects bash or PowerShell based on platform
- **Dynamic system prompts**: Incorporates real-time directory and git context
- **Safe tool importing**: Graceful degradation when tools fail to load
- **Persistent shell sessions**: BashTool maintains state between command executions
- **Comprehensive error handling**: Tools provide detailed error messages and safety checks