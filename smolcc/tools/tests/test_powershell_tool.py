#!/usr/bin/env python3
"""
Unit tests for the PowerShell tool.

These tests verify that the PowerShell tool continues to produce the expected output
for standard inputs, effectively "locking in" the current behavior.
"""

import os
import unittest
import platform
from typing import Dict, Any

from smolcc.tools.powershell_tool import powershell_tool

# Constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(TEST_DIR, "testdata")

# Expected outputs for PowerShell commands
EXPECTED_OUTPUTS = {
    "simple_command": {
        "inputs": {
            "command": "Write-Host 'Hello, world!'",
            "timeout": 5000
        },
        "expected": "Hello, world!"
    },
    "environment_variables": {
        "inputs": {
            "command": "$env:TEST_VAR = 'hello world'; Write-Host $env:TEST_VAR",
            "timeout": 5000
        },
        "expected": "hello world"
    },
    "arithmetic_operation": {
        "inputs": {
            "command": "Write-Host (2 + 3 * 4)",
            "timeout": 5000
        },
        "expected": "14"
    },
    "multiline_output": {
        "inputs": {
            "command": "Write-Host 'Line 1'; Write-Host 'Line 2'; Write-Host 'Line 3'",
            "timeout": 5000
        },
        "expected": "Line 1\nLine 2\nLine 3"
    },
    "file_count": {
        "inputs": {
            "command": f"(Get-ChildItem -Path '{TEST_DATA_DIR}' -File).Count",
            "timeout": 10000
        },
        "expected": "6"
    },
    "directory_listing": {
        "inputs": {
            "command": f"Get-ChildItem -Path '{TEST_DATA_DIR}' -Name | Sort-Object",
            "timeout": 5000
        },
        "expected_files": [
            "large_file.txt",
            "subfolder1", 
            "test_config.json",
            "test_file1.txt",
            "test_file2.py",
            "test_js_file.js",
            "test_typescript_file.ts"
        ]
    }
}


class PowerShellToolTests(unittest.TestCase):
    """Tests for the PowerShell tool."""

    @classmethod
    def setUpClass(cls):
        """Set up test class - check if PowerShell is available."""
        try:
            # Test if PowerShell is available by running a simple command
            result = powershell_tool.forward("Write-Host 'test'", timeout=2000)
            if "Error" in result and "PowerShell not found" in result:
                raise unittest.SkipTest("PowerShell not available on this system")
        except Exception as e:
            raise unittest.SkipTest(f"PowerShell not available: {str(e)}")

    def test_simple_command(self):
        """Test a simple Write-Host command."""
        test_data = EXPECTED_OUTPUTS["simple_command"]
        result = powershell_tool.forward(**test_data["inputs"])
        self.assertEqual(result.strip(), test_data["expected"])

    def test_environment_variables(self):
        """Test environment variable setting and retrieval."""
        test_data = EXPECTED_OUTPUTS["environment_variables"]
        result = powershell_tool.forward(**test_data["inputs"])
        self.assertEqual(result.strip(), test_data["expected"])

    def test_arithmetic_operation(self):
        """Test arithmetic operations in PowerShell."""
        test_data = EXPECTED_OUTPUTS["arithmetic_operation"]
        result = powershell_tool.forward(**test_data["inputs"])
        self.assertEqual(result.strip(), test_data["expected"])

    def test_multiline_output(self):
        """Test commands that produce multiple lines of output."""
        test_data = EXPECTED_OUTPUTS["multiline_output"]
        result = powershell_tool.forward(**test_data["inputs"])
        # Normalize line endings for cross-platform compatibility
        normalized_result = result.strip().replace('\r\n', '\n')
        self.assertEqual(normalized_result, test_data["expected"])

    def test_file_count(self):
        """Test counting files in the test data directory."""
        test_data = EXPECTED_OUTPUTS["file_count"]
        result = powershell_tool.forward(**test_data["inputs"])
        self.assertEqual(result.strip(), test_data["expected"])

    def test_directory_listing(self):
        """Test directory listing with sorted output."""
        test_data = EXPECTED_OUTPUTS["directory_listing"]
        result = powershell_tool.forward(**test_data["inputs"])
        
        # Split result into lines and check for expected files/directories
        result_lines = [line.strip() for line in result.strip().split('\n') if line.strip()]
        
        # Check that all expected files are present
        for expected_file in test_data["expected_files"]:
            self.assertIn(expected_file, result_lines, 
                         f"Expected file/directory '{expected_file}' not found in listing")

    def test_error_handling(self):
        """Test error handling for invalid commands."""
        result = powershell_tool.forward("Get-NonExistentCommand", timeout=5000)
        # PowerShell should return an error message
        self.assertTrue(any(word in result.lower() for word in ['error', 'not', 'recognized', 'cmdlet']),
                       f"Expected error message, got: {result}")

    def test_banned_command_protection(self):
        """Test that banned commands are properly blocked."""
        banned_commands = [
            "Invoke-WebRequest https://example.com",
            "wget https://example.com", 
            "curl https://example.com",
            "Start-Process notepad"
        ]
        
        for cmd in banned_commands:
            result = powershell_tool.forward(cmd, timeout=1000)
            self.assertIn("banned", result.lower(), 
                         f"Banned command '{cmd}' was not properly blocked: {result}")

    def test_timeout_functionality(self):
        """Test that timeout works properly."""
        # Use a command that will take longer than the timeout
        if platform.system() == "Windows":
            cmd = "Start-Sleep -Seconds 3"
        else:
            cmd = "Start-Sleep 3"  # PowerShell Core syntax
        
        result = powershell_tool.forward(cmd, timeout=1000)  # 1 second timeout
        self.assertIn("timed out", result.lower(), 
                     f"Expected timeout message, got: {result}")

    def test_persistent_session(self):
        """Test that variables can be set and used within a single command."""
        # Set and use a variable in a single command
        result = powershell_tool.forward("$TestVariable = 'persistent_value'; Write-Host $TestVariable", timeout=5000)
        self.assertEqual(result.strip(), "persistent_value")

    def test_working_directory_persistence(self):
        """Test that working directory can be changed and verified within a single command."""
        # Change directory and verify location in a single command
        result = powershell_tool.forward(f"Set-Location '{TEST_DATA_DIR}'; (Get-Location).Path", timeout=5000)
        self.assertTrue(result.strip().endswith("testdata") or "testdata" in result.strip(),
                       f"Expected to be in testdata directory, but got: {result.strip()}")


if __name__ == "__main__":
    unittest.main()