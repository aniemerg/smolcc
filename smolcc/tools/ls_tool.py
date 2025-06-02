"""
LSTool for SmolCC - Directory listing tool

This tool lists files and directories in a given path.
"""

import os
import fnmatch
from typing import List, Dict, Any, Optional, Set, Tuple

from smolagents import Tool

# Constants
MAX_FILES = 1000
TRUNCATED_MESSAGE = f"There are more than {MAX_FILES} files in the repository. Use the LS tool (passing a specific path), Bash tool, and other tools to explore nested directories. The first {MAX_FILES} files and directories are included below:\n\n"


class LSTool(Tool):
    """
    Lists files and directories in a given path with a tree-like structure.
    """
    
    name = "LS"
    description = "Displays a directory’s contents—files and sub-directories—at the location specified by **path**. The **path** argument must be an absolute path (it cannot be relative). You may optionally supply an **ignore** parameter: an array of glob patterns that should be skipped. If you already know the directories you want to scan, the Glob and Grep tools are generally the better choice."
    inputs = {
        "path": {"type": "string", "description": "The absolute path to the directory to list (must be absolute, not relative)"},
        "ignore": {"type": "array", "description": "List of glob patterns to ignore", "items": {"type": "string"}, "nullable": True}
    }
    output_type = "string"
    
    def forward(self, path: str, ignore: Optional[List[str]] = None) -> str:
        """
        List files and directories in the given path.
        
        Args:
            path: The absolute path to the directory to list
            ignore: Optional list of glob patterns to ignore
            
        Returns:
            A tree-like representation of the directory contents
        """
        # Ensure path is absolute
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        # Check if path exists and is a directory
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        if not os.path.isdir(path):
            return f"Error: Path '{path}' is not a directory"
        
        # Get the list of all paths in the directory
        all_paths = self._list_directory(path, ignore or [])
        
        # Build tree structure from the paths
        tree = self._create_file_tree(all_paths)
        
        # Format the tree as a string
        truncated = len(all_paths) >= MAX_FILES
        prefix = TRUNCATED_MESSAGE if truncated else ""
        tree_output = self._print_tree(tree, path)
        
        # Return result with safety warning
        result = f"{prefix}{tree_output}"
        return result 
        
    def _list_directory(self, initial_path: str, ignore_patterns: List[str]) -> List[str]:
        """
        Lists all files and directories using breadth-first traversal.
        
        Args:
            initial_path: The starting directory path
            ignore_patterns: List of glob patterns to ignore
            
        Returns:
            List of relative paths (directories ending with /)
        """
        results = []
        queue = [initial_path]
        file_count = 0
        
        while queue and file_count < MAX_FILES:
            path = queue.pop(0)  # Dequeue from left (FIFO)
            
            # Skip if this path should be filtered
            if self._should_skip(path, ignore_patterns):
                continue
                
            # Add this path to results (except the initial path)
            if path != initial_path:
                # Get relative path and normalize separators
                rel_path = os.path.relpath(path, initial_path).replace(os.path.sep, '/')
                # Ensure directories end with /
                if os.path.isdir(path):
                    if not rel_path.endswith('/'):
                        rel_path += '/'
                    results.append(rel_path)
                else:
                    results.append(rel_path)
                    file_count += 1
            
            # If it's a directory, add its children to the queue
            if os.path.isdir(path):
                try:
                    # Get all entries in the directory
                    entries = []
                    for item in os.listdir(path):
                        item_path = os.path.join(path, item)
                        entries.append(item_path)
                    
                    # Sort entries alphabetically
                    entries.sort()
                    
                    # Add entries to queue
                    for item_path in entries:
                        if not self._should_skip(item_path, ignore_patterns):
                            queue.append(item_path)
                except (PermissionError, FileNotFoundError):
                    continue
        
        # Sort results alphabetically
        results.sort()
        return results
        
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
    
    def _create_file_tree(self, sorted_paths: List[str]) -> List[Dict]:
        """
        Converts a flat list of paths into a tree structure.
        
        Args:
            sorted_paths: Alphabetically sorted list of relative paths
            
        Returns:
            List of tree nodes representing the directory structure
        """
        root = []
        
        for path in sorted_paths:
            parts = path.split('/')
            current_level = root
            current_path = ''
            
            for i, part in enumerate(parts):
                if not part:  # Skip empty parts from trailing slashes
                    continue
                    
                current_path = f"{current_path}/{part}" if current_path else part
                is_directory = i < len(parts) - 1 or path.endswith('/')
                
                # Check if this node already exists
                existing_node = None
                for node in current_level:
                    if node['name'] == part:
                        existing_node = node
                        break
                        
                if existing_node:
                    # Move to existing node's children
                    current_level = existing_node.get('children', [])
                else:
                    # Create new node
                    new_node = {
                        'name': part,
                        'path': current_path,
                        'type': 'directory' if is_directory else 'file'
                    }
                    
                    if is_directory:
                        new_node['children'] = []
                        
                    current_level.append(new_node)
                    current_level = new_node.get('children', [])
        
        return root
    
    def _print_tree(self, tree: List[Dict], root_path: str, level: int = 0, prefix: str = '') -> str:
        """
        Formats a tree structure into a string representation.
        
        Args:
            tree: The tree structure to print
            root_path: The absolute path to the root directory
            level: Current indentation level
            prefix: Prefix string for indentation
            
        Returns:
            Formatted string representation of the tree
        """
        result = ""
        
        # Add absolute path at root level
        if level == 0:
            # Ensure root path ends with / for consistency
            root_path = root_path.rstrip(os.path.sep) + '/'
            result += f"- {root_path}\n"
            prefix = "  "
        
        for node in tree:
            # Add the current node with proper formatting
            node_suffix = "/" if node['type'] == 'directory' else ""
            result += f"{prefix}- {node['name']}{node_suffix}\n"
            
            # Process children recursively if this is a directory
            if node.get('children'):
                result += self._print_tree(
                    node['children'],
                    root_path,
                    level + 1,
                    prefix + "  "
                )
        
        return result


# Export the tool as an instance that can be directly used
ls_tool = LSTool()