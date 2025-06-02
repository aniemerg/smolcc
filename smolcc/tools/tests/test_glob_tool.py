#!/usr/bin/env python3
"""
Unit tests for the GlobTool.

These tests verify that the GlobTool continues to produce the expected output
for standard inputs, effectively "locking in" the current behavior.
"""

import os
import unittest
import re
from typing import Dict, Any, List

from smolcc.tools.glob_tool import glob_tool

# Constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(TEST_DIR, "testdata")

# Expected file patterns to be found (we use partial matching to handle path differences)
EXPECTED_PATTERNS = {
    "find_text_files": {
        "inputs": {
            "pattern": "*.txt",
            "path": TEST_DATA_DIR
        },
        "expected_files": [
            "test_file1.txt",
            "large_file.txt"
        ]
    },
    "find_all_recursively": {
        "inputs": {
            "pattern": "**/*.*",
            "path": TEST_DATA_DIR
        },
        "expected_files": [
            "test_file1.txt",
            "large_file.txt",
            "test_config.json",
            "test_file2.py",
            "test_js_file.js",
            "test_typescript_file.ts",
            "subfolder1/test_file3.txt",
            "subfolder1/test_component.jsx",
            "subfolder1/subfolder2/test_config.yml"
        ]
    },
    "find_config_files": {
        "inputs": {
            "pattern": "**/*config*.*",
            "path": TEST_DATA_DIR
        },
        "expected_files": [
            "test_config.json",
            "subfolder1/subfolder2/test_config.yml"
        ]
    }
}


class GlobToolTests(unittest.TestCase):
    """Tests for the GlobTool."""

    def _verify_glob_results(self, result: str, expected_files: List[str]) -> None:
        """
        Verify that the glob result contains the expected files.
        
        Args:
            result: The result string from the glob tool
            expected_files: List of expected filenames (without full paths)
        """
        # Split the result into lines
        found_files = result.strip().split('\n')
        
        # Check if we got any results
        if not found_files[0]:
            found_files = []
            
        # Verify we found the right number of files
        self.assertEqual(
            len(found_files), 
            len(expected_files), 
            f"Expected {len(expected_files)} files, but found {len(found_files)}"
        )
        
        # Check that each expected file is in the results
        for expected_file in expected_files:
            found = False
            for file_path in found_files:
                if os.path.basename(file_path) == expected_file or expected_file in file_path:
                    found = True
                    break
                    
            self.assertTrue(
                found, 
                f"File '{expected_file}' was not found in glob results"
            )

    def test_find_text_files(self):
        """Test finding text files with a simple pattern."""
        test_data = EXPECTED_PATTERNS["find_text_files"]
        result = glob_tool.forward(**test_data["inputs"])
        self._verify_glob_results(result, test_data["expected_files"])

    def test_find_all_recursively(self):
        """Test finding all files recursively."""
        test_data = EXPECTED_PATTERNS["find_all_recursively"]
        result = glob_tool.forward(**test_data["inputs"])
        self._verify_glob_results(result, test_data["expected_files"])

    def test_find_config_files(self):
        """Test finding config files with a complex pattern."""
        test_data = EXPECTED_PATTERNS["find_config_files"]
        result = glob_tool.forward(**test_data["inputs"])
        self._verify_glob_results(result, test_data["expected_files"])


if __name__ == "__main__":
    unittest.main()