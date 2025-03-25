#!/bin/bash
# Main script to automate the entire code coverage analysis and test generation process
# Exit on error
set -e

echo "========================================================"
echo "Code Coverage Analysis and Test Generation Automation"
echo "========================================================"

# Create a results directory
mkdir -p results

# Step 1: Clone the repository and set up the environment
echo -e "\n\n======== Step 1: Setting up environment and cloning repository ========"
bash setup-script.sh

# Verify pynguin is installed and working
echo "Verifying pynguin installation..."
export PYNGUIN_DANGERAWARE=true
pynguin --help || {
    echo "Installing pynguin..."
    pip install pynguin
    echo "Checking pynguin installation..."
    pynguin --help
}

# Copy configuration files to the algorithms directory
cp pytest.ini algorithms/
cp .coveragerc algorithms/

# Fix relative imports in the repository to ensure tests can run correctly
cd algorithms
echo -e "\n\n======== Patching repository import statements ========"
# This fixes relative imports to work with our generated tests
find . -name "*.py" -type f -exec grep -l "from tree" {} \; | xargs -I{} sed -i 's/from tree/from algorithms.tree/g' {} || true
find . -name "*.py" -type f -exec grep -l "import tree" {} \; | xargs -I{} sed -i 's/import tree/import algorithms.tree/g' {} || true
find . -name "*.py" -type f -exec grep -l "from polynomial" {} \; | xargs -I{} sed -i 's/from polynomial/from algorithms.maths.polynomial/g' {} || true
cd ..

# Step 2: Analyze the repository structure
echo -e "\n\n======== Step 2: Analyzing repository structure ========"
cd algorithms
python ../repo-analysis.py .
cd ..

# Step 3: Run Test Suite A (original tests) and analyze coverage
echo -e "\n\n======== Step 3 & 4: Running Test Suite A and analyzing coverage ========"
cd algorithms
python -m pytest tests --cov=algorithms --cov-report=term --cov-report=html --cov-report=json
# Save test suite A results
if [ -f "coverage.json" ]; then
    cp coverage.json coverage.suite_a.json
    cp .coverage .coverage.suite_a
    echo "Saved Test Suite A coverage results"
fi
cd ..

# Copy results
cp algorithms/coverage.suite_a.json results/ 2>/dev/null || true
cp -r algorithms/htmlcov results/htmlcov_suite_a 2>/dev/null || true

# Step 4: Generate tests for files with low coverage
echo -e "\n\n======== Step 5: Generating Test Suite B with pynguin only ========"
cd algorithms

# Run improved coverage analysis to identify files with low coverage
python ../improved-coverage.py

# Generate tests using Pynguin only
echo "Running test generation script with Pynguin..."
python ../updated-test-generation.py

cd ..

# Step 5: Run Test Suite B and measure coverage
echo -e "\n\n======== Step 6: Running Test Suite B and measuring coverage ========"
cd algorithms
rm -f .coverage coverage.json 2>/dev/null || true

# Use direct test runner to run the generated tests and measure coverage
python ../direct-test-runner.py pynguin_tests

# Save test suite B results
if [ -f "coverage.json" ]; then
    cp coverage.json coverage.suite_b.json
    cp .coverage .coverage.suite_b
    echo "Saved Test Suite B coverage results"
else
    echo "No coverage data from Test Suite B. Creating empty file for comparison."
    echo '{"totals": {"covered_lines": 0, "num_statements": 1, "percent_covered": 0}}' > coverage.suite_b.json
fi
cd ..

# Copy results
cp algorithms/coverage.suite_b.json results/ 2>/dev/null || true
cp -r algorithms/htmlcov results/htmlcov_suite_b 2>/dev/null || true

# Step 6: Compare the test suites and report findings
echo -e "\n\n======== Step 7: Comparing test suites and reporting findings ========"
cd algorithms
python ../compare-test-suites.py
cd ..

# Copy final results
cp algorithms/coverage_comparison.png results/ 2>/dev/null || true
cp algorithms/file_improvement.png results/ 2>/dev/null || true
cp algorithms/coverage_report.md results/ 2>/dev/null || true

echo -e "\n\n======== Process Complete ========"
echo "All results are available in the 'results' directory:"
ls -la results/

if [ -f "results/coverage_report.md" ]; then
    echo -e "\nSummary of findings:"
    grep -A 5 "Overall Coverage Metrics" results/coverage_report.md | grep -v "Overall Coverage Metrics" || echo "No summary available"
fi
