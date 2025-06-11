"""
Tool output formatting classes for SmolCC.

This module provides classes for tool output formatting with rich display capabilities,
styled to match the desired appearance.
"""
from typing import Any, Optional, List, Dict, Union
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.box import ROUNDED


class ToolOutput:
    """
    Container for tool execution results with display information.
    
    Base class for all tool output formats, provides a consistent
    interface for displaying different types of output.
    """
    
    def __init__(self, data: Any):
        """
        Initialize a ToolOutput object.
        
        Args:
            data: The raw data returned by the tool
        """
        self.data = data
    
    def __str__(self) -> str:
        """String representation for backward compatibility."""
        return str(self.data)
    
    def display(self, console: Console) -> None:
        """
        Display the output in the console using styling.
        
        Args:
            console: The Rich console to display the output in
        """
        # Default display with styling
        console.print(f"  ⎿  {str(self.data)}", style="bright_black")


class ToolCallOutput(ToolOutput):
    """Output format for displaying a tool call."""
    
    def __init__(self, tool_name: str, params: Union[Dict, str, Any]):
        """
        Initialize a ToolCallOutput object.
        
        Args:
            tool_name: Name of the tool being called
            params: Parameters being passed to the tool
        """
        # Format the tool call string 
        if isinstance(params, dict):
            param_str = ", ".join([f"{k}: {repr(v)}" for k, v in params.items()])
            tool_call = f"{tool_name}({param_str})"
        else:
            tool_call = f"{tool_name}({repr(params)})"
        
        # Truncate if too long
        if len(tool_call) > 80:
            tool_call = tool_call[:77] + "..."
            
        super().__init__(tool_call)
        self.tool_name = tool_name
        self.params = params
    
    def display(self, console: Console) -> None:
        """Display the tool call with styling."""
        console.print(f"⏺ {self.data}…", style="yellow")


class TextOutput(ToolOutput):
    """Simple text output with UI styling."""
    
    def display(self, console: Console) -> None:
        """Display the text with UI styling."""
        # For multiline results
        if isinstance(self.data, str) and "\n" in self.data:
            lines = self.data.split("\n")
            first_line = lines[0]
            line_count = len(lines) - 1  # -1 because we're showing the first line
            
            if line_count > 3:
                console.print(f"  ⎿  {first_line}", style="bright_black")
                console.print(f"     ... (+{line_count} lines)", style="bright_black")
            else:
                console.print(f"  ⎿  {self.data}", style="bright_black")
        else:
            console.print(f"  ⎿  {str(self.data)}", style="bright_black")


class CodeOutput(ToolOutput):
    """Code output with syntax highlighting and styling."""
    
    def __init__(self, code: str, language: str = "python", theme: str = "monokai", 
                 line_numbers: bool = True):
        """
        Initialize a CodeOutput object.
        
        Args:
            code: The code to display
            language: The programming language for syntax highlighting
            theme: The color theme for syntax highlighting
            line_numbers: Whether to show line numbers
        """
        super().__init__(code)
        self.language = language
        self.theme = theme
        self.line_numbers = line_numbers
    
    def display(self, console: Console) -> None:
        """Display the code with styling."""
        # Start with the result indicator
        console.print("  ⎿", style="bright_black")
        
        # Show a preview and summary for long code blocks
        if isinstance(self.data, str) and self.data.count("\n") > 10:
            lines = self.data.split("\n")
            first_few_lines = "\n".join(lines[:3])
            line_count = len(lines)
            
            # Show preview with syntax highlighting
            syntax = Syntax(
                first_few_lines,
                self.language,
                theme=self.theme,
                line_numbers=True
            )
            console.print(syntax)
            console.print(f"     ... (+{line_count-3} more lines)", style="bright_black")
        else:
            # For shorter code, show the whole thing with syntax highlighting
            syntax = Syntax(
                str(self.data),
                self.language,
                theme=self.theme,
                line_numbers=self.line_numbers
            )
            console.print(syntax)


class TableOutput(ToolOutput):
    """Tabular data output with styling."""
    
    def __init__(self, data: List[List[Any]], headers: Optional[List[str]] = None):
        """
        Initialize a TableOutput object.
        
        Args:
            data: List of rows, where each row is a list of cell values
            headers: Optional list of column headers
        """
        super().__init__(data)
        self.headers = headers
    
    def display(self, console: Console) -> None:
        """Display the data as a table with UI styling."""
        # Start with the result indicator
        console.print("  ⎿", style="bright_black")
        
        table = Table(box=ROUNDED, show_header=bool(self.headers))
        
        # Add headers if provided
        if self.headers:
            for header in self.headers:
                table.add_column(header, style="cyan bold")
        else:
            # Add columns based on the first row
            if self.data and self.data[0]:
                for _ in range(len(self.data[0])):
                    table.add_column()
        
        # Add rows
        for row in self.data:
            table.add_row(*[str(cell) for cell in row])
        
        console.print(table)


class FileListOutput(ToolOutput):
    """File listing output with UI styling."""
    
    def __init__(self, files: List[Dict[str, Any]], path: str = ""):
        """
        Initialize a FileListOutput object.
        
        Args:
            files: List of file info dictionaries with 'name', 'type', etc.
            path: Base path for the file listing
        """
        super().__init__(files)
        self.path = path
    
    def display(self, console: Console) -> None:
        """Display the file listing with UI styling."""
        # Start with the result indicator and immediately add path
        if self.path:
            console.print(f"  ⎿ Directory: {self.path}", style="bright_black")
        else:
            console.print("  ⎿", style="bright_black")
        
        # Create a table for the file listing
        table = Table(box=None, show_header=True, show_edge=False)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Size", style="magenta")
        
        total_items = len(self.data)
        shown_items = min(10, total_items)  # Limit to 10 items for display
        
        # Add rows for the files
        for i, file in enumerate(self.data[:shown_items]):
            file_type = "[DIR]" if file.get("is_dir", False) else "[FILE]"
            size = file.get("size", "")
            if isinstance(size, int):
                # Format size nicely
                if size < 1024:
                    size = f"{size} B"
                elif size < 1024 * 1024:
                    size = f"{size / 1024:.1f} KB"
                else:
                    size = f"{size / (1024 * 1024):.1f} MB"
            
            table.add_row(file.get("name", ""), file_type, size)
        
        console.print(table)
        
        # Show a summary if items were truncated
        if total_items > shown_items:
            console.print(f"... (+{total_items - shown_items} more items)", style="bright_black")


class AssistantOutput(ToolOutput):
    """Output format for assistant messages."""
    
    def display(self, console: Console) -> None:
        """Display the assistant message with UI styling."""
        console.print(f"{self.data}", style="white")


# Helper function to convert plain results to appropriate ToolOutput objects
def convert_to_tool_output(result: Any) -> ToolOutput:
    """
    Convert a plain result to an appropriate ToolOutput object.
    
    Args:
        result: The result to convert
        
    Returns:
        A ToolOutput object
    """
    if isinstance(result, ToolOutput):
        return result
    
    if isinstance(result, str):
        # Check if it looks like code
        if "\n" in result and any(line.startswith(("    ", "\t", "def ", "class ", "import ")) for line in result.split("\n")):
            return CodeOutput(result)
        else:
            return TextOutput(result)
    
    if isinstance(result, list):
        # Check if it's a list of lists (table)
        if all(isinstance(item, list) for item in result):
            return TableOutput(result)
        # Check if it's a list of dicts with file info
        elif all(isinstance(item, dict) and "name" in item for item in result):
            return FileListOutput(result)
    
    # Default to basic ToolOutput
    return TextOutput(result)