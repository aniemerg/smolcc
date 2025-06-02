#!/usr/bin/env python3
"""
Unit tests for the Replace tool.

These tests verify that the Replace tool continues to produce the expected output
for standard inputs, effectively "locking in" the current behavior.
"""

import os
import json
import unittest
import shutil
from typing import Dict, Any

from smolcc.tools.replace_tool import write_tool

# Constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(TEST_DIR, "temp")

# Test cases with expected patterns to check in the output
TEST_CASES = {
    "create_new_file": {
        "inputs": {
            "file_path": "",  # Will be set dynamically
            "content": "This is a test file\nCreated by the Replace tool"
        },
        "expected_patterns": [
            "File created successfully",
            "test_replace.txt"  # Part of the file path
        ]
    },
    "create_complex_json_file": {
        "inputs": {
            "file_path": "",  # Will be set dynamically
            "content": json.dumps({
                "name": "test-file",
                "version": "1.0.0",
                "description": "A test JSON file with nested structure",
                "dependencies": {
                    "typescript": "^4.9.5",
                    "react": "^18.2.0"
                },
                "scripts": {
                    "start": "node dist/index.js",
                    "build": "tsc",
                    "test": "jest"
                },
                "config": {
                    "port": 3000,
                    "debug": True,
                    "environments": ["development", "staging", "production"]
                }
            }, indent=2)
        },
        "expected_patterns": [
            "File created successfully",
            "test_replace_complex.json"  # Part of the file path
        ]
    }
}


class ReplaceToolTests(unittest.TestCase):
    """Tests for the Replace tool."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all tests."""
        # Create temporary directory if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Set dynamic file paths
        TEST_CASES["create_new_file"]["inputs"]["file_path"] = os.path.join(TEMP_DIR, "test_replace.txt")
        TEST_CASES["create_complex_json_file"]["inputs"]["file_path"] = os.path.join(TEMP_DIR, "test_replace_complex.json")
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Remove any test files created
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)

    def _verify_file_content(self, file_path: str, expected_content: str) -> None:
        """
        Verify that a file has the expected content.
        
        Args:
            file_path: Path to the file
            expected_content: Expected content of the file
        """
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertEqual(content, expected_content)

    def test_create_new_file(self):
        """Test creating a new text file."""
        test_data = TEST_CASES["create_new_file"]
        
        # Remove the file if it exists
        if os.path.exists(test_data["inputs"]["file_path"]):
            os.remove(test_data["inputs"]["file_path"])
        
        # Run the tool
        result = write_tool.forward(**test_data["inputs"])
        
        # Verify the output contains expected patterns
        for pattern in test_data["expected_patterns"]:
            self.assertIn(pattern, result)
        
        # Verify the file was created with the correct content
        self._verify_file_content(
            test_data["inputs"]["file_path"],
            test_data["inputs"]["content"]
        )

    def test_create_complex_json_file(self):
        """Test creating a complex JSON file."""
        test_data = TEST_CASES["create_complex_json_file"]
        
        # Remove the file if it exists
        if os.path.exists(test_data["inputs"]["file_path"]):
            os.remove(test_data["inputs"]["file_path"])
        
        # Run the tool
        result = write_tool.forward(**test_data["inputs"])
        
        # Verify the output contains expected patterns
        for pattern in test_data["expected_patterns"]:
            self.assertIn(pattern, result)
        
        # Verify the file was created with the correct content
        self._verify_file_content(
            test_data["inputs"]["file_path"],
            test_data["inputs"]["content"]
        )

        # Verify the file can be parsed as valid JSON
        with open(test_data["inputs"]["file_path"], 'r') as f:
            parsed_json = json.load(f)
            self.assertEqual(parsed_json["name"], "test-file")
            self.assertEqual(parsed_json["version"], "1.0.0")
            self.assertEqual(parsed_json["dependencies"]["typescript"], "^4.9.5")
            self.assertEqual(parsed_json["dependencies"]["react"], "^18.2.0")


if __name__ == "__main__":
    unittest.main()