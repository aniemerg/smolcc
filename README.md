# SmolCC

A lightweight code assistant with tool-using capabilities built on HuggingFace's smolagents. Inspired by the tool use in DeepSeek Chat, this project provides a simple, easy-to-use interface with access to a range of tools for file manipulation, text search, and command execution.

## Features

- Command-line interface for code assistance
- Integration with various tools:
  - `BashTool` - Execute bash commands
  - `EditTool` - Make changes to files
  - `GlobTool` - Find files using glob patterns
  - `GrepTool` - Search within files
  - `LSTool` - List directory contents
  - `ReplaceTool` - Create or overwrite files
  - `ViewTool` - Read files

## Installation

### Prerequisites

- Python 3.11 or higher
- A DeepSeek Chat API key

### Setting up the environment

1. Clone this repository:
   ```bash
   git clone [https://github.com/fabiopauli/smolcc.git]
   cd smolcc
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package:
   ```bash
   pip install -e .
   # Alternatively, use uv for faster installation:
   uv pip install -e .
   ```

4. Create a `.env` file with your DeepSeek Chat API key:
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   ```

## Usage

### Command-line interface

Run SmolCC from the command line:

```bash
python main.py "What files are in the current directory?"
```

### Interactive mode

Start an interactive session:

```bash
python main.py -i
```

Then enter your queries at the prompt.

## Development

This project uses a standard Python package structure:

- `smolcc/` - The main package
  - `tools/` - Tool implementations
    - `examples/` - Example usage of tools
    - `tests/` - Unit tests for tools

## License

[MIT License](LICENSE)
