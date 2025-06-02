#!/usr/bin/env python3
"""
Unit tests for the Edit tool.

These tests verify that the Edit tool continues to produce the expected output
for standard inputs, effectively "locking in" the current behavior.
"""

import os
import unittest
import tempfile
import shutil
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tools.edit_tool import file_edit_tool

# Constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(TEST_DIR, "testdata")
TEMP_DIR = os.path.join(TEST_DIR, "temp")

# Expected output patterns (partial matches to account for path differences)
EXPECTED_PATTERNS = {
    "create_new_file": {
        "inputs": {
            "file_path": "",  # Will be set dynamically
            "old_string": "",
            "new_string": "This is a test file\nCreated by the Edit tool"
        },
        "expected_patterns": [
            "has been updated",
            "This is a test file",
            "Created by the Edit tool"
        ]
    },
    "modify_file_with_context": {
        "inputs": {
            "file_path": "",  # Will be set dynamically
            "old_string": "function sayHello() {\n  console.log('Hello');\n}\n\nsayHello();",
            "new_string": "function sayHello(name) {\n  console.log(`Hello ${name}`);\n}\n\nsayHello('World');"
        },
        "expected_patterns": [
            "has been updated",
            "function sayHello(name)",
            "console.log(`Hello ${name}`)",
            "sayHello('World')"
        ]
    }
}


class EditToolTests(unittest.TestCase):
    """Tests for the Edit tool."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all tests."""
        # Create temporary directory if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Set dynamic file paths
        EXPECTED_PATTERNS["create_new_file"]["inputs"]["file_path"] = os.path.join(TEMP_DIR, "test_edit.txt")
        EXPECTED_PATTERNS["modify_file_with_context"]["inputs"]["file_path"] = os.path.join(TEMP_DIR, "test_edit_modify.txt")
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Remove any test files created
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)

    def setUp(self):
        """Set up before each test."""
        # Create test files needed for modification tests
        modify_file_path = EXPECTED_PATTERNS["modify_file_with_context"]["inputs"]["file_path"]
        with open(modify_file_path, 'w') as f:
            f.write(EXPECTED_PATTERNS["modify_file_with_context"]["inputs"]["old_string"])

    def test_create_new_file(self):
        """Test creating a new file with the Edit tool."""
        test_data = EXPECTED_PATTERNS["create_new_file"]
        
        # Make sure the file doesn't exist before the test
        if os.path.exists(test_data["inputs"]["file_path"]):
            os.remove(test_data["inputs"]["file_path"])
            
        # Run the tool
        result = file_edit_tool.forward(**test_data["inputs"])
        
        # Check that the result contains expected patterns
        for pattern in test_data["expected_patterns"]:
            self.assertIn(pattern, result)
            
        # Check that the file was actually created with the right content
        self.assertTrue(os.path.exists(test_data["inputs"]["file_path"]))
        with open(test_data["inputs"]["file_path"], 'r') as f:
            content = f.read()
            self.assertEqual(content, test_data["inputs"]["new_string"])

    def test_modify_file_with_context(self):
        """Test modifying an existing file."""
        test_data = EXPECTED_PATTERNS["modify_file_with_context"]
        
        # Run the tool
        result = file_edit_tool.forward(**test_data["inputs"])
        
        # Check that the result contains expected patterns
        for pattern in test_data["expected_patterns"]:
            self.assertIn(pattern, result)
            
        # Check that the file was actually modified with the right content
        with open(test_data["inputs"]["file_path"], 'r') as f:
            content = f.read()
            self.assertEqual(content, test_data["inputs"]["new_string"])


if __name__ == "__main__":
    unittest.main()