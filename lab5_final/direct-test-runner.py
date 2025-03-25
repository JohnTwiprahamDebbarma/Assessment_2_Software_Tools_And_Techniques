#!/usr/bin/env python3
import os
import sys
import importlib
import inspect
import coverage
import pytest
import unittest
from pathlib import Path

def setup_paths():
    """Add the necessary paths to sys.path for module imports"""
    # Get the current directory
    repo_root = os.getcwd()
    
    # Add repo root to path to enable imports
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    
    # Check if we can import from algorithms package
    try:
        import algorithms
        print(f"Successfully imported algorithms package from {algorithms.__file__}")
    except ImportError:
        print("Warning: Unable to import algorithms package. Check your paths.")

def find_all_tests(test_dirs):
    test_files = []
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            for root, _, files in os.walk(test_dir):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        test_files.append(os.path.join(root, file))
    
    return test_files

def discover_and_run_tests(test_dirs):
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Discover tests in each directory
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"Discovering tests in {test_dir}...")
            discovered_tests = test_loader.discover(test_dir, pattern="test_*.py")
            test_suite.addTests(discovered_tests)
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result

def run_tests_with_coverage(test_dirs):
    """Run tests and measure coverage"""
    # Setup the paths
    setup_paths()
    
    # Get all test files
    test_files = find_all_tests(test_dirs)
    
    if not test_files:
        print("No test files found in directories:", test_dirs)
        return False
    
    print(f"Found {len(test_files)} test files")
    
    # Start coverage measurement
    cov = coverage.Coverage(source=['algorithms'])
    cov.start()
    
    # Run the tests using unittest discovery
    test_result = discover_and_run_tests(test_dirs)
    
    # Stop coverage measurement
    cov.stop()
    
    # Write coverage data to files
    cov.save()
    cov.json_report(outfile='coverage.json')
    cov.html_report(directory='htmlcov')
    
    # Print coverage report
    print("\nCoverage Report:")
    cov.report()
    
    return test_result.wasSuccessful()

if __name__ == "__main__":
    # Get the test directories from arguments, or use defaults
    test_dirs = sys.argv[1:] if len(sys.argv) > 1 else ['tests', 'pynguin_tests']
    
    # Run tests with coverage
    success = run_tests_with_coverage(test_dirs)
    
    if success:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed.")
