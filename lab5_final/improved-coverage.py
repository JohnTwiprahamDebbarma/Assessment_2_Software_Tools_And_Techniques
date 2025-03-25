#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import os
import subprocess
import sys
from pathlib import Path

# Try to import coverage, but don't fail if it's not available
try:
    import coverage
    HAS_COVERAGE_MODULE = True
except ImportError:
    HAS_COVERAGE_MODULE = False
    print("Warning: 'coverage' module not found. Will use alternative approach.")

# Check if algorithms module is available, if not try to install it
try:
    import algorithms
    HAS_ALGORITHMS_MODULE = True
except ImportError:
    HAS_ALGORITHMS_MODULE = False
    print("Warning: 'algorithms' module not found. Trying to install it...")
    try:
        # Try to install the algorithms package in editable mode
        subprocess.run(['pip', 'install', '-e', '.'], check=True)
        print("Successfully installed 'algorithms' package.")
        try:
            import algorithms
            HAS_ALGORITHMS_MODULE = True
        except ImportError:
            print("Error: Still unable to import 'algorithms' module after installation.")
    except subprocess.CalledProcessError:
        print("Error: Failed to install 'algorithms' package.")

def analyze_coverage_manually(source_path="algorithms"):
    """Analyze coverage without relying on pytest"""
    if HAS_COVERAGE_MODULE:
        # Use the coverage module if available
        cov = coverage.Coverage(source=[source_path])
        cov.start()
        
        # Try to import all modules
        for root, _, files in os.walk(source_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    module_path = os.path.join(root, file)
                    module_name = os.path.relpath(module_path, ".").replace("/", ".").replace(".py", "")
                    try:
                        __import__(module_name)
                    except Exception:
                        pass  # Ignore import errors
        
        cov.stop()
        cov.save()
        
        # Generate reports
        cov.json_report(outfile="coverage.json")
        cov.html_report(directory="htmlcov")
        
        print("Generated coverage reports using coverage module")
    else:
        # Alternative approach using manual inspection
        generate_empty_coverage_data()
        print("Generated empty coverage data (coverage module not available)")

def generate_empty_coverage_data():
    """Generate empty coverage data for files"""
    result = {
        "meta": {
            "version": "7.7.1",
            "timestamp": "2025-02-06T00:00:00",
            "branch_coverage": True,
            "show_contexts": False
        },
        "files": {},
        "totals": {
            "covered_lines": 0,
            "num_statements": 0,
            "percent_covered": 0.0,
            "percent_covered_display": "0%",
            "missing_lines": 0,
            "excluded_lines": 0
        }
    }
    
    # Find all Python files in algorithms
    for root, _, files in os.walk("algorithms"):
        for file in files:
            if file.endswith(".py") and not file.startswith("test_"):
                file_path = os.path.join(root, file)
                
                # Get line count
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    line_count = len([line for line in lines if line.strip() and not line.strip().startswith("#")])
                    
                    # Create entry for this file
                    result["files"][file_path] = {
                        "executed_lines": [],
                        "summary": {
                            "covered_lines": 0,
                            "num_statements": line_count,
                            "percent_covered": 0.0,
                            "percent_covered_display": "0%",
                            "missing_lines": line_count,
                            "excluded_lines": 0
                        },
                        "missing_lines": list(range(1, line_count + 1)),
                        "excluded_lines": []
                    }
                    
                    # Update totals
                    result["totals"]["num_statements"] += line_count
                    result["totals"]["missing_lines"] += line_count
                except:
                    pass
    
    # Save the coverage data
    with open("coverage.json", "w") as f:
        json.dump(result, f)
    
    return result

def load_coverage_data(json_file='coverage.json'):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Coverage data file {json_file} not found. Generating empty coverage data.")
        return generate_empty_coverage_data()

def analyze_coverage(data):
    """Analyze line, branch, and function coverage"""
    total_lines = 0
    covered_lines = 0
    file_coverage = {}
    
    # Process the data for each file
    for file_path, file_data in data.get('files', {}).items():
        # Skip test files
        if '/tests/' in file_path or file_path.endswith('__init__.py'):
            continue
            
        file_missing_lines = len(file_data.get('missing_lines', []))
        file_covered_lines = file_data.get('summary', {}).get('covered_lines', 0)
        file_total_lines = file_data.get('summary', {}).get('num_statements', 0)
        
        if file_total_lines > 0:
            file_coverage[file_path] = {
                'total_lines': file_total_lines,
                'covered_lines': file_covered_lines,
                'line_coverage': file_covered_lines / file_total_lines if file_total_lines > 0 else 0,
                'missing_lines': file_data.get('missing_lines', [])
            }
            
            total_lines += file_total_lines
            covered_lines += file_covered_lines
    
    # Get overall metrics
    line_coverage = covered_lines / total_lines if total_lines > 0 else 0
    branch_coverage_str = data.get('totals', {}).get('percent_covered_display', '0%')
    branch_coverage = float(branch_coverage_str.strip('%')) / 100 if isinstance(branch_coverage_str, str) else 0
    
    return {
        'line_coverage': line_coverage,
        'branch_coverage': branch_coverage,
        'function_coverage': 0.0,  # No function coverage data without pytest-func-cov
        'file_coverage': file_coverage
    }

def plot_coverage(coverage_data, output_prefix='test_suite_a'):
    # Plot overall coverage metrics
    labels = ['Line', 'Branch', 'Function']
    values = [
        coverage_data['line_coverage'] * 100,
        coverage_data['branch_coverage'] * 100,
        coverage_data['function_coverage'] * 100
    ]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color=['#3498db', '#2ecc71', '#e74c3c'])
    
    # Add labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                 f'{height:.1f}%', ha='center', va='bottom')
    
    plt.ylim(0, 100)
    plt.ylabel('Coverage (%)')
    plt.title(f'{output_prefix.replace("_", " ").title()} Coverage')
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_coverage.png')
    plt.close()
    
    # Find all files that don't have 100% coverage
    file_coverage = coverage_data['file_coverage']
    not_fully_covered_files = [(file, info) for file, info in file_coverage.items() 
                              if info['line_coverage'] < 1.0]
    
    # Plot file coverage for the top 10 files with lowest coverage (for visualization only)
    sorted_files = sorted(not_fully_covered_files, key=lambda x: x[1]['line_coverage'])[:10]
    
    if sorted_files:
        plt.figure(figsize=(12, 8))
        file_names = [os.path.basename(f[0]) for f in sorted_files]
        file_values = [f[1]['line_coverage'] * 100 for f in sorted_files]
        
        bars = plt.barh(file_names, file_values, color='#f39c12')
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 1, bar.get_y() + bar.get_height()/2.,
                     f'{width:.1f}%', ha='left', va='center')
        
        plt.xlim(0, 100)
        plt.xlabel('Line Coverage (%)')
        plt.title('Top 10 Files with Lowest Coverage')
        plt.tight_layout()
        plt.savefig(f'{output_prefix}_file_coverage.png')
        plt.close()
    
    # Return all files that don't have 100% coverage
    return not_fully_covered_files

def run_tests_and_record_coverage(suite_name='a'):
    print(f"Running Test Suite {suite_name.upper()}...")
    
    try:
        if suite_name.lower() == 'a':
            # First try existing tests if pytest-cov is available
            try:
                cmd = ['pytest', 'tests', '--cov=algorithms', '--cov-report=term', '--cov-report=html', '--cov-report=json']
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(result.stdout)
                
                # Check if coverage data was generated
                if os.path.exists('coverage.json'):
                    print("Coverage data generated from existing tests")
                else:
                    print("No coverage data from existing tests")
            except Exception as e:
                print(f"Error running pytest with coverage: {e}")
            
            # If no coverage data, try manual analysis
            if not os.path.exists('coverage.json'):
                print("Generating coverage data manually...")
                analyze_coverage_manually()
    except Exception as e:
        print(f"Warning: Error during test execution: {e}")
    
    # Save the coverage data for this test suite
    if os.path.exists('.coverage'):
        os.system(f"cp .coverage .coverage.suite_{suite_name}")
    if os.path.exists('coverage.json'):
        os.system(f"cp coverage.json coverage.suite_{suite_name}.json")
    else:
        # If no coverage.json was generated, create an empty one
        generate_empty_coverage_data()
        if os.path.exists('coverage.json'):
            os.system(f"cp coverage.json coverage.suite_{suite_name}.json")
    
    # Load and analyze coverage data
    data = load_coverage_data()
    coverage_data = analyze_coverage(data)
    
    # Plot coverage and get files without 100% coverage
    not_fully_covered_files = plot_coverage(coverage_data, f'test_suite_{suite_name}')
    
    print(f"\nTest Suite {suite_name.upper()} Coverage Analysis:")
    print(f"Line Coverage: {coverage_data['line_coverage']:.2%}")
    print(f"Branch Coverage: {coverage_data['branch_coverage']:.2%}")
    print(f"Function Coverage: {coverage_data['function_coverage']:.2%}")
    
    # Save files without 100% coverage for test generation if this is suite A
    if suite_name.lower() == 'a' and not_fully_covered_files:
        print(f"\nFound {len(not_fully_covered_files)} files without 100% coverage:")
        with open('low_coverage_files.json', 'w') as f:
            low_cov_dict = {file: {"line_coverage": info["line_coverage"]} for file, info in not_fully_covered_files}
            json.dump(low_cov_dict, f, indent=2)
        
        for file_path, info in not_fully_covered_files[:10]:  # Show first 10 for brevity
            print(f"  {file_path}: {info['line_coverage']:.2%}")
        
        if len(not_fully_covered_files) > 10:
            print(f"  ... and {len(not_fully_covered_files) - 10} more files")
    
    return coverage_data

if __name__ == '__main__':
    os.makedirs('results', exist_ok=True)
    
    # Run test suite A and analyze coverage
    suite_a_data = run_tests_and_record_coverage('a')
