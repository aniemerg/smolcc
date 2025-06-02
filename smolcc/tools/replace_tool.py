"""
WriteTool for SmolCC - File writing tool

This tool allows writing (creating or overwriting) files in the local filesystem.
It handles complete file replacements rather than partial edits.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

from smolagents import Tool

MAX_LINES=16000


class WriteTool(Tool):
    """
    Writes content to a file in the local filesystem, creating or overwriting the existing file.
    """
    
    name = "Replace"
    description = """Writes data to a file on the local filesystem, replacing any existing file with the same name.

Before invoking this tool:

1. First inspect the current file with the **ReadFile** tool so you fully understand its contents and context.

2. Directory check (relevant only when creating a brand-new file):  
   • Use the **LS** tool to confirm the parent directory already exists and is indeed the intended destination.
"""

    
    inputs = {
        "file_path": {"type": "string", "description": "The absolute path to the file to write (must be absolute, not relative)"},
        "content": {"type": "string", "description": "The content to write to the file"}
    }
    output_type = "string"
    
    def forward(self, file_path: str, content: str) -> str:
        """
        Write content to a file, creating or overwriting it.
        
        Args:
            file_path: The absolute path to the file to write
            content: The content to write to the file
            
        Returns:
            Success or error message
        """
        # Make sure path is absolute
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Check if parent directory exists
        parent_dir = os.path.dirname(file_path)
        if not os.path.exists(parent_dir):
            return f"Error: Parent directory '{parent_dir}' does not exist"
        
        # Check file permissions if the file already exists
        if os.path.exists(file_path):
            if not os.path.isfile(file_path):
                return f"Error: Path '{file_path}' exists but is not a file"
                
            if not os.access(file_path, os.W_OK):
                return f"Error: File '{file_path}' is not writable"
        
        # Write the content to the file
        try:
            file_existed = os.path.exists(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Return success message
            if not file_existed:
                return f"File created successfully at: {file_path}"
            else:
                # Add cat -n style line numbering for updates
                preview_lines = content.splitlines()[:MAX_LINES] 
                numbered_lines = [f"{i+1:6d}\t{line}" for i, line in enumerate(preview_lines)]
                numbered_preview = "\n".join(numbered_lines)
                
                return f"The file {file_path} has been updated. Here's the result of running `cat -n` on a snippet of the edited file:\n{numbered_preview}"
            
        except Exception as e:
            return f"Error writing to file '{file_path}': {str(e)}"


# Export the tool as an instance that can be directly used
write_tool = WriteTool()