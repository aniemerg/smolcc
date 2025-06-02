"""
ViewTool for SmolCC - File reading tool

This tool reads files from the local filesystem.
It supports reading text files with optional line limiting and offsetting.
"""

import os
import mimetypes
import base64
from typing import Optional, Dict, Any
from pathlib import Path

from smolagents import Tool

# Constants matching the original implementation
MAX_LINES = 2000
MAX_LINE_LENGTH = 2000
TRUNCATED_LINE_SUFFIX = "... (line truncated)"
TRUNCATED_FILE_MESSAGE = f"(Result truncated - total length: {{length}} characters)"


class ViewTool(Tool):
    """
    Reads a file from the local filesystem with various options.
    """
    
    name = "View"
    description = "Retrieves a file’s contents from the local filesystem. The **file_path** parameter must be an absolute path (relative paths are not allowed). By default, the tool returns up to 2,000 lines starting at the top of the file. You may optionally specify a line offset and a maximum number of lines—handy for extremely long files—but when feasible, omit these options to load the entire file. Any line longer than 2,000 characters will be truncated. If the target is an image, the tool will render it for you. For Jupyter notebooks (`.ipynb`), use **ReadNotebook** instead."
    inputs = {
        "file_path": {"type": "string", "description": "The absolute path to the file to read"},
        "offset": {"type": "number", "description": "The line number to start reading from. Only provide if the file is too large to read at once", "nullable": True},
        "limit": {"type": "number", "description": "The number of lines to read. Only provide if the file is too large to read at once.", "nullable": True}
    }
    output_type = "string"
    
    def forward(self, file_path: str, offset: Optional[int] = 0, limit: Optional[int] = None) -> str:
        """
        Read a file from the local filesystem.
        
        Args:
            file_path: The absolute path to the file to read
            offset: The line number to start reading from (0-indexed)
            limit: The maximum number of lines to read
            
        Returns:
            The content of the file, with line numbers prepended
        """
        # Make sure path is absolute
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
            
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        if not os.path.isfile(file_path):
            return f"Error: Path '{file_path}' is not a file"
        
        # Check if this is an image file
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('image/'):
            return self._handle_image_file(file_path, mime_type)
            
        # Handle Jupyter notebook files - suggest using ReadNotebook
        if file_path.lower().endswith('.ipynb'):
            return f"This is a Jupyter notebook file. Please use the ReadNotebook tool instead to view it properly."
        
        # Setup limits
        if limit is None:
            limit = MAX_LINES
        else:
            limit = min(int(limit), MAX_LINES)  # Don't exceed MAX_LINES
            truncated = True
            
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
                        return "This file contains binary content that cannot be displayed as text."
                except Exception as e:
                    return f"Error reading file: {str(e)}"
            
            line_count = len(file_content)
            # Prepare the formatted output with line numbers
            for i, line in enumerate(file_content):
                
                # Skip lines before offset
                if i < offset-1:
                    continue
                    
                # Stop after limit lines
                if displayed_lines >= limit:
                    # truncated = True
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
                
            # Add line separator - deprecated
            # result += "\n" + "-" * 80 + "\n"
                
            return result
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
            
    def _handle_image_file(self, file_path: str, mime_type: str) -> str:
        """
        Handle image files by creating a message with the image data.
        
        Args:
            file_path: Path to the image file
            mime_type: The mime type of the image
            
        Returns:
            A string indicating this is an image file
        """
        try:
            # Message about image files
            return f"This is an image file ({mime_type}). Images are supported in certain environments but not in a text-only interface."
        except Exception as e:
            return f"Error handling image file: {str(e)}"


# Export the tool as an instance that can be directly used
view_tool = ViewTool()