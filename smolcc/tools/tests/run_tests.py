#!/usr/bin/env python3
"""
Test runner for SmolCC tools.

This script provides a simple way to run all or selected tool tests.
"""

import os
import sys
import unittest
import argparse
import importlib


def discover_and_run_tests(tool_name=None):
    """
    Discover and run tests for all tools or a specific tool.
    
    Args:
        tool_name: Optional name of a specific tool to test
    
    Returns:
        True if all tests passed, False otherwise
    """
    loader = unittest.TestLoader()
    
    if tool_name:
        # Run tests for a specific tool
        try:
            module_name = f"test_{tool_name.lower()}_tool"
            module = importlib.import_module(module_name)
            suite = loader.loadTestsFromModule(module)
        except (ImportError, ModuleNotFoundError):
            print(f"Error: Could not find test module for tool '{tool_name}'")
            print("Available tools: bash, edit, glob, grep, ls, replace, view")
            return False
    else:
        # Run all tests by discovering test modules in the current directory
        suite = loader.discover(".", pattern="test_*.py")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run tests for SmolCC tools")
    parser.add_argument("--tool", help="Run tests for a specific tool (bash, edit, glob, grep, ls, replace, view)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Change to the test directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Set verbosity level
    if args.verbose:
        os.environ["SMOLCC_TEST_VERBOSE"] = "1"
    
    # Run the tests
    success = discover_and_run_tests(args.tool)
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())