#!/usr/bin/env python3
"""
Wrapper script for running SmolCC tool tests.

This script provides a simple interface to run the tool tests from the project root.
"""

import os
import sys
import subprocess
import argparse


def main():
    """Run the SmolCC tool tests."""
    parser = argparse.ArgumentParser(description="Run SmolCC tool tests")
    parser.add_argument("--tool", help="Run tests for a specific tool (bash, edit, glob, grep, ls, replace, view)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Path to the test runner
    test_dir = os.path.join("tools", "tests")
    test_runner = os.path.join(test_dir, "run_tests.py")
    
    # Build command
    cmd = [sys.executable, test_runner]
    if args.tool:
        cmd.extend(["--tool", args.tool])
    if args.verbose:
        cmd.append("--verbose")
    
    # Run the tests
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())