#!/usr/bin/env python3
"""
Unit tests for the View tool.

These tests verify that the View tool continues to produce the expected output
for standard inputs, effectively "locking in" the current behavior.
"""

import os
import json
import unittest
import re
from typing import Dict, Any, List

from smolcc.tools.view_tool import view_tool

# Constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(TEST_DIR, "testdata")

# Test cases with expected content to find in the view results
TEST_CASES = {
    "view_test_file": {
        "inputs": {
            "file_path": os.path.join(TEST_DATA_DIR, "test_file1.txt")
        },
        "expected_lines": [
            "This is a test file for testing the View tool.",
            "It contains multiple lines of text.",
            "Line 3 contains some content.",
            "Line 4 contains more content.",
            "Line 5 contains the final line of content."
        ]
    },
    "view_json_file": {
        "inputs": {
            "file_path": os.path.join(TEST_DATA_DIR, "test_config.json")
        },
        "expected_patterns": [
            "test-config",
            "version",
            "database",
            "host",
            "features"
        ]
    },
    "view_large_file_with_limits": {
        "inputs": {
            "file_path": os.path.join(TEST_DATA_DIR, "large_file.txt"),
            "offset": 20,
            "limit": 30
        },
        "expected_line_count": 30,
        "start_line": "Line 21 of the large file.",
        "end_line": "Line 50 of the large file."
    }
}


class ViewToolTests(unittest.TestCase):
    """Tests for the View tool."""

    def test_view_test_file(self):
        """Test viewing a simple text file."""
        test_data = TEST_CASES["view_test_file"]
        result = view_tool.forward(**test_data["inputs"])
        
        # Check that the output contains line numbers and content
        for line in test_data["expected_lines"]:
            self.assertIn(line, result)
            
        # Check for line numbers in the format "     1\t..."
        for i, _ in enumerate(test_data["expected_lines"], 1):
            line_number_pattern = f"{i:6d}"
            self.assertIn(line_number_pattern, result)

    def test_view_json_file(self):
        """Test viewing a JSON file."""
        test_data = TEST_CASES["view_json_file"]
        result = view_tool.forward(**test_data["inputs"])
        
        # Check for expected patterns in the JSON output
        for pattern in test_data["expected_patterns"]:
            self.assertIn(pattern, result)
            
        # The output should have line numbers
        self.assertRegex(result, r"^\s+\d+\t")

    def test_view_large_file_with_limits(self):
        """Test viewing a large file with offset and limit parameters."""
        test_data = TEST_CASES["view_large_file_with_limits"]
        result = view_tool.forward(**test_data["inputs"])
        
        # Count the number of lines in the result
        lines = result.strip().split('\n')
        
        # Check that we got the right number of lines
        self.assertEqual(len(lines), test_data["expected_line_count"], 
                        f"Expected {test_data['expected_line_count']} lines, got {len(lines)}")
        
        # Check the line content - adjust for line numbers in output
        self.assertTrue("Line 20" in lines[0] or "Line 21" in lines[0], 
                       f"First line doesn't contain correct line number: {lines[0]}")
        self.assertTrue("Line 49" in lines[-1] or "Line 50" in lines[-1], 
                       f"Last line doesn't contain correct line number: {lines[-1]}")
        
        # Check for line numbers in a more flexible way
        if re.search(r'\d+\t', lines[0]):
            line_number = re.search(r'(\d+)\t', lines[0]).group(1)
            line_number = int(line_number)
            
            # Check that line number is in the expected range
            expected_min = test_data["inputs"]["offset"]
            expected_max = test_data["inputs"]["offset"] + 1
            self.assertTrue(expected_min <= line_number <= expected_max,
                           f"Line number {line_number} outside expected range {expected_min}-{expected_max}")


if __name__ == "__main__":
    unittest.main()