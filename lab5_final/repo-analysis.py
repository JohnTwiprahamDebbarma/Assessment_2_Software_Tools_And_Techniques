#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def find_python_files(directory):
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def find_test_files(directory):
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files

def analyze_imports(file_path):
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return imports

def analyze_repository(repo_path):
    print(f"Analyzing repository at {repo_path}...")
    
    # Find all Python files
    python_files = find_python_files(repo_path)
    print(f"Found {len(python_files)} Python files")
    
    # Find all test files
    test_files = find_test_files(repo_path)
    print(f"Found {len(test_files)} test files")
    
    # Analyze test structure
    if test_files:
        print("\nTest files:")
        for test_file in test_files[:5]:  # Show first 5 test files
            print(f"  {os.path.relpath(test_file, repo_path)}")
            # Analyze imports
            imports = analyze_imports(test_file)
            for imp in imports[:3]:  # Show first 3 imports
                print(f"    {imp}")
        if len(test_files) > 5:
            print(f"  ... and {len(test_files) - 5} more test files")
    else:
        print("\nNo test files found. We need to create our own test files.")
    
    # Check for __init__.py files
    init_files = []
    for root, _, files in os.walk(repo_path):
        if "__init__.py" in files:
            init_files.append(os.path.join(root, "__init__.py"))
    print(f"\nFound {len(init_files)} __init__.py files")
    
    # Analyze package structure
    package_structure = {}
    for root, dirs, files in os.walk(repo_path):
        rel_path = os.path.relpath(root, repo_path)
        if rel_path == ".":
            continue
        package_structure[rel_path] = [f for f in files if f.endswith(".py")]
    
    print("\nPackage structure:")
    for package, files in list(package_structure.items())[:5]:  # Show first 5 packages
        print(f"  {package}: {len(files)} Python files")
    if len(package_structure) > 5:
        print(f"  ... and {len(package_structure) - 5} more packages")
    
    return {
        "python_files": python_files,
        "test_files": test_files,
        "init_files": init_files,
        "package_structure": package_structure
    }

if __name__ == "__main__":
    repo_path = "."
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    
    analyze_repository(repo_path)
