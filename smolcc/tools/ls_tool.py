"""
LS Tool for SmolCC - Directory listing tool with rich output

This tool lists files and directories in a given path with rich formatting.
"""

import os
import fnmatch
import stat
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple, Union

from smolagents import Tool
from smolcc.tool_output import FileListOutput, TextOutput, ToolOutput

# Constants
MAX_FILES = 1000
TRUNCATED_MESSAGE = f"There are more than {MAX_FILES} files in the repository."


class LSTool(Tool):
    """
    Lists files and directories in a given path with rich formatting.
    """
    
    name = "LS"
    description = "Displays a directory's contents—files and sub-directories—at the location specified by **path**. The **path** argument must be an absolute path (it cannot be relative). You may optionally supply an **ignore** parameter: an array of glob patterns that should be skipped. If you already know the directories you want to scan, the Glob and Grep tools are generally the better choice."
    inputs = {
        "path": {"type": "string", "description": "The absolute path to the directory to list (must be absolute, not relative)"},
        "ignore": {"type": "array", "description": "List of glob patterns to ignore", "items": {"type": "string"}, "nullable": True}
    }
    output_type = "string"
    
    def forward(self, path: str, ignore: Optional[List[str]] = None) -> Union[ToolOutput, str]:
        """
        List files and directories in the given path with rich output.
        
        Args:
            path: The absolute path to the directory to list
            ignore: Optional list of glob patterns to ignore
            
        Returns:
            A FileListOutput object for rich display
        """
        # Ensure path is absolute
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        # Check if path exists and is a directory
        if not os.path.exists(path):
            return TextOutput(f"Error: Path '{path}' does not exist")
        if not os.path.isdir(path):
            return TextOutput(f"Error: Path '{path}' is not a file")
        
        # Get file information for the directory
        file_info = self._get_directory_contents(path, ignore or [])
        
        # Return as FileListOutput for rich display
        return FileListOutput(file_info, path)
    
    def _get_directory_contents(self, path: str, ignore_patterns: List[str]) -> List[Dict[str, Any]]:
        """
        Get information about files and directories in the given path.
        
        Args:
            path: The directory path to list
            ignore_patterns: List of glob patterns to ignore
            
        Returns:
            List of dictionaries with file information
        """
        file_info = []
        
        try:
            # Get all entries in the directory
            entries = os.listdir(path)
            
            # Sort entries alphabetically (directories first, then files)
            entries.sort()
            
            # Process each entry
            for entry in entries:
                entry_path = os.path.join(path, entry)
                
                # Skip if this path should be filtered
                if self._should_skip(entry_path, ignore_patterns):
                    continue
                
                try:
                    # Get file stats
                    stats = os.stat(entry_path)
                    is_dir = os.path.isdir(entry_path)
                    
                    # Create file info dictionary
                    info = {
                        "name": entry,
                        "is_dir": is_dir,
                        "size": stats.st_size,
                        "modified": int(stats.st_mtime),
                        "modified_date": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "path": entry_path
                    }
                    
                    file_info.append(info)
                    
                    if len(file_info) >= MAX_FILES:
                        break
                except (PermissionError, FileNotFoundError):
                    # Skip entries we can't access
                    continue
        except (PermissionError, FileNotFoundError) as e:
            return [{"name": f"Error listing directory: {str(e)}", "is_dir": False, "size": 0}]
        
        # Sort the list - directories first, then files alphabetically
        file_info.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        return file_info
    
    def _should_skip(self, path: str, ignore_patterns: List[str]) -> bool:
        """
        Determines if a path should be skipped.
        
        Args:
            path: Path to check
            ignore_patterns: List of glob patterns to ignore
            
        Returns:
            True if the path should be skipped, False otherwise
        """
        basename = os.path.basename(path.rstrip(os.path.sep))
        
        # Skip hidden files and directories
        if basename.startswith('.') and basename != '.':
            return True
            
        # Skip __pycache__ directories
        if basename == '__pycache__' or '__pycache__/' in path.replace(os.path.sep, '/'):
            return True
            
        # Skip paths matching ignore patterns
        if any(fnmatch.fnmatch(path, pattern) for pattern in ignore_patterns):
            return True
            
        return False


# Export the tool as an instance that can be directly used
ls_tool = LSTool()
enhanced_ls_tool = ls_tool  # Alias for backward compatibility