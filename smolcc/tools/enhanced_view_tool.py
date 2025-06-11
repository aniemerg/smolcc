"""
EnhancedViewTool for SmolCC - File reading tool with rich output

This tool reads files from the local filesystem and returns rich output objects
for better display in the terminal.
"""

import os
import mimetypes
import base64
from typing import Optional, Dict, Any, Union
from pathlib import Path

from smolagents import Tool
from smolcc.tool_output import ToolOutput, CodeOutput, TextOutput

# Constants matching the original implementation
MAX_LINES = 2000
MAX_LINE_LENGTH = 2000
TRUNCATED_LINE_SUFFIX = "... (line truncated)"
TRUNCATED_FILE_MESSAGE = f"(Result truncated - total length: {{length}} characters)"

# File extension to language mapping for syntax highlighting
LANGUAGE_MAP = {
    # Python files
    '.py': 'python',
    '.pyx': 'python',
    '.pyw': 'python',
    # JavaScript/TypeScript files
    '.js': 'javascript',
    '.jsx': 'jsx',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    # Web files
    '.html': 'html',
    '.htm': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    # Data files
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.xml': 'xml',
    # Shell scripts
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'bash',
    '.fish': 'fish',
    # C-family languages
    '.c': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.java': 'java',
    # Ruby
    '.rb': 'ruby',
    '.erb': 'erb',
    # Go
    '.go': 'go',
    # Rust
    '.rs': 'rust',
    # Swift
    '.swift': 'swift',
    # Markdown
    '.md': 'markdown',
    '.markdown': 'markdown',
    # Structured Config
    '.ini': 'ini',
    '.cfg': 'ini',
    '.conf': 'ini',
    # Other languages
    '.php': 'php',
    '.pl': 'perl',
    '.kotlin': 'kotlin',
    '.kt': 'kotlin',
    '.lua': 'lua',
    '.sql': 'sql',
    '.r': 'r',
    '.dart': 'dart',
    '.scala': 'scala',
    '.elm': 'elm',
    '.clj': 'clojure',
    '.ex': 'elixir',
    '.exs': 'elixir',
    '.hs': 'haskell',
    '.fs': 'fsharp',
    '.fsx': 'fsharp',
    '.lisp': 'lisp',
    '.matlab': 'matlab',
    '.m': 'matlab',
    '.asm': 'asm6502',
    '.bat': 'batch',
    '.ps1': 'powershell',
    '.dockerfile': 'dockerfile',
}


class EnhancedViewTool(Tool):
    """
    Reads a file from the local filesystem with rich output.
    """
    
    name = "View"
    description = "Retrieves a file's contents from the local filesystem. The **file_path** parameter must be an absolute path (relative paths are not allowed). By default, the tool returns up to 2,000 lines starting at the top of the file. You may optionally specify a line offset and a maximum number of lines—handy for extremely long files—but when feasible, omit these options to load the entire file. Any line longer than 2,000 characters will be truncated. If the target is an image, the tool will render it for you. For Jupyter notebooks (`.ipynb`), use **ReadNotebook** instead."
    inputs = {
        "file_path": {"type": "string", "description": "The absolute path to the file to read"},
        "offset": {"type": "number", "description": "The line number to start reading from. Only provide if the file is too large to read at once", "nullable": True},
        "limit": {"type": "number", "description": "The number of lines to read. Only provide if the file is too large to read at once.", "nullable": True}
    }
    output_type = "string"
    
    def forward(self, file_path: str, offset: Optional[int] = 0, limit: Optional[int] = None) -> Union[ToolOutput, str]:
        """
        Read a file from the local filesystem with rich output formatting.
        
        Args:
            file_path: The absolute path to the file to read
            offset: The line number to start reading from (0-indexed)
            limit: The maximum number of lines to read
            
        Returns:
            A ToolOutput object for rich display
        """
        # Make sure path is absolute
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
            
        # Check if file exists
        if not os.path.exists(file_path):
            return TextOutput(f"Error: File '{file_path}' does not exist")
        if not os.path.isfile(file_path):
            return TextOutput(f"Error: Path '{file_path}' is not a file")
        
        # Check if this is an image file
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('image/'):
            return self._handle_image_file(file_path, mime_type)
            
        # Handle Jupyter notebook files - suggest using ReadNotebook
        if file_path.lower().endswith('.ipynb'):
            return TextOutput(f"This is a Jupyter notebook file. Please use the ReadNotebook tool instead to view it properly.")
        
        # Setup limits
        if limit is None:
            limit = MAX_LINES
        else:
            limit = min(int(limit), MAX_LINES)  # Don't exceed MAX_LINES
            
        # Ensure offset is valid
        offset = max(0, int(offset))  # Must be non-negative
        
        try:
            result = ""
            total_length = 0
            line_count = 0
            displayed_lines = 0
            truncated = False
            
            # Try different encodings if needed
            encodings = ['utf-8', 'latin-1', 'cp1252']
            file_content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        file_content = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            
            # If we couldn't read with any encoding, try as binary
            if file_content is None:
                try:
                    with open(file_path, 'rb') as f:
                        # For binary files, show a message about binary content
                        return TextOutput("This file contains binary content that cannot be displayed as text.")
                except Exception as e:
                    return TextOutput(f"Error reading file: {str(e)}")
            
            line_count = len(file_content)
            # Prepare the formatted output with line numbers
            for i, line in enumerate(file_content):
                
                # Skip lines before offset
                if i < offset:
                    continue
                    
                # Stop after limit lines
                if displayed_lines >= limit:
                    truncated = True
                    break
                
                # Truncate lines that are too long
                if len(line) > MAX_LINE_LENGTH:
                    line = line[:MAX_LINE_LENGTH] + TRUNCATED_LINE_SUFFIX
                
                # Add line with line number
                # Use actual line number from the file, with offset considered
                line_number = i + 1 # i is 0-indexed but we want to show 1-indexed line numbers
                display_line = f"{line_number:6d}\t{line}"
                result += display_line if display_line.endswith('\n') else display_line + '\n'
                displayed_lines += 1
                total_length += len(display_line)
            
            # Add a message if the file was truncated
            if truncated:
                result += f"\n{TRUNCATED_FILE_MESSAGE.format(length=total_length)}\n"
                
            # Return result as a CodeOutput if the file is code, otherwise as TextOutput
            if self._is_code_file(file_path):
                language = self._get_language_for_file(file_path)
                return CodeOutput(result, language=language, line_numbers=False)
            else:
                return TextOutput(result)
            
        except Exception as e:
            return TextOutput(f"Error reading file: {str(e)}")
            
    def _handle_image_file(self, file_path: str, mime_type: str) -> TextOutput:
        """
        Handle image files by creating a message with the image data.
        
        Args:
            file_path: Path to the image file
            mime_type: The mime type of the image
            
        Returns:
            A TextOutput for rich display
        """
        try:
            # Message about image files
            return TextOutput(f"This is an image file ({mime_type}). Images are supported in certain environments but not in a text-only interface.")
        except Exception as e:
            return TextOutput(f"Error handling image file: {str(e)}")
    
    def _is_code_file(self, file_path: str) -> bool:
        """
        Determine if a file is a code file based on its extension or content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file appears to be code, False otherwise
        """
        # Check extension first
        ext = os.path.splitext(file_path)[1].lower()
        if ext in LANGUAGE_MAP:
            return True
            
        # Check some common code patterns if extension doesn't match
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_lines = "".join(f.readlines(10))  # Read first 10 lines
                
            # Look for patterns that suggest code
            code_indicators = [
                "import ", "from ", "def ", "class ", "function ", 
                "var ", "let ", "const ", "#include", "package ", 
                "using ", "public class", "pragma", "{", "<html", "<?php"
            ]
            
            if any(indicator in first_lines for indicator in code_indicators):
                return True
        except:
            pass  # If we can't read the file, assume it's not code
            
        return False
    
    def _get_language_for_file(self, file_path: str) -> str:
        """
        Get the language for syntax highlighting based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language identifier for syntax highlighting
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        # Check for special cases first
        if file_path.lower().endswith('dockerfile'):
            return 'dockerfile'
            
        # Use the extension mapping
        if ext in LANGUAGE_MAP:
            return LANGUAGE_MAP[ext]
            
        # Default to plain text
        return 'text'


# Export the tool as an instance that can be directly used
enhanced_view_tool = EnhancedViewTool()