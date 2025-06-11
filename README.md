# SmolCC

A lightweight code assistant with tool-using capabilities built on HuggingFace's smolagents. Inspired by the tool use in Claude Code, this project provides a simple, easy-to-use interface with access to a range of tools for file manipulation, text search, and command execution. Features rich terminal UI output for an improved user experience.

![SmolCC Screenshot](screen.jpg)

## Features

- Rich terminal UI with syntax highlighting and formatted output
- Command-line interface for code assistance
- Integration with various tools:
  - `BashTool` - Execute bash commands
  - `EditTool` - Make changes to files
  - `GlobTool` - Find files using glob patterns
  - `GrepTool` - Search within files
  - `LSTool` - List directory contents
  - `ReplaceTool` - Create or overwrite files
  - `ViewTool` - Read files
  - `UserInputTool` - Ask for user input during execution

## Installation

### Prerequisites

- Python 3.11 or higher
- An Anthropic API key

### Setting up the environment

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/smolcc.git
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
   ```

4. Create a `.env` file with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

## Usage

### Command-line interface

Run SmolCC from the command line:

```bash
python smolcc.py "What files are in the current directory?"
```

### Interactive mode

Start an interactive session:

```bash
python smolcc.py -i
```

Then enter your queries at the prompt.

### Additional options

SmolCC supports several command-line options:

```bash
python smolcc.py --help
```

Options include:
- `-i, --interactive`: Run in interactive mode
- `--cwd PATH`: Set the working directory
- `--no-log`: Disable logging to file
- `--log-file PATH`: Specify a custom log file path

## Development

This project uses a standard Python package structure:

- `smolcc/` - The main package
  - `agent.py` - The main agent implementation
  - `tool_output.py` - Output formatting classes
  - `tools/` - Tool implementations
    - `tests/` - Unit tests for tools

## License

[MIT License](LICENSE)