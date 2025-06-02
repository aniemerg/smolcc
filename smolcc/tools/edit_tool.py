"""
FileEditTool for SmolCC - File editing tool

This tool allows editing files in the local filesystem.
It supports replacing specific text strings within files and creating new files.
"""

import os
import difflib
from typing import Optional, Dict, Any
from pathlib import Path

from smolagents import Tool

# Constants
MAX_DIFF_SIZE = 50000  # Maximum diff size in characters
DIFF_TRUNCATION_MESSAGE = "(Diff output truncated due to size)"


class FileEditTool(Tool):
    """
    Edits files in the local filesystem by replacing specific text with new content.
    Can also create new files.
    """
    
    name = "Edit"
    description = """This utility is designed for making in-place edits to files.  
If your goal is to move or rename a file, you should normally reach for the
Bash tool and the `mv` command.  When you need to replace an entire file’s
contents, the Write tool is more appropriate. 

Before you run this utility:

1. Examine the file with the View tool so you fully understand its context.
2. When creating a brand-new file, confirm the directory path is correct:  
   • Use the LS tool to be sure the parent folder exists and is the intended
     location.

Supplying an edit requires three fields:

1. **file_path** – An *absolute* path (starts with “/”) to the file you want to
   change.  
2. **old_string** – The exact text to be replaced.  It *must* appear exactly
   once in the file and include every space, tab, and line break exactly as
   written.  
3. **new_string** – The replacement text that will take the place of
   `old_string`.

The tool swaps **one** occurrence of `old_string` with `new_string` in the
specified file.

CRITICAL RULES FOR USING THIS TOOL
==================================

1. **UNIQUENESS** – `old_string` must single-handedly identify the correct
   spot.  To achieve that:  
   • Provide at least 3–5 lines of context **before** the edit location.  
   • Provide at least 3–5 lines of context **after** the edit location.  
   • Preserve all whitespace, indentation, and surrounding code exactly as it
     appears in the file.

2. **SINGLE INSTANCE** – The utility edits only one occurrence at a time.  
   • Make separate calls for each additional change.  
   • Each call’s `old_string` must uniquely flag its own spot with ample
     context.

3. **VERIFICATION** – Prior to calling the tool:  
   • Count how many times the target text occurs in the file.  
   • If it appears more than once, gather enough surrounding text so the
     `old_string` isolates exactly one instance.  
   • Plan separate calls for every additional instance.

**Failure to follow these rules will cause errors:**

• The edit fails if `old_string` matches multiple places.  
• The edit fails if `old_string` does not match the file *exactly* (including
  whitespace).  
• Insufficient context can lead to changing the wrong code.

GENERAL EDITING GUIDELINES
--------------------------

• Ensure the resulting file is valid, idiomatic code.  
• Never leave the file in a broken state.  
• Always provide absolute paths (begin with “/”).

### Creating a new file

• Use a fresh `file_path` (include new directories if needed).  
• Set `old_string` to an empty string.  
• Put the complete contents of the new file in `new_string`.
"""

    
    inputs = {
        "file_path": {"type": "string", "description": "The absolute path to the file to modify"},
        "old_string": {"type": "string", "description": "The text to replace"},
        "new_string": {"type": "string", "description": "The text to replace it with"}
    }
    output_type = "string"
    
    def forward(self, file_path: str, old_string: str, new_string: str) -> str:
        """
        Edit a file by replacing old_string with new_string.
        
        Args:
            file_path: The absolute path to the file to modify
            old_string: The text to replace
            new_string: The text to replace it with
            
        Returns:
            Success or error message, with a snippet of the edited file
        """
        # Make sure path is absolute
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Check if we're creating a new file
        is_new_file = not os.path.exists(file_path) and old_string == ""
        
        # If creating a new file, ensure parent directory exists
        if is_new_file:
            parent_dir = os.path.dirname(file_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # Create the new file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_string)
                    
                # For new files, directly create a formatted snippet from the new content
                # Instead of using _get_snippet which might produce duplication
                return f"The file {file_path} has been updated. Here's the result of running `cat -n` on a snippet of the edited file:\n{self._add_line_numbers(new_string)}"
            except Exception as e:
                return f"Error creating file '{file_path}': {str(e)}"
        
        # For existing files, check if file exists
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        
        if not os.path.isfile(file_path):
            return f"Error: Path '{file_path}' is not a file"
        
        # Check if file is writable
        if not os.access(file_path, os.W_OK):
            return f"Error: File '{file_path}' is not writable"
        
        # Read the file content
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252']
            file_content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        file_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_content is None:
                return f"Error: Could not decode the file with any supported encoding"
            
            # Special handling for empty old_string
            if old_string == "":
                # For empty strings, we'll either:
                # 1. Create a new file (handled above in is_new_file case)
                # 2. Append to an existing file (handled here)
                new_content = file_content + new_string
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
                # Get a snippet of the modified file
                snippet = self._get_snippet(new_content, "", new_string)
                return self._format_result(file_path, snippet)
            
            # For non-empty old_string, check if it's in the file
            if old_string not in file_content:
                return f"Error: The specified text was not found in the file"
            
            # Count occurrences (only for non-empty strings)
            occurrences = file_content.count(old_string)
            if occurrences > 1:
                return f"Error: The specified text appears {occurrences} times in the file. Please provide more context to uniquely identify which instance to replace."
            
            # Replace the text
            new_content = file_content.replace(old_string, new_string, 1)
            
            # Write the changed content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Get a snippet of the modified file with line numbers (OpenAGI format)
            snippet = self._get_snippet(new_content, old_string, new_string)
            
            # Return success message with snippet of edited file
            return self._format_result(file_path, snippet)
            
        except Exception as e:
            return f"Error editing file '{file_path}': {str(e)}"
    
    def _get_snippet(self, new_content: str, old_string: str, new_string: str) -> str:
        """
        Get a snippet of the modified file around the edit point.
        
        Args:
            new_content: The content of the modified file
            old_string: The string that was replaced
            new_string: The string that replaced it
            
        Returns:
            A snippet of the modified file as a string with line numbers
        """
        # Number of context lines before/after the change
        n_lines_snippet = 4
        
        # For new files or if old_string is empty
        if old_string == "":
            # Just return the first few lines of the new content
            new_lines = new_content.split('\n')
            max_lines = min(len(new_lines), n_lines_snippet * 2)
            return '\n'.join(new_lines[:max_lines])
            
        # Find the position of the old string in the original content
        lines = new_content.split('\n')
        
        # We need to find approximately where the edit happened
        # For simplicity, let's just show the whole file if it's short enough
        if len(lines) <= n_lines_snippet * 2:
            return new_content
            
        # Otherwise, try to find a window around the edit
        # This is an approximation - in a real implementation we'd need to 
        # do more sophisticated diffing to find the exact location
        try:
            # First, try to find where the new_string appears
            new_string_parts = new_string.split('\n')
            first_line_of_new = new_string_parts[0]
            
            # Find this line in the content
            line_index = -1
            for i, line in enumerate(lines):
                if first_line_of_new in line:
                    line_index = i
                    break
            
            # If we found it, create a window around it
            if line_index >= 0:
                start_line = max(0, line_index - n_lines_snippet)
                end_line = min(len(lines), line_index + len(new_string_parts) + n_lines_snippet)
                return '\n'.join(lines[start_line:end_line])
            
            # If we couldn't find it, just return a reasonable chunk from the start
            return '\n'.join(lines[:n_lines_snippet * 2])
            
        except Exception:
            # Fallback to just showing the first few lines
            return '\n'.join(lines[:n_lines_snippet * 2])
    
    def _format_result(self, file_path: str, snippet: str) -> str:
        """
        Format the result message with the edited file details.
        
        Args:
            file_path: The path to the file that was modified
            snippet: A snippet of the modified file
            
        Returns:
            A formatted result message
        """
        # Add line numbers to the snippet
        numbered_snippet = self._add_line_numbers(snippet)
        
        return f"The file {file_path} has been updated. Here's the result of running `cat -n` on a snippet of the edited file:\n{numbered_snippet}"
    
    def _add_line_numbers(self, content: str, start_line: int = 1) -> str:
        """
        Add line numbers to content.
        
        Args:
            content: The content to add line numbers to
            start_line: The line number to start from
            
        Returns:
            Content with line numbers
        """
        lines = content.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            line_number = start_line + i
            result.append(f"{line_number:6d}\t{line}")
            
        return '\n'.join(result)


# Export the tool as an instance that can be directly used
file_edit_tool = FileEditTool()