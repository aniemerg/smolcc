#!/usr/bin/env python3
"""
Unit tests for the LS tool.

These tests verify that the LS tool continues to produce the expected output
for standard inputs, effectively "locking in" the current behavior.
"""

import os
import unittest
import re
from typing import Dict, Any, List

from smolcc.tools.ls_tool import ls_tool

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

    def _verify_ls_results(self, result: str, expected_files: List[str], 
                          should_not_contain: List[str] = None) -> None:
        """
        Verify that the LS result contains the expected files and directories.
        
        Args:
            result: The result string from the LS tool
            expected_files: List of expected filenames or directory names
            should_not_contain: List of files that should not be in the result
        """
        # Get the content from the result
        content = result
        
        # Check that each expected file is in the content
        for expected_file in expected_files:
            self.assertIn(
                os.path.basename(expected_file), 
                content,
                f"Expected file/dir '{expected_file}' not found in LS output"
            )
        
        # Check that none of the excluded files are in the content
        if should_not_contain:
            for excluded_file in should_not_contain:
                self.assertNotIn(
                    os.path.basename(excluded_file),
                    content,
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