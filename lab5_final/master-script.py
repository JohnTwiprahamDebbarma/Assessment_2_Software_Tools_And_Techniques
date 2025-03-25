#!/usr/bin/env python3
import os
import subprocess
import time

def run_script(script_name):
    print(f"\n{'='*60}")
    print(f"Running {script_name}...")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        subprocess.run(['python', script_name], check=True)
        elapsed = time.time() - start_time
        print(f"\nCompleted {script_name} in {elapsed:.2f} seconds")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running {script_name}: {e}")
        return False

def main():
    os.makedirs('visualizations', exist_ok=True)
    
    # List of all visualization scripts
    scripts = [
        'coverage-comparison.py',
        'module-level-coverage.py',
        'pynguin-analysis.py',
        'coverage-sunburst.py',
        'uncovered-scenario-analysis.py'
    ]
    
    # Run each script
    success_count = 0
    for script in scripts:
        if os.path.exists(script):
            if run_script(script):
                success_count += 1
        else:
            print(f"Warning: Script {script} not found")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Visualization Generation Summary: {success_count}/{len(scripts)} scripts completed successfully")
    print(f"Results saved to the 'visualizations' directory")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
    