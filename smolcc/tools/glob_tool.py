"""
GlobTool for SmolCC - File pattern matching tool with rich output

This tool allows finding files using glob pattern matching and returns
rich output objects for better display in the terminal.
"""

import glob as glob_module
import os
import pathlib
import time
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime

from smolagents import Tool
from smolcc.tool_output import ToolOutput, FileListOutput, TextOutput


class GlobTool(Tool):
    """
    Fast file pattern matching tool that works with any codebase size.
    Supports glob patterns and returns matching files as rich FileListOutput.
    """
    
    name = "GlobTool"
    description = """- Lightning-quick file-pattern matcher that scales to projects of any size  
- Understands glob expressions such as "**/*.js" and "src/**/*.ts"  
- Returns matching file paths in descending order of last-modified time  
- Reach for this tool whenever you need to locate files by name patterns  
- For exploratory searches that may involve several rounds of globbing and grepping, use the Agent tool instead  
"""

    inputs = {
        "pattern": {"type": "string", "description": "The glob pattern to match files against"},
        "path": {"type": "string", "description": "The directory to search in. Defaults to the current working directory.", "nullable": True}
    }
    output_type = "string"
    
    def forward(self, pattern: str, path: Optional[str] = None) -> Union[ToolOutput, str]:
        """
        Find files matching the given glob pattern with rich output.
        
        Args:
            pattern: The glob pattern to match files against (e.g. "**/*.py")
            path: The directory to search in (defaults to current working directory)
            
        Returns:
            A FileListOutput object for rich display
        """
        start_time = time.time()
        search_path = path or os.getcwd()
        
        # Make sure search_path is absolute
        search_path = os.path.abspath(search_path) if not os.path.isabs(search_path) else search_path
        
        # Verify path exists
        if not os.path.exists(search_path):
            return TextOutput(f"Error: Path '{search_path}' does not exist")
        if not os.path.isdir(search_path):
            return TextOutput(f"Error: Path '{search_path}' is not a directory")
        
        # Find matching files and determine if results are truncated
        matching_files, truncated = self._find_matching_files(pattern, search_path, limit=100, offset=0)
        
        # If no files found, return a simple message
        if not matching_files:
            return TextOutput(f"No files found matching pattern '{pattern}' in '{search_path}'")
        
        # Convert to rich file info format
        file_info_list = self._convert_to_file_info(matching_files)
        
        # Calculate duration in milliseconds
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Add a note about truncation if needed
        if truncated:
            truncation_note = f"(Results limited to 100 files. Consider using a more specific pattern.)"
            file_info_list.append({
                "name": truncation_note,
                "is_dir": False,
                "size": "",
                "modified_date": "",
                "path": ""
            })
        
        # Return as FileListOutput for rich display
        return FileListOutput(file_info_list, path=f"{search_path} (pattern: {pattern})")
    
    def _find_matching_files(self, pattern: str, search_path: str, limit: int = 100, offset: int = 0) -> Tuple[List[str], bool]:
        """
        Find files matching the pattern with pagination support.
        
        Args:
            pattern: The glob pattern to match
            search_path: The directory to search in
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            Tuple of (matching_files, truncated_flag)
        """
        # Handle Node.js-style patterns like "**/*.ts?(x)" which Python doesn't natively support
        # Handle brace expansion for patterns like "**/*config*.{js,json,ts}"
        if "{" in pattern and "}" in pattern:
            before_brace, rest = pattern.split("{", 1)
            options, after_brace = rest.split("}", 1)
            options_list = options.split(",")
            patterns = [f"{before_brace}{opt}{after_brace}" for opt in options_list]
        elif "?(" in pattern:
            # For "**/*.ts?(x)" pattern, we'll look for both .ts and .tsx files
            if pattern.endswith("?(x)"):
                base_pattern = pattern[:-4]  # Remove "?(x)"
                patterns = [f"{base_pattern}", f"{base_pattern}x"]
            else:
                # For other ?() patterns, split into multiple patterns
                parts = pattern.split("?(")
                if len(parts) == 2 and parts[1].endswith(")"):
                    optional_part = parts[1][:-1]  # Remove trailing ")"
                    patterns = [f"{parts[0]}", f"{parts[0]}{optional_part}"]
                else:
                    # If we can't handle the pattern, just use it as-is
                    patterns = [pattern]
        else:
            patterns = [pattern]
            
        all_matches = []
        for p in patterns:
            # Handle "**" recursive patterns correctly
            # Python's pathlib.glob doesn't handle ** the same way as Node's glob
            if "**" in p:
                # Use glob.glob with recursive=True for ** patterns
                matches = glob_module.glob(
                    os.path.join(search_path, p),
                    recursive=True
                )
                for match in matches:
                    if os.path.isfile(match):  # Only include files, not directories
                        all_matches.append(match)
            else:
                # Use standard pathlib.glob for non-recursive patterns
                base_path = pathlib.Path(search_path)
                all_matches.extend([str(path) for path in base_path.glob(p) if path.is_file()])
                
        # Remove duplicates that might have been added from multiple patterns
        all_matches = list(set(all_matches))
        
        # Sort by modification time (oldest first like in OpenAGI)
        all_matches.sort(key=lambda p: os.path.getmtime(p))
        
        # Determine if results are truncated
        truncated = len(all_matches) > offset + limit
        
        # Apply pagination (offset + limit)
        paginated_matches = all_matches[offset:offset + limit]
        
        return paginated_matches, truncated
    
    def _convert_to_file_info(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Convert file paths to rich file info dictionaries.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of file info dictionaries
        """
        file_info_list = []
        
        for file_path in file_paths:
            try:
                # Get file stats
                stats = os.stat(file_path)
                
                # Format size
                size = stats.st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                
                # Format modification time
                modified_date = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                # Create file info
                file_info = {
                    "name": os.path.basename(file_path),
                    "is_dir": False,  # We only match files, not directories
                    "size": size,
                    "size_str": size_str,
                    "modified": int(stats.st_mtime),
                    "modified_date": modified_date,
                    "path": file_path
                }
                
                file_info_list.append(file_info)
            except (PermissionError, FileNotFoundError):
                # Skip files we can't access
                continue
        
        return file_info_list


# Export the tool as an instance that can be directly used
glob_tool = GlobTool()
enhanced_glob_tool = glob_tool  # Alias for backward compatibility