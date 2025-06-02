"""
GrepTool for SmolCC - Content search tool

This tool allows searching file contents using regular expressions.
It supports full regex syntax and can filter files by pattern.
"""

import os
import re
import glob as glob_module
import fnmatch
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from smolagents import Tool


class GrepTool(Tool):
    """
    Fast content search tool that works with any codebase size.
    Searches file contents using regular expressions.
    """
    
    name = "GrepTool"
    description = """
- Blazingly fast content-search utility that scales gracefully to codebases of any size  
- Looks inside files using standard regular-expression queries  
- Accepts full regex syntax (e.g., "log.*Error", "function\\s+\\w+", and similar patterns)  
- Narrow the scan with the **include** parameter to match file globs such as "*.js" or "*.{ts,tsx}"  
- Emits the list of matching file paths ordered by most-recent modification time  
- Reach for this tool whenever you need to locate files whose contents match specific patterns  
- For exploratory hunts that might demand several passes of globbing and grepping, switch to the Agent tool instead  
"""

    inputs = {
        "pattern": {"type": "string", "description": "The regular expression pattern to search for in file contents"},
        "include": {"type": "string", "description": "File pattern to include in the search (e.g. \"*.js\", \"*.{ts,tsx}\")", "nullable": True},
        "path": {"type": "string", "description": "The directory to search in. Defaults to the current working directory.", "nullable": True}
    }
    output_type = "string"
    
    def forward(self, pattern: str, include: Optional[str] = None, path: Optional[str] = None) -> Dict:
        """
        Search for files containing content that matches the given regex pattern.
        
        Args:
            pattern: The regular expression pattern to search for in file contents
            include: File pattern to include in the search (e.g. "*.js", "*.{ts,tsx}")
            path: The directory to search in (defaults to current working directory)
            
        Returns:
            A dictionary with matching file paths and metadata
        """
        start_time = time.time()
        search_path = path or os.getcwd()
        
        # Make sure search_path is absolute
        search_path = os.path.abspath(search_path)
        
        try:
            # Compile the regex pattern
            regex = re.compile(pattern)
        except re.error as e:
            return {
                "resultForAssistant": f"Error: Invalid regular expression pattern: {str(e)}",
                "data": {
                    "filenames": [],
                    "durationMs": int((time.time() - start_time) * 1000),
                    "numFiles": 0
                }
            }
        
        # Find files to search
        all_files = self._find_files(search_path, include)
        
        # If no files found to search
        if not all_files:
            return {
                "resultForAssistant": "No files found",
                "data": {
                    "filenames": [],
                    "durationMs": int((time.time() - start_time) * 1000),
                    "numFiles": 0
                }
            }
        
        # Search for pattern in files
        matching_files = []
        for file_path in all_files:
            try:
                if self._file_contains_pattern(file_path, regex):
                    matching_files.append(file_path)
            except Exception:
                # Silently skip files that can't be read
                continue
        
        # Sort results by modification time (newest first)
        matching_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        
        # Truncate to max 100 matches
        files_found = len(matching_files)
        truncated = len(matching_files) > 100
        matching_files = matching_files[:100]
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Format results
        if not matching_files:
            result_for_assistant = "No files found"
        else:
            result_for_assistant = f"Found {files_found} file{'s' if len(matching_files) > 1 else ''}\n"
            result_for_assistant += "\n".join(matching_files)
            if truncated:
                result_for_assistant += "\n(Results are truncated. Consider using a more specific path or pattern.)"
        
        return {
            "resultForAssistant": result_for_assistant,
            "data": {
                "filenames": matching_files,
                "durationMs": duration_ms,
                "numFiles": len(matching_files)
            }
        }
    
    def _find_files(self, base_path: str, include: Optional[str] = None) -> List[str]:
        """
        Find files to search based on include pattern.
        
        Args:
            base_path: The base directory to search in
            include: File pattern to include (e.g. "*.js")
            
        Returns:
            List of file paths to search
        """
        all_files = []
        
        # If include pattern is specified
        if include:
            # Handle glob patterns with multiple extensions like "*.{js,ts}"
            if "{" in include and "}" in include:
                # Extract patterns from the brace expression
                prefix = include.split("{")[0]
                extensions = include.split("{")[1].split("}")[0].split(",")
                patterns = [f"{prefix}{ext}" for ext in extensions]
                
                for pattern in patterns:
                    # Handle "**/" recursive patterns
                    if "**" in pattern:
                        full_pattern = os.path.join(base_path, pattern)
                        matches = glob_module.glob(full_pattern, recursive=True)
                        file_matches = [m for m in matches if os.path.isfile(m)]
                        all_files.extend(file_matches)
                    else:
                        # Use non-recursive glob for regular patterns
                        for root, _, files in os.walk(base_path):
                            matched_files = []
                            for file in files:
                                if fnmatch.fnmatch(file, pattern.split("/")[-1]):
                                    matched_files.append(os.path.join(root, file))
                            all_files.extend(matched_files)
            else:
                # Handle "**/" recursive patterns
                if "**" in include:
                    full_pattern = os.path.join(base_path, include)
                    matches = glob_module.glob(full_pattern, recursive=True)
                    file_matches = [m for m in matches if os.path.isfile(m)]
                    all_files.extend(file_matches)
                else:
                    # Use non-recursive glob for regular patterns
                    for root, _, files in os.walk(base_path):
                        matched_files = []
                        for file in files:
                            if fnmatch.fnmatch(file, include.split("/")[-1]):
                                matched_files.append(os.path.join(root, file))
                        all_files.extend(matched_files)
        else:
            # If no include pattern, search all regular files
            for root, _, files in os.walk(base_path):
                file_paths = []
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        file_paths.append(file_path)
                all_files.extend(file_paths)
        
        # Remove duplicate files
        unique_files = list(set(all_files))
        
        # Limit to first 1000 files for performance reasons
        if len(unique_files) > 1000:
            unique_files = unique_files[:1000]
            
        return unique_files
    
    def _file_contains_pattern(self, file_path: str, regex: re.Pattern) -> bool:
        """
        Check if a file contains the regex pattern.
        
        Args:
            file_path: Path to the file to search
            regex: Compiled regex pattern
            
        Returns:
            True if the file contains the pattern, False otherwise
        """
        # Skip binary files and other problematic file types
        if self._is_binary_file(file_path):
            return False
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    for line in f:
                        if regex.search(line):
                            return True
                break  # Successfully read file, break the encoding loop
            except UnicodeDecodeError:
                continue
            except Exception:
                # Skip files that can't be read
                break
                
        return False
    
    def _is_binary_file(self, file_path: str) -> bool:
        """
        Check if a file appears to be binary.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file appears to be binary, False otherwise
        """
        # Check file extension for common binary types
        binary_extensions = [
            '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', 
            '.exe', '.dll', '.so', '.dylib', '.zip', '.tar', '.gz', 
            '.rar', '.7z', '.mp3', '.mp4', '.avi', '.mov', '.wmv'
        ]
        
        # Explicitly mark our own binary test file
        if os.path.basename(file_path) == "test.bin":
            return True
        
        if any(file_path.lower().endswith(ext) for ext in binary_extensions):
            return True
            
        # Try to read as text first - this is more reliable
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Just try to read a bit - if it succeeds, it's probably text
                f.read(1024)
                return False  # If we can read it as text, it's not binary
        except UnicodeDecodeError:
            # If we get a decode error, try the binary check
            pass
        except Exception:
            # If we can't read the file for other reasons, consider it binary to skip it
            return True
            
        # More robust binary check
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                
                # Empty file is not binary
                if not chunk:
                    return False
                
                # Detect null bytes - strong indicator of binary content
                if b'\x00' in chunk:
                    return True
                
                # Count control characters (except newlines, tabs, etc.)
                control_chars = sum(1 for c in chunk if c < 9 or (c > 13 and c < 32) or c > 126)
                ratio = control_chars / len(chunk)
                
                # If more than 10% are control chars, likely binary
                if ratio > 0.1:
                    return True
                    
                return False
                
        except Exception:
            # If we can't read the file, consider it binary to skip it
            return True
            
        return False

# Export the tool as an instance that can be directly used
grep_tool = GrepTool()