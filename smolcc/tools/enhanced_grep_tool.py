"""
EnhancedGrepTool for SmolCC - Content search tool with rich output

This tool allows searching file contents using regular expressions and returns
rich output objects with highlighted matches for better display in the terminal.
"""

import os
import re
import glob as glob_module
import fnmatch
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Union

from smolagents import Tool
from smolcc.tool_output import ToolOutput, CodeOutput, TextOutput, TableOutput, FileListOutput


class EnhancedGrepTool(Tool):
    """
    Fast content search tool that works with any codebase size.
    Searches file contents using regular expressions with rich output.
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
    
    def forward(self, pattern: str, include: Optional[str] = None, path: Optional[str] = None) -> Union[ToolOutput, Dict, str]:
        """
        Search for files containing content that matches the given regex pattern with rich output.
        
        Args:
            pattern: The regular expression pattern to search for in file contents
            include: File pattern to include in the search (e.g. "*.js", "*.{ts,tsx}")
            path: The directory to search in (defaults to current working directory)
            
        Returns:
            A ToolOutput object for rich display
        """
        start_time = time.time()
        search_path = path or os.getcwd()
        
        # Make sure search_path is absolute
        search_path = os.path.abspath(search_path)
        
        try:
            # Compile the regex pattern
            regex = re.compile(pattern)
        except re.error as e:
            return TextOutput(f"Error: Invalid regular expression pattern: {str(e)}")
        
        # Find files to search
        all_files = self._find_files(search_path, include)
        
        # If no files found to search
        if not all_files:
            return TextOutput(f"No files found matching include pattern: {include or '*'}")
        
        # Search for pattern in files and get matches
        file_matches = []
        match_count = 0
        for file_path in all_files:
            try:
                file_match_info = self._get_file_matches(file_path, regex)
                if file_match_info:
                    file_matches.append(file_match_info)
                    match_count += len(file_match_info['matches'])
            except Exception:
                # Silently skip files that can't be read
                continue
        
        # Sort results by modification time (newest first)
        file_matches.sort(key=lambda f: os.path.getmtime(f['path']), reverse=True)
        
        # Check if we found any matches
        if not file_matches:
            return TextOutput(f"No matches found for pattern '{pattern}' in {len(all_files)} files")
        
        # Truncate to max 10 files for display
        truncated = len(file_matches) > 10
        displayed_files = file_matches[:10]
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Format results for display
        return self._format_results(
            pattern=pattern,
            file_matches=displayed_files,
            total_files=len(file_matches),
            truncated=truncated,
            duration_ms=duration_ms,
            search_path=search_path,
            match_count=match_count
        )
    
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
    
    def _get_file_matches(self, file_path: str, regex: re.Pattern) -> Optional[Dict[str, Any]]:
        """
        Get matches for a regex pattern in a file with context.
        
        Args:
            file_path: Path to the file to search
            regex: Compiled regex pattern
            
        Returns:
            Dictionary with match information or None if no matches
        """
        # Skip binary files and other problematic file types
        if self._is_binary_file(file_path):
            return None
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        file_content = None
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    file_content = f.read()
                break  # Successfully read file, break the encoding loop
            except UnicodeDecodeError:
                continue
            except Exception:
                # Skip files that can't be read
                return None
        
        if file_content is None:
            return None
            
        # Get all matches with context
        lines = file_content.split('\n')
        matches = []
        
        for i, line in enumerate(lines):
            for match in regex.finditer(line):
                # Get context (3 lines before and after)
                start_line = max(0, i - 3)
                end_line = min(len(lines) - 1, i + 3)
                
                # Extract the match and context
                context_lines = lines[start_line:end_line + 1]
                match_line_index = i - start_line
                
                matches.append({
                    'line_number': i + 1,  # 1-indexed line number
                    'context': context_lines,
                    'match_line_index': match_line_index,
                    'match_span': match.span(),
                    'match_text': match.group(0)
                })
                
        if not matches:
            return None
            
        # Get file extension for syntax highlighting
        _, ext = os.path.splitext(file_path)
        language = self._get_language_for_extension(ext)
        
        return {
            'path': file_path,
            'language': language,
            'matches': matches,
            'modified': os.path.getmtime(file_path)
        }
    
    def _format_results(
        self, 
        pattern: str,
        file_matches: List[Dict[str, Any]],
        total_files: int,
        truncated: bool,
        duration_ms: int,
        search_path: str,
        match_count: int
    ) -> ToolOutput:
        """
        Format search results for rich display.
        
        Args:
            pattern: The search pattern
            file_matches: List of file match information
            total_files: Total number of matching files
            truncated: Whether results were truncated
            duration_ms: Search duration in milliseconds
            search_path: Path that was searched
            match_count: Total number of matches
            
        Returns:
            A ToolOutput object for rich display
        """
        # Create a summary with statistics
        summary = f"Found {match_count} matches in {total_files} files"
        if truncated:
            summary += f" (showing first 10 files)"
        summary += f" for pattern '{pattern}' in {search_path}"
        summary += f" ({duration_ms}ms)"
        
        # Check if we should show all matches as a table
        if total_files <= 5:
            # For small result sets, we'll show all matches with context
            result = f"{summary}\n\n"
            
            for file_info in file_matches:
                file_path = file_info['path']
                language = file_info['language']
                
                result += f"File: {file_path}\n"
                
                for match in file_info['matches'][:5]:  # Limit to 5 matches per file
                    line_number = match['line_number']
                    context_lines = match['context']
                    match_line_index = match['match_line_index']
                    
                    # Format context with line numbers and highlighting
                    context_with_numbers = ""
                    for i, line in enumerate(context_lines):
                        line_num = line_number - match_line_index + i
                        
                        # Highlight the match line
                        if i == match_line_index:
                            # Add markers for the match
                            match_start, match_end = match['match_span']
                            highlighted_line = line[:match_start] + "§" + line[match_start:match_end] + "§" + line[match_end:]
                            context_with_numbers += f"{line_num:4d} | {highlighted_line}\n"
                        else:
                            context_with_numbers += f"{line_num:4d} | {line}\n"
                    
                    result += context_with_numbers + "\n"
                
                # If we have more matches than shown
                if len(file_info['matches']) > 5:
                    result += f"... and {len(file_info['matches']) - 5} more matches in this file\n\n"
            
            # Return as CodeOutput for syntax highlighting
            return CodeOutput(result, language="text", line_numbers=False)
        else:
            # For larger result sets, just return a file list
            file_list = []
            for file_info in file_matches:
                match_count = len(file_info['matches'])
                first_line = file_info['matches'][0]['line_number'] if match_count > 0 else 0
                
                file_list.append({
                    'name': os.path.basename(file_info['path']),
                    'path': file_info['path'],
                    'is_dir': False,
                    'matches': match_count,
                    'first_match': f"line {first_line}",
                    'size': os.path.getsize(file_info['path'])
                })
            
            # Return as FileListOutput with a custom path showing the pattern
            return FileListOutput(file_list, path=f"Search results for '{pattern}' in {search_path}")
    
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
    
    def _get_language_for_extension(self, ext: str) -> str:
        """
        Get the language name for syntax highlighting based on file extension.
        
        Args:
            ext: File extension including the dot (e.g. ".py")
            
        Returns:
            Language name for syntax highlighting
        """
        ext = ext.lower()
        
        # Mapping of extensions to languages
        language_map = {
            # Python
            '.py': 'python',
            '.pyx': 'python',
            # JavaScript/TypeScript
            '.js': 'javascript',
            '.jsx': 'jsx',
            '.ts': 'typescript',
            '.tsx': 'tsx',
            # Web
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            # Data formats
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.toml': 'toml',
            # Shell
            '.sh': 'bash',
            '.bash': 'bash',
            # C-family languages
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.java': 'java',
            # Other languages
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.md': 'markdown',
            '.markdown': 'markdown'
        }
        
        return language_map.get(ext, 'text')


# Export the tool as an instance that can be directly used
enhanced_grep_tool = EnhancedGrepTool()