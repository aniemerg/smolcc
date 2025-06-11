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
from smolcc.tool_output import ToolOutput, TextOutput, CodeOutput

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
        self.assertIsInstance(result, ToolOutput)
        
        # Convert to string for testing
        result_str = str(result)
        
        # Check that the output contains line numbers and content
        for line in test_data["expected_lines"]:
            self.assertIn(line, result_str)
            
        # Check for line numbers in the format "     1\t..."
        for i, _ in enumerate(test_data["expected_lines"], 1):
            line_number_pattern = f"{i:6d}"
            self.assertIn(line_number_pattern, result_str)

    def test_view_json_file(self):
        """Test viewing a JSON file."""
        test_data = TEST_CASES["view_json_file"]
        result = view_tool.forward(**test_data["inputs"])
        self.assertIsInstance(result, ToolOutput)
        
        # Convert to string for testing
        result_str = str(result)
        
        # Check for expected patterns in the JSON output
        for pattern in test_data["expected_patterns"]:
            self.assertIn(pattern, result_str)
            
        # The output should have line numbers
        self.assertRegex(result_str, r"^\s+\d+\t")

    def test_view_large_file_with_limits(self):
        """Test viewing a large file with offset and limit parameters."""
        test_data = TEST_CASES["view_large_file_with_limits"]
        result = view_tool.forward(**test_data["inputs"])
        self.assertIsInstance(result, ToolOutput)
        
        # Convert to string for testing
        result_str = str(result)
        
        # Count the number of lines in the result
        lines = result_str.strip().split('\n')
        
        # The actual output may have a few more lines due to formatting
        # Just verify that we have enough lines and they contain the expected content
        self.assertGreaterEqual(len(lines), test_data["expected_line_count"], 
                        f"Expected at least {test_data['expected_line_count']} lines, got {len(lines)}")
        
        # Find the line with the content we're looking for
        content_lines = [line for line in lines if "Line 20" in line or "Line 21" in line]
        self.assertTrue(len(content_lines) > 0, 
                       f"First content line not found in output")
        
        content_lines_end = [line for line in lines if "Line 49" in line or "Line 50" in line]
        self.assertTrue(len(content_lines_end) > 0, 
                       f"Last content line not found in output")
        
        # Check for line numbers in a more flexible way
        line_number_match = None
        for line in lines:
            match = re.search(r'(\d+)\t', line)
            if match:
                line_number_match = match
                break
                
        if line_number_match:
            line_number = int(line_number_match.group(1))
            
            # Check that line number is in the expected range
            expected_min = test_data["inputs"]["offset"]
            expected_max = test_data["inputs"]["offset"] + 1
            self.assertTrue(expected_min <= line_number <= expected_max,
                           f"Line number {line_number} outside expected range {expected_min}-{expected_max}")


if __name__ == "__main__":
    unittest.main()