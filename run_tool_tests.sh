#!/bin/bash
# Wrapper script for running SmolCC tool tests

# Ensure the project directory is in the Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Change to the smolcc directory
cd smolcc || { echo "Error: smolcc directory not found"; exit 1; }

# Run the tests with any provided arguments
python run_tool_tests.py "$@"