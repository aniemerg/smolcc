"""
ChangeDirectoryTool for SmolCC - Smart working directory management

This tool allows the agent to change its working directory with validation,
helpful suggestions, and safety features.
"""

import os
import platform
from pathlib import Path
from typing import Optional

from smolagents import Tool


class ChangeDirectoryTool(Tool):
    """
    Smart tool for changing the agent's working directory with validation and helpful features.
    """
    
    name = "ChangeDirectory"
    description = """Changes the agent's working directory to the specified path with smart validation and helpful features.

Features:
- Validates that the target directory exists and is accessible
- Supports both absolute and relative paths
- Expands user home directory (~) and environment variables
- Provides helpful suggestions for similar directory names when target doesn't exist
- Shows current directory before and after change
- Prevents changing to restricted system directories for safety
- Cross-platform path handling (Windows/Unix)

Usage Examples:
- cd_tool.forward(path="./src") - Change to src subdirectory
- cd_tool.forward(path="~/Documents") - Change to user's Documents folder
- cd_tool.forward(path="/tmp") - Change to absolute path
- cd_tool.forward(path="..") - Go up one directory level
- cd_tool.forward(path="-") - Go back to previous directory (if supported)

Safety Features:
- Validates directory existence before changing
- Prevents access to system-critical directories
- Provides clear error messages with suggestions
- Shows directory contents summary after successful change"""

    inputs = {
        "path": {
            "type": "string", 
            "description": "The target directory path (absolute, relative, or special paths like ~, .., -)"
        }
    }
    output_type = "string"
    
    def __init__(self):
        """Initialize the ChangeDirectoryTool."""
        super().__init__()
        self.previous_directory = None
        self.restricted_dirs = self._get_restricted_directories()
    
    def _get_restricted_directories(self) -> list[str]:
        """Get list of restricted system directories to prevent accidental access."""
        if platform.system() == "Windows":
            return [
                "C:\\Windows\\System32",
                "C:\\Windows\\SysWOW64", 
                "C:\\Program Files",
                "C:\\Program Files (x86)"
            ]
        else:
            return [
                "/bin",
                "/sbin", 
                "/usr/bin",
                "/usr/sbin",
                "/boot",
                "/dev",
                "/proc",
                "/sys"
            ]
    
    def forward(self, path: str) -> str:
        """
        Change the working directory to the specified path.
        
        Args:
            path: The target directory path
            
        Returns:
            Status message with directory change information
        """
        try:
            # Store current directory
            current_dir = os.getcwd()
            
            # Handle special paths
            if path == "-" and self.previous_directory:
                target_path = self.previous_directory
                special_note = " (previous directory)"
            elif path == "~":
                target_path = str(Path.home())
                special_note = " (home directory)"
            else:
                # Expand user directory and environment variables
                expanded_path = os.path.expanduser(os.path.expandvars(path))
                target_path = os.path.abspath(expanded_path)
                special_note = ""
            
            # Validate target directory
            validation_result = self._validate_directory(target_path)
            if not validation_result["valid"]:
                return validation_result["message"]
            
            # Check if it's a restricted directory
            if self._is_restricted_directory(target_path):
                return f"Error: Cannot change to restricted system directory '{target_path}'. This is prevented for safety reasons."
            
            # Attempt to change directory
            try:
                os.chdir(target_path)
                self.previous_directory = current_dir
                
                # Get new directory info
                new_dir = os.getcwd()
                dir_summary = self._get_directory_summary(new_dir)
                
                return f"""Directory changed successfully!

Previous: {current_dir}
Current:  {new_dir}{special_note}

{dir_summary}"""
                
            except PermissionError:
                return f"Error: Permission denied. Cannot access directory '{target_path}'. Check if you have the necessary permissions."
            except Exception as e:
                return f"Error: Failed to change directory to '{target_path}': {str(e)}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _validate_directory(self, path: str) -> dict:
        """
        Validate that the target directory exists and is accessible.
        
        Args:
            path: The directory path to validate
            
        Returns:
            Dictionary with validation result and message
        """
        if not os.path.exists(path):
            suggestions = self._get_directory_suggestions(path)
            suggestion_text = f"\n\nDid you mean one of these?\n{suggestions}" if suggestions else ""
            
            return {
                "valid": False,
                "message": f"Error: Directory '{path}' does not exist.{suggestion_text}"
            }
        
        if not os.path.isdir(path):
            return {
                "valid": False,
                "message": f"Error: '{path}' exists but is not a directory."
            }
        
        return {"valid": True, "message": ""}
    
    def _is_restricted_directory(self, path: str) -> bool:
        """
        Check if the path is a restricted system directory.
        
        Args:
            path: The directory path to check
            
        Returns:
            True if restricted, False otherwise
        """
        normalized_path = os.path.normpath(path).lower()
        
        for restricted in self.restricted_dirs:
            if normalized_path.startswith(os.path.normpath(restricted).lower()):
                return True
        
        return False
    
    def _get_directory_suggestions(self, path: str) -> str:
        """
        Provide helpful suggestions for similar directory names.
        
        Args:
            path: The invalid directory path
            
        Returns:
            String with suggestions or empty string if none found
        """
        try:
            parent_dir = os.path.dirname(path)
            target_name = os.path.basename(path).lower()
            
            if not os.path.exists(parent_dir):
                return ""
            
            # Find similar directory names
            similar_dirs = []
            for item in os.listdir(parent_dir):
                item_path = os.path.join(parent_dir, item)
                if os.path.isdir(item_path):
                    # Simple similarity check (contains target or target contains item)
                    if (target_name in item.lower() or 
                        item.lower() in target_name or
                        self._levenshtein_distance(target_name, item.lower()) <= 2):
                        similar_dirs.append(item)
            
            if similar_dirs:
                suggestions = "\n".join(f"  - {parent_dir}/{dir_name}" for dir_name in similar_dirs[:5])
                return suggestions
            
            return ""
            
        except Exception:
            return ""
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Edit distance between the strings
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _get_directory_summary(self, path: str) -> str:
        """
        Get a helpful summary of the directory contents.
        
        Args:
            path: The directory path
            
        Returns:
            Summary string with directory information
        """
        try:
            items = os.listdir(path)
            if not items:
                return "Directory is empty."
            
            files = []
            dirs = []
            
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            summary_parts = []
            
            if dirs:
                dir_count = len(dirs)
                dir_preview = ", ".join(dirs[:3])
                if dir_count > 3:
                    dir_preview += f" (and {dir_count - 3} more)"
                summary_parts.append(f"📁 {dir_count} directories: {dir_preview}")
            
            if files:
                file_count = len(files)
                file_preview = ", ".join(files[:3])
                if file_count > 3:
                    file_preview += f" (and {file_count - 3} more)"
                summary_parts.append(f"📄 {file_count} files: {file_preview}")
            
            return "\n".join(summary_parts)
            
        except PermissionError:
            return "Directory contents not accessible (permission denied)."
        except Exception as e:
            return f"Could not read directory contents: {str(e)}"


# Export the tool as an instance that can be directly used
cd_tool = ChangeDirectoryTool()