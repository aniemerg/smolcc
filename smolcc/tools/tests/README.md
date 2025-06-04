# SmolCC Tool Tests

This directory contains regression tests for the SmolCC tool implementations. 

## Test Structure

- Each tool has its own test file (`test_bash_tool.py`, `test_edit_tool.py`, etc.)
- The `testdata/` directory contains files used by the tests
- `conftest.py` provides pytest fixtures for common test operations
- `run_tests.py` is a simple script to run all or selected tests

## Running Tests

First, make sure the `smolcc` package is in your Python path. You can:

1. **Install the package in development mode from the project root**:

```bash
# From the project root (smolcc directory)
pip install -e .
```

2. **Or set the PYTHONPATH environment variable**:

```bash
# From the project root (smolcc directory)
export PYTHONPATH=$PYTHONPATH:<your_project_root>
```

3. **Or add a .pth file to your site-packages directory**:

```bash
# Create a .pth file with the path to your project
echo "<your_project_root>" > $(python -c "import site; print(site.getsitepackages()[0])")/smolcc.pth
```

Then you can run the tests using the provided script:

```bash
# Run all tests
./run_tests.py

# Run tests for a specific tool
./run_tests.py --tool bash

# Run with verbose output
./run_tests.py --verbose
```

Alternatively, you can use pytest directly:

```bash
# Run all tests
pytest

# Run tests for a specific tool
pytest test_bash_tool.py

# Run with verbose output
pytest -v
```

## Test Philosophy

1. **Independence**: Each test should be independent and not rely on the state from other tests
2. **Reproducibility**: Tests should produce consistent results when run repeatedly
3. **Stability**: Tests should not be brittle or prone to false failures
4. **Clarity**: Test failures should clearly indicate what went wrong

## Adding New Tests

To add a new test case for an existing tool:

1. Add any necessary test files to `testdata/`
2. Add a new test case to the relevant test file
3. Create a new test method that uses the test case

## Test Data Files

The `testdata/` directory contains files specifically designed for testing:

- Text files with known content
- Programming files (Python, JavaScript, TypeScript)
- Configuration files (JSON, YAML)
- Nested directory structure for testing recursive operations

## Temporary Files

Tests that require creating or modifying files use a temporary directory (`temp/`) that is:
- Created at the start of the test suite
- Cleaned up after tests complete

This ensures that tests don't leave behind unwanted files or interfere with each other.