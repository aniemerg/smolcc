#!/usr/bin/env python3
"""
Unit tests for the Bash tool.

These tests verify that the Bash tool continues to produce the expected output
for standard inputs, effectively "locking in" the current behavior.
"""

import os
import unittest
import json
from typing import Dict, Any

from smolcc.tools.bash_tool import bash_tool
from smolcc.tool_output import ToolOutput, TextOutput

# Constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(TEST_DIR, "testdata")
EXPECTED_OUTPUTS = {
    "simple_command": {
        "inputs": {
            "command": "echo 'Hello, world!'",
            "timeout": 5000
        },
        "expected": "Hello, world\\!"
    },
    "environment_variables": {
        "inputs": {
            "command": "export TEST_VAR='hello world' && echo $TEST_VAR",
            "timeout": 5000
        },
        "expected": "hello world"
    },
    "complex_command_pipeline": {
        "inputs": {
            "command": f"find {TEST_DATA_DIR} -type f -name '*.json' | wc -l",
            "timeout": 10000
        },
        "expected": "       1"
    },
    "directory_listing_with_details": {
        "inputs": {
            "command": f"ls -la {TEST_DATA_DIR} | head -n 20",
            "timeout": 5000
        },
        "expected": """total 56
drwxr-xr-x  9 allanniemerg  staff   288 Jun  2 13:19 .
drwxr-xr-x  3 allanniemerg  staff    96 Jun  2 13:24 ..
-rw-r--r--  1 allanniemerg  staff  5200 Jun  2 13:19 large_file.txt
-rw-r--r--  1 allanniemerg  staff   478 Jun  2 12:59 test_config.json
-rw-r--r--  1 allanniemerg  staff   271 Jun  2 12:59 test_file1.txt
-rw-r--r--  1 allanniemerg  staff   658 Jun  2 12:59 test_file2.py
-rw-r--r--  1 allanniemerg  staff  1226 Jun  2 12:59 test_js_file.js
drwxr-xr-x  4 allanniemerg  staff   128 Jun  2 13:00 subfolder1
-rw-r--r--  1 allanniemerg  staff  1460 Jun  2 12:59 test_typescript_file.ts"""
    }
}


class BashToolTests(unittest.TestCase):
    """Tests for the Bash tool."""

    def test_simple_command(self):
        """Test a simple echo command."""
        test_data = EXPECTED_OUTPUTS["simple_command"]
        result = bash_tool.forward(**test_data["inputs"])
        self.assertIsInstance(result, ToolOutput)
        self.assertEqual(str(result), test_data["expected"])

    def test_environment_variables(self):
        """Test environment variable persistence."""
        test_data = EXPECTED_OUTPUTS["environment_variables"]
        result = bash_tool.forward(**test_data["inputs"])
        self.assertIsInstance(result, ToolOutput)
        self.assertEqual(str(result), test_data["expected"])

    def test_complex_command_pipeline(self):
        """Test a more complex command with piping."""
        test_data = EXPECTED_OUTPUTS["complex_command_pipeline"]
        result = bash_tool.forward(**test_data["inputs"])
        self.assertIsInstance(result, ToolOutput)
        self.assertEqual(str(result), test_data["expected"])

    def test_directory_listing_with_details(self):
        """Test listing a directory with details."""
        test_data = EXPECTED_OUTPUTS["directory_listing_with_details"]
        result = bash_tool.forward(**test_data["inputs"])
        self.assertIsInstance(result, ToolOutput)
        
        # Instead of comparing specific lines which may vary, check for expected files
        all_actual_lines = str(result).strip().split('\n')
        
        # These should be unique files from the test data directory
        expected_files = ["test_file1.txt", "test_file2.py", "test_js_file.js", "test_typescript_file.ts", "test_config.json"]
        for file in expected_files:
            found = any(file in line for line in all_actual_lines)
            self.assertTrue(found, f"File '{file}' not found in directory listing results")


if __name__ == "__main__":
    unittest.main()