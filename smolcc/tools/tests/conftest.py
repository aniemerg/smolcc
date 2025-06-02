#!/usr/bin/env python3
"""
Pytest configuration and fixtures for the SmolCC tool tests.
"""

import os
import shutil
import pytest


@pytest.fixture(scope="session")
def test_dir():
    """Return the absolute path to the test directory."""
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def test_data_dir(test_dir):
    """Return the absolute path to the test data directory."""
    return os.path.join(test_dir, "testdata")


@pytest.fixture(scope="session")
def temp_dir(test_dir):
    """
    Create and return a temporary directory for test files.
    This directory will be deleted after all tests are completed.
    """
    # Create the temp directory
    temp_path = os.path.join(test_dir, "temp")
    os.makedirs(temp_path, exist_ok=True)
    
    yield temp_path
    
    # Cleanup after all tests
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture(scope="function")
def temp_file_path(temp_dir):
    """
    Return a path to a temporary file that doesn't exist yet.
    Each test will get a unique file path.
    """
    import random
    import string
    
    # Generate a random filename
    letters = string.ascii_lowercase
    random_name = ''.join(random.choice(letters) for _ in range(10))
    
    return os.path.join(temp_dir, f"test_{random_name}.txt")


@pytest.fixture(scope="function")
def temp_edit_file(temp_dir):
    """
    Create a temporary file with initial content for Edit tool tests.
    """
    file_path = os.path.join(temp_dir, "test_edit_file.txt")
    
    with open(file_path, 'w') as f:
        f.write("function sayHello() {\n  console.log('Hello');\n}\n\nsayHello();")
    
    yield file_path
    
    # Cleanup after test
    if os.path.exists(file_path):
        os.remove(file_path)