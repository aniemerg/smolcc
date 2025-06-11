#!/usr/bin/env python3
"""
Unit tests for the LS tool.

These tests verify that the LS tool continues to produce the expected output
for standard inputs, effectively "locking in" the current behavior.
"""

import os
import unittest
import re
from typing import Dict, Any, List, Union

from smolcc.tools.ls_tool import ls_tool
from smolcc.tool_output import ToolOutput, FileListOutput

# Constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(TEST_DIR, "testdata")

# Test cases with expected files and directories
TEST_CASES = {
    "list_test_directory": {
        "inputs": {
            "path": TEST_DATA_DIR
        },
        "expected_files": [
            "large_file.txt",
            "subfolder1/",
            "test_config.json",
            "test_file1.txt",
            "test_file2.py",
            "test_js_file.js",
            "test_typescript_file.ts"
        ]
    },
    "list_with_ignore": {
        "inputs": {
            "path": TEST_DATA_DIR,
            "ignore": ["**/*.json", "**/*.yml"]
        },
        "expected_files": [
            "large_file.txt",
            "subfolder1/",
            "test_file1.txt",
            "test_file2.py",
            "test_js_file.js",
            "test_typescript_file.ts"
        ],
        "should_not_contain": [
            "test_config.json",
            "test_config.yml"
        ]
    },
    "list_subfolder": {
        "inputs": {
            "path": os.path.join(TEST_DATA_DIR, "subfolder1")
        },
        "expected_files": [
            "subfolder2/",
            "test_component.jsx",
            "test_file3.txt"
        ]
    }
}


class LSToolTests(unittest.TestCase):
    """Tests for the LS tool."""

    def _verify_ls_results(self, result: Union[ToolOutput, str], expected_files: List[str], 
                          should_not_contain: List[str] = None) -> None:
        """
        Verify that the LS result contains the expected files and directories.
        
        Args:
            result: The result from the LS tool
            expected_files: List of expected filenames or directory names
            should_not_contain: List of files that should not be in the result
        """
        self.assertIsInstance(result, ToolOutput)
        
        # Get file names from the result
        if isinstance(result, FileListOutput):
            # Extract file names and information from the FileListOutput
            file_entries = result.data
            file_names = [file.get('name', '') for file in file_entries]
            is_dirs = [file.get('is_dir', False) for file in file_entries]
            
            # Create a combined list of files with trailing slashes for directories
            formatted_names = []
            for i, name in enumerate(file_names):
                if is_dirs[i]:
                    formatted_names.append(f"{name}/")
                else:
                    formatted_names.append(name)
                    
            content = '\n'.join(formatted_names)  # Join for string contains checks
        else:
            # Fallback to string representation
            content = str(result)
            file_names = content.strip().split('\n')
            formatted_names = file_names
        
        # Now we have formatted names with correct directory indicators
        
        # Check that each expected file is in the content
        for expected_file in expected_files:
            expected_basename = os.path.basename(expected_file.rstrip('/'))
            expected_is_dir = expected_file.endswith('/')
            
            found = False
            
            # Check if the file exists in the formatted names
            if expected_file in formatted_names:
                found = True
            # Check if it exists in the base names list
            elif expected_basename in file_names:
                found = True
            # For directories, check without trailing slash
            elif expected_is_dir and any(name == expected_basename for name in file_names):
                found = True
            # Check if the directory is correctly identified in FileListOutput
            elif expected_is_dir and isinstance(result, FileListOutput):
                for i, name in enumerate(file_names):
                    if name == expected_basename and is_dirs[i]:
                        found = True
                        break
            # Fallback to content search
            elif expected_basename in content:
                found = True
                
            self.assertTrue(
                found,
                f"Expected file/dir '{expected_file}' not found in LS output. Found: {formatted_names}"
            )
        
        # Check that none of the excluded files are in the content
        if should_not_contain:
            for excluded_file in should_not_contain:
                excluded_basename = os.path.basename(excluded_file.rstrip('/'))
                excluded_is_dir = excluded_file.endswith('/')
                
                found = False
                
                # Check if the file exists in the formatted names
                if excluded_file in formatted_names:
                    found = True
                # Check if it exists in the base names list
                elif excluded_basename in file_names:
                    found = True
                # For directories, check without trailing slash
                elif excluded_is_dir and any(name == excluded_basename for name in file_names):
                    found = True
                # Check if the directory is correctly identified in FileListOutput
                elif excluded_is_dir and isinstance(result, FileListOutput):
                    for i, name in enumerate(file_names):
                        if name == excluded_basename and is_dirs[i]:
                            found = True
                            break
                            
                self.assertFalse(
                    found,
                    f"Excluded file '{excluded_file}' was found in LS output"
                )

    def test_list_test_directory(self):
        """Test listing the test directory."""
        test_data = TEST_CASES["list_test_directory"]
        result = ls_tool.forward(**test_data["inputs"])
        self._verify_ls_results(result, test_data["expected_files"])

    def test_list_with_ignore(self):
        """Test listing with ignore patterns."""
        test_data = TEST_CASES["list_with_ignore"]
        result = ls_tool.forward(**test_data["inputs"])
        self._verify_ls_results(
            result, 
            test_data["expected_files"], 
            test_data.get("should_not_contain")
        )

    def test_list_subfolder(self):
        """Test listing a subfolder."""
        test_data = TEST_CASES["list_subfolder"]
        result = ls_tool.forward(**test_data["inputs"])
        self._verify_ls_results(result, test_data["expected_files"])


if __name__ == "__main__":
    unittest.main()