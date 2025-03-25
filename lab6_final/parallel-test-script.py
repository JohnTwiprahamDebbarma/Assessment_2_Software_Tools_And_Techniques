#!/usr/bin/env python3
import subprocess
import time
import json
import os
from collections import defaultdict

def run_parallel_tests(config, iterations=3):   # config: Dictionary containing the parallel configuration
    worker_count = config["worker_count"]
    thread_count = config["thread_count"]
    dist_mode = config["dist_mode"]

    config_str = (
        f"-n {worker_count} --dist {dist_mode} --parallel-threads {thread_count}"
    )
    print(f"\nRunning parallel tests with configuration: {config_str}")

    cmd = ["pytest"]
    if worker_count != "1":
        cmd.extend(["-n", worker_count])
    if dist_mode != "no":
        cmd.extend(["--dist", dist_mode])
    if thread_count != "1":
        cmd.extend(["--parallel-threads", thread_count])

    execution_times = []
    all_failing_tests = []
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}")
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        execution_time = end_time - start_time
        execution_times.append(execution_time)

        # Parsing the output to identify failing tests:
        failing_tests = []
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if " FAILED " in line or " ERROR " in line:
                parts = line.split(" ")
                test_name = parts[0]
                failing_tests.append(test_name)
        all_failing_tests.append(failing_tests)
        print(
            f"  Execution time: {execution_time:.2f} seconds, failures: {len(failing_tests)}"
        )

    # Calculate Tpar - average execution time for this configuration
    tpar = sum(execution_times) / len(execution_times)
    
    # Identifying flaky tests:
    all_tests = set()
    for tests in all_failing_tests:
        all_tests.update(tests)
    flaky_tests = []
    for test in all_tests:
        counts = sum(1 for tests in all_failing_tests if test in tests)
        if 0 < counts < iterations:
            flaky_tests.append(test)
    print(f"\nConfiguration {config_str} Results:")
    print(f"- Tpar (average execution time): {tpar:.2f} seconds")
    print(f"- Flaky tests: {len(flaky_tests)}")
    return {
        "config": config,
        "tpar": tpar,  # Explicitly named as Tpar
        "avg_time": tpar,  # Keep for backward compatibility
        "times": execution_times,
        "failures": [len(tests) for tests in all_failing_tests],
        "failing_tests": all_failing_tests,
        "flaky_tests": flaky_tests,
    }

def calculate_speedup(sequential_time, parallel_time):
    return sequential_time / parallel_time

def execute_all_configurations():
    print("Executing all parallel configurations...")

    # Loading sequential execution time (Tseq) for reference:
    try:
        with open("sequential_time.json", "r") as f:
            sequential_data = json.load(f)
        
        # Handle both old and new format of sequential_time.json
        if "avg_time" in sequential_data:
            # Old format
            tseq = sequential_data["avg_time"]
        elif "avg_time_simple" in sequential_data:
            # New format - prefer the simple 5 executions measurement
            tseq = sequential_data["avg_time_simple"]
        elif "avg_time_nested" in sequential_data:
            # New format - fallback to nested measurement
            tseq = sequential_data["avg_time_nested"]
        elif "tseq_simple" in sequential_data and "value" in sequential_data["tseq_simple"]:
            # New format - nested structure
            tseq = sequential_data["tseq_simple"]["value"]
        elif "tseq_nested" in sequential_data and "value" in sequential_data["tseq_nested"]:
            # New format - nested structure
            tseq = sequential_data["tseq_nested"]["value"]
        else:
            # Fallback to a default if no recognized format is found
            print("  Warning: Could not find sequential execution time in expected format.")
            print("  Using default value of 10.0 seconds for Tseq.")
            tseq = 10.0
        
        print(f"Sequential execution time (Tseq): {tseq:.2f} seconds")
    except FileNotFoundError:
        print("  Warning: sequential_time.json not found.")
        print("  Using default value of 10.0 seconds for Tseq.")
        tseq = 10.0
    except json.JSONDecodeError:
        print("  Warning: Could not parse sequential_time.json.")
        print("  Using default value of 10.0 seconds for Tseq.")
        tseq = 10.0
    
    configurations = [
        # Process-level parallelization (pytest-xdist)
        {"worker_count": "1", "thread_count": "1", "dist_mode": "no"},
        {"worker_count": "auto", "thread_count": "1", "dist_mode": "no"},
        {"worker_count": "1", "thread_count": "1", "dist_mode": "load"},
        {"worker_count": "auto", "thread_count": "1", "dist_mode": "load"},
        # Thread-level parallelization (pytest-run-parallel)
        {"worker_count": "1", "thread_count": "auto", "dist_mode": "no"},
        {"worker_count": "1", "thread_count": "auto", "dist_mode": "load"},
        # Combined parallelization
        {"worker_count": "auto", "thread_count": "auto", "dist_mode": "no"},
        {"worker_count": "auto", "thread_count": "auto", "dist_mode": "load"},
    ]

    results = []
    for config in configurations:
        result = run_parallel_tests(config)
        speedup = calculate_speedup(tseq, result["tpar"])
        result["speedup"] = speedup
        
        # Store which Tseq was used for reference
        result["tseq_used"] = tseq
        
        print(f"- Speedup (Tseq/Tpar): {speedup:.2f}x")
        results.append(result)
        
        # Save results after each configuration in case of interruption
        with open("parallel_results.json", "w") as f:
            json.dump(results, f, indent=2)
    
    print("\nAll parallel configurations executed successfully")
    
    # Final summary
    print("\nSummary of Parallel Execution Times (Tpar) for Each Configuration:")
    for i, result in enumerate(results):
        config = result["config"]
        config_str = f"W={config['worker_count']}, T={config['thread_count']}, D={config['dist_mode']}"
        print(f"{i+1}. {config_str}: Tpar = {result['tpar']:.2f}s, Speedup = {result['speedup']:.2f}x")
    
    return results


if __name__ == "__main__":
    execute_all_configurations()
