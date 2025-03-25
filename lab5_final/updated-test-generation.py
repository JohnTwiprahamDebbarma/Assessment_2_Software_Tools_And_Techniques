#!/usr/bin/env python3
import os
import json
import subprocess
import sys
import shutil
import time
import signal
from pathlib import Path

def load_low_coverage_files():
    try:
        with open('low_coverage_files.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("Error: low_coverage_files.json not found. Run improved-coverage.py first.")
        sys.exit(1)

def file_path_to_module_name(file_path):
    module_path = file_path.replace(os.sep, '.')
    if module_path.endswith('.py'):
        module_path = module_path[:-3]
    
    return module_path

def generate_tests_for_file(file_path, timeout=90):
    module_name = file_path_to_module_name(file_path)
    output_dir_name = module_name.replace('.', '_')
    output_dir = f"pynguin_tests/{output_dir_name}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating tests for {module_name}...")
    
    try:
        # Setting the PYNGUIN_DANGERAWARE environment variable:
        env = os.environ.copy()
        env["PYNGUIN_DANGERAWARE"] = "true"
        
        cmd = [
            "pynguin",
            "--project-path=.",
            f"--output-path={output_dir}",
            f"--module-name={module_name}",
            "--algorithm=DYNAMOSA",
            "--budget", "60",
            "-v"  # verbose flag
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Run pynguin with timeout
        try:
            start_time = time.time()
            process = subprocess.Popen(
                cmd, 
                env=env, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"Waiting for Pynguin to complete (max {timeout} seconds)...")
            stdout_data, stderr_data = "", ""
            elapsed = 0
            while elapsed < timeout:
                if process.poll() is not None:
                    # Process finished
                    stdout_data, stderr_data = process.communicate()
                    break
                time.sleep(1)
                elapsed = time.time() - start_time
            
            # Kill if still running
            if process.poll() is None:
                print(f"Pynguin is taking too long for {module_name}, terminating...")
                # Try to terminate gently first
                process.terminate()
                try:
                    process.wait(5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                
                stdout_data, stderr_data = process.communicate()
                print("Process terminated.")
            
            test_files = list(Path(output_dir).glob("test_*.py"))
            if test_files:
                print(f"Successfully generated tests for {module_name}")
                # Make test files importable by creating __init__.py
                with open(os.path.join(output_dir, "__init__.py"), "w") as f:
                    pass
                return True
            else:
                print(f"No test files generated for {module_name}. Skipping.")
                # Remove empty directory
                shutil.rmtree(output_dir, ignore_errors=True)
                return False
                
        except subprocess.SubprocessError as e:
            print(f"Subprocess error for {module_name}: {e}")
            # Remove empty directory
            shutil.rmtree(output_dir, ignore_errors=True)
            return False
            
    except Exception as e:
        print(f"Exception while generating tests for {module_name}: {e}")
        # Remove empty directory
        shutil.rmtree(output_dir, ignore_errors=True)
        return False

def main():
    # Ensure PYNGUIN_DANGERAWARE is set
    os.environ["PYNGUIN_DANGERAWARE"] = "true"
    
    # Create directory for generated tests
    os.makedirs("pynguin_tests", exist_ok=True)
    
    # Create __init__.py for the pynguin_tests directory
    with open("pynguin_tests/__init__.py", "w") as f:
        pass
    
    # Load files with low coverage
    low_coverage_files = load_low_coverage_files()
    
    # Generate tests for each file
    pynguin_successes = 0
    total_files = len(low_coverage_files)
    
    print(f"Generating tests for {total_files} files with low coverage using Pynguin only...")
    
    # Fix module imports to prevent import errors in the generated tests
    # Add algorithms.tree and algorithms.maths.polynomial to sys.modules
    try:
        import algorithms.tree
        sys.modules['tree'] = algorithms.tree
        import algorithms.maths.polynomial
        sys.modules['polynomial'] = algorithms.maths.polynomial
        print("Successfully patched import modules")
    except ImportError as e:
        print(f"Warning: Failed to patch import modules: {e}")
    
    # Process all files
    for i, file_path in enumerate(list(low_coverage_files.keys())):
        # Skip test files and __init__.py
        if '/tests/' in file_path or file_path.endswith('__init__.py'):
            continue
        
        print(f"Processing file {i+1}/{total_files}: {file_path}")
        
        # Try pynguin with timeout
        if generate_tests_for_file(file_path):
            pynguin_successes += 1
    
    print(f"\nTest generation complete: {pynguin_successes}/{total_files} files processed successfully with Pynguin")
    
    # Create master test file if any tests were generated
    if pynguin_successes > 0:
        pynguin_test_dirs = [d for d in os.listdir("pynguin_tests") 
                           if os.path.isdir(os.path.join("pynguin_tests", d)) 
                           and d != "__pycache__"]
        
        with open("pynguin_tests/test_all_pynguin.py", "w") as f:
            f.write("# Auto-generated file that imports all pynguin tests\n\n")
            for test_dir in pynguin_test_dirs:
                test_files = [tf for tf in os.listdir(os.path.join("pynguin_tests", test_dir)) 
                            if tf.startswith("test_") and tf.endswith(".py")]
                for test_file in test_files:
                    module_name = f"pynguin_tests.{test_dir}.{test_file[:-3]}"
                    f.write(f"import {module_name}\n")
    else:
        print("No Pynguin tests were successfully generated.")

if __name__ == '__main__':
    main()