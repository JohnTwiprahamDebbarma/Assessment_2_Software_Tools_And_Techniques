#!/bin/bash
# Script to run tests and generate coverage reports

echo "Running tests and measuring coverage"
echo "==============================================================="

# Activate the virtual environment
source venv/bin/activate

# Make sure we're in the algorithms directory
cd algorithms

# Clear any previous coverage data
rm -f .coverage coverage.json 2>/dev/null || true

# Step 1: Run the original tests from the repository
echo -e "\n\n======== Running original tests (Test Suite A) ========"
if [ -d "tests" ]; then
    echo "Found 'tests' directory in repository"
    python ../direct-test-runner.py tests
    
    # Save Test Suite A coverage results
    if [ -f "coverage.json" ]; then
        cp coverage.json coverage.suite_a.json
        cp .coverage .coverage.suite_a
        echo "Saved Test Suite A coverage results"
    else
        echo "Warning: No coverage data generated from Test Suite A"
    fi
else
    echo "No 'tests' directory found in repository"
fi

cd ..

echo -e "\nTest execution completed!"