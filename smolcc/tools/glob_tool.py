"""
GlobTool for SmolCC - File pattern matching tool

This tool allows finding files using glob pattern matching.
It supports standard glob patterns and returns matching files sorted by modification time.
"""

import glob as glob_module
import os
import pathlib
import time
from typing import List, Optional, Dict, Any, Tuple

from smolagents import Tool


class GlobTool(Tool):
    """
    Fast file pattern matching tool that works with any codebase size.
    Supports glob patterns and returns matching files sorted by modification time.
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
    
    def forward(self, pattern: str, path: Optional[str] = None) -> str:
        """
        Find files matching the given glob pattern.
        
        Args:
            pattern: The glob pattern to match files against (e.g. "**/*.py")
            path: The directory to search in (defaults to current working directory)
            
        Returns:
            A newline-separated list of matching file paths
        """
        start_time = time.time()
        search_path = path or os.getcwd()
        
        # Make sure search_path is absolute
        search_path = os.path.abspath(search_path) if not os.path.isabs(search_path) else search_path
        
        # Use pathlib to handle paths and patterns
        base_path = pathlib.Path(search_path)
        
        # Find matching files and determine if results are truncated
        matching_files, truncated = self._find_matching_files(pattern, search_path, limit=100, offset=0)
        
        # Format the result for the assistant
        result_str = self._format_result_for_assistant(matching_files, truncated)
        
        # Calculate duration in milliseconds
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Create structured output data
        output_data = {
            "filenames": matching_files,
            "durationMs": duration_ms,
            "numFiles": len(matching_files),
            "truncated": truncated
        }
        
        # We need to return a string with a structured format
        return result_str
    
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
    
    def _format_result_for_assistant(self, files: List[str], truncated: bool) -> str:
        """
        Format the file list as a string for the assistant.
        
        Args:
            files: List of file paths
            truncated: Whether the results were truncated
            
        Returns:
            Formatted string result
        """
        if not files:
            return "No files found"
        
        result = "\n".join(files)
        
        # Only add truncation message if results were actually truncated
        if truncated:
            result += "\n(Results are truncated. Consider using a more specific path or pattern.)"
            
        return result

# Export the tool as an instance that can be directly used
glob_tool = GlobTool()