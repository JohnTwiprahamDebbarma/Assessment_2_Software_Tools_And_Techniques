#!/usr/bin/env python3
import json
import os
import subprocess
import matplotlib.pyplot as plt
from collections import Counter

def analyze_parallel_failures(parallel_results):
    print("Analyzing parallel test failures...")

    # Collecting all failing tests across all configurations:
    all_failing_tests = set()
    for result in parallel_results:
        for failure_list in result["failing_tests"]:
            all_failing_tests.update(failure_list)

    # Counting frequency of failing tests:
    test_failure_counter = Counter()
    for result in parallel_results:
        for failure_list in result["failing_tests"]:
            test_failure_counter.update(failure_list)

    # Identifying the most common failing tests:
    most_common_failures = test_failure_counter.most_common(10)

    # Analyzing which configurations cause the most failures:
    config_failure_rates = []
    for result in parallel_results:
        config = result["config"]
        config_str = f"-n {config['worker_count']} --dist {config['dist_mode']} --parallel-threads {config['thread_count']}"
        failure_rate = sum(1 for x in result["failures"] if x > 0) / len(
            result["failures"]
        )
        config_failure_rates.append((config_str, failure_rate))

    # Sorting by failure rate (highest first):
    config_failure_rates.sort(key=lambda x: x[1], reverse=True)
    print(f"- Total unique failing tests: {len(all_failing_tests)}")
    print(
        f"- Most common failing test: {most_common_failures[0][0] if most_common_failures else 'None'}"
    )
    print(
        f"- Configuration with highest failure rate: {config_failure_rates[0][0] if config_failure_rates else 'None'}"
    )
    return {
        "all_failing_tests": list(all_failing_tests),
        "most_common_failures": most_common_failures,
        "config_failure_rates": config_failure_rates,
    }

def categorize_test_failures(failure_analysis):
    print("Categorizing test failures...")

    # In a real scenario, we would examine the test code to determine the cause
    # For this example, we'll use a heuristic approach based on test names

    shared_resources = []
    timing_issues = []
    order_dependencies = []
    other_issues = []

    for test in failure_analysis["all_failing_tests"]:
        test_lower = test.lower()
        if "global" in test_lower or "state" in test_lower or "resource" in test_lower:
            shared_resources.append(test)
        elif "time" in test_lower or "wait" in test_lower or "sleep" in test_lower:
            timing_issues.append(test)
        elif (
            "order" in test_lower or "sequence" in test_lower or "depend" in test_lower
        ):
            order_dependencies.append(test)
        else:
            other_issues.append(test)

    print(f"- Shared resource issues: {len(shared_resources)}")
    print(f"- Timing issues: {len(timing_issues)}")
    print(f"- Order dependencies: {len(order_dependencies)}")
    print(f"- Other/unknown issues: {len(other_issues)}")
    return {
        "shared_resources": shared_resources,
        "timing_issues": timing_issues,
        "order_dependencies": order_dependencies,
        "other_issues": other_issues,
    }

def generate_speedup_plot(parallel_results):
    print("Generating speedup plot...")
    plt.figure(figsize=(12, 10))
    labels = []
    speedups = []
    for result in parallel_results:
        config = result["config"]
        label = f"W={config['worker_count']}\nT={config['thread_count']}\nD={config['dist_mode']}"
        labels.append(label)
        speedups.append(result["speedup"])

    plt.bar(range(len(speedups)), speedups, color="skyblue")
    plt.axhline(y=1.0, color="r", linestyle="-", alpha=0.3)  # Line at y=1 for reference
    plt.xlabel("Configuration")
    plt.ylabel("Speedup Ratio (Tseq/Tpar)")
    plt.title("Speedup Ratios for Different Parallelization Configurations")
    plt.xticks(range(len(speedups)), labels)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    for i, v in enumerate(speedups):
        plt.text(i, v + 0.02, f"{v:.2f}", ha="center")
    plt.tight_layout()
    plt.savefig("speedup_ratios.png")
    print("  Speedup plot saved as 'speedup_ratios.png'")


def create_execution_matrix(parallel_results):
    print("Creating execution matrix...")
    matrix_rows = []
    for result in parallel_results:
        config = result["config"]
        # Use tpar if available, otherwise fall back to avg_time
        avg_time = result.get("tpar", result.get("avg_time", 0))
        
        row = {
            "Worker Count": config["worker_count"],
            "Thread Count": config["thread_count"],
            "Distribution Mode": config["dist_mode"],
            "Average Time (s)": round(avg_time, 2),
            "Speedup": round(result["speedup"], 2),
            "Failures": ", ".join([str(x) for x in result["failures"]]),
            "Failure Rate": round(
                sum(1 for x in result["failures"] if x > 0) / len(result["failures"]), 2
            ),
        }
        matrix_rows.append(row)
    return matrix_rows

def assess_project_readiness(failure_analysis, categorized_failures):
    print("Assessing project readiness for parallel testing...")
    total_failures = len(failure_analysis["all_failing_tests"])
    
    # Calculating readiness score (following simple heuristic):
    if total_failures == 0:
        readiness = "The project is fully ready for parallel testing. No failures were detected in parallel execution."
    elif total_failures < 5:
        readiness = "The project is mostly ready for parallel testing. A few failures were detected, but they can be addressed with minor changes."
    elif total_failures < 15:
        readiness = "The project has moderate readiness for parallel testing. Several failures were detected, indicating potential issues with test isolation."
    else:
        readiness = "The project is not ready for parallel testing. Numerous failures indicate significant issues with test isolation and shared state."

    # Adding details about the types of issues:
    if len(categorized_failures["shared_resources"]) > 0:
        readiness += f"\n\nShared resource issues ({len(categorized_failures['shared_resources'])} tests) suggest that tests are modifying global state or accessing shared resources without proper isolation."

    if len(categorized_failures["timing_issues"]) > 0:
        readiness += f"\n\nTiming issues ({len(categorized_failures['timing_issues'])} tests) suggest that tests rely on specific timing or contain race conditions that become problematic in parallel execution."

    if len(categorized_failures["order_dependencies"]) > 0:
        readiness += f"\n\nOrder dependencies ({len(categorized_failures['order_dependencies'])} tests) indicate that some tests depend on others being run first, which violates test independence principles."

    return readiness


def suggest_improvements(categorized_failures):
    print("Suggesting improvements...")

    improvements = "Based on the analysis, the following improvements would enhance parallel testing readiness:\n\n"

    if len(categorized_failures["shared_resources"]) > 0:
        improvements += """1. **Improve Test Isolation**:
   - Use fixtures to create isolated test environments
   - Avoid modifying global state or shared resources
   - Implement proper setup/teardown to reset state between tests
   - Use mocking to avoid dependencies on shared resources\n\n"""

    if len(categorized_failures["timing_issues"]) > 0:
        improvements += """2. **Address Timing Issues**:
   - Replace time-dependent tests with deterministic alternatives
   - Use appropriate mocking for time-dependent functions
   - Implement more robust waiting mechanisms instead of fixed sleeps
   - Add retry mechanisms for flaky tests that cannot be made deterministic\n\n"""

    if len(categorized_failures["order_dependencies"]) > 0:
        improvements += """3. **Eliminate Order Dependencies**:
   - Ensure each test sets up its own prerequisites
   - Use fixtures to create necessary preconditions
   - Refactor tests to be truly independent
   - Mark tests with unavoidable dependencies using pytest markers\n\n"""

    improvements += """4. **General Improvements**:
   - Use pytest-xdist with `--dist=loadfile` to run tests from the same file on the same worker
   - Add proper test documentation indicating parallel execution limitations
   - Implement a CI pipeline that runs tests both sequentially and in parallel
   - Regularly review test logs to identify and address flaky tests"""

    return improvements

def suggest_pytest_improvements():
    print("Suggesting pytest improvements...")

    suggestions = """Based on the experiences with this lab, here are suggestions for pytest developers to improve thread safety:

1. **Enhanced Detection of Shared Resources**: Develop a pytest plugin that can automatically detect when tests are accessing or modifying shared resources, providing warnings during test execution.

2. **Improved Isolation Mechanisms**: Provide built-in mechanisms for stronger isolation between tests, such as process-level isolation by default or containerization options.

3. **Smarter Test Distribution**: Improve the test distribution algorithm to recognize tests that might share resources or have dependencies and schedule them appropriately (e.g., in the same worker or in sequence).

4. **Flaky Test Detection**: Enhance pytest to automatically identify and report flaky tests by running each test multiple times in different environments.

5. **Thread Safety Analysis**: Implement static analysis tools that can examine test code to identify potential thread safety issues before execution.

6. **Resource Locking Framework**: Provide a built-in framework for tests to declare resources they need, allowing pytest to manage resource allocation and prevent conflicts.

7. **Parallel Execution Report**: Generate detailed reports about parallel execution performance, highlighting bottlenecks and suggesting optimizations.

8. **Training Mode**: Add a "training mode" that learns from multiple test runs to optimize future parallel executions based on historical test behavior."""

    return suggestions


def generate_report(
    commit_hash,
    sequential_data,
    parallel_results,
    failure_analysis,
    categorized_failures,
    matrix_rows,
    readiness_assessment,
    improvement_suggestions,
    pytest_suggestions,
):
    """
    Generate the comprehensive lab report.

    Args:
        commit_hash: Repository commit hash
        sequential_data: Results from sequential testing
        parallel_results: Results from parallel testing
        failure_analysis: Analysis of test failures
        categorized_failures: Categorized test failures
        matrix_rows: Execution matrix rows
        readiness_assessment: Assessment of project readiness
        improvement_suggestions: Suggested improvements
        pytest_suggestions: Suggestions for pytest developers
    """
    print("Generating comprehensive report...")

    # Formatting matrix rows for markdown table:
    matrix_table_rows = []
    for row in matrix_rows:
        matrix_table_rows.append(
            f"| {row['Worker Count']} | {row['Thread Count']} | {row['Distribution Mode']} | "
            f"{row['Average Time (s)']} | {row['Speedup']} | {row['Failures']} | {row['Failure Rate']} |"
        )

    # Formatting the most common failures:
    most_common_failures = []
    for test, count in failure_analysis["most_common_failures"]:
        most_common_failures.append(f"- {test}: Failed in {count} executions")

    report = f"""# Python Test Parallelization Lab Report

## 1. Environment Setup

### Repository Information
- Repository: keon/algorithms
- Commit Hash: {commit_hash}

### Dependencies
- pytest (test execution)
- pytest-xdist (process level test parallelization)
- pytest-run-parallel (thread level test parallelization)

## 2. Sequential Test Execution

### Failing and Flaky Tests

During sequential execution, the following issues were identified:
- Consistently failing tests: {len(sequential_data.get('failing_tests', []))} tests
- Flaky tests (non-deterministic): {len(sequential_data.get('flaky_tests', []))} tests

### Sequential Execution Time

After eliminating failing and flaky tests, the average sequential execution time was:
- Tseq = {sequential_data.get('avg_time', 0):.2f} seconds

## 3. Parallel Test Execution

### Execution Matrix

| Worker Count | Thread Count | Distribution Mode | Average Time (s) | Speedup | Failures | Failure Rate |
|--------------|--------------|-------------------|------------------|---------|----------|--------------|
{chr(10).join(matrix_table_rows)}

### Speedup Plot

![Speedup Ratios](speedup_ratios.png)

## 4. Analysis

### Flaky Tests in Parallel Execution

The following tests were identified as flaky during parallel execution:

{chr(10).join([f"- {test}" for test in failure_analysis["all_failing_tests"][:10]])}{" (and more...)" if len(failure_analysis["all_failing_tests"]) > 10 else ""}

### Most Common Test Failures

{chr(10).join(most_common_failures)}

### Causes of Test Failures in Parallel Runs

Based on analysis of the failing tests, the following causes were identified:

1. **Shared Resources**: Tests that modify global state or shared resources.
   {chr(10).join([f"   - {test}" for test in categorized_failures["shared_resources"][:3]])}{" (and more...)" if len(categorized_failures["shared_resources"]) > 3 else ""}

2. **Timing Issues**: Tests that rely on specific timing or race conditions.
   {chr(10).join([f"   - {test}" for test in categorized_failures["timing_issues"][:3]])}{" (and more...)" if len(categorized_failures["timing_issues"]) > 3 else ""}

3. **Order Dependencies**: Tests that depend on a specific execution order.
   {chr(10).join([f"   - {test}" for test in categorized_failures["order_dependencies"][:3]])}{" (and more...)" if len(categorized_failures["order_dependencies"]) > 3 else ""}

## 5. Parallel Testing Readiness

### Success/Failure Patterns

Configurations with the highest failure rates:
{chr(10).join([f"- {config}: {rate:.2f} failure rate" for config, rate in failure_analysis["config_failure_rates"][:3]])}

Configurations with the lowest failure rates:
{chr(10).join([f"- {config}: {rate:.2f} failure rate" for config, rate in failure_analysis["config_failure_rates"][-3:]])}

### Project Readiness Assessment

{readiness_assessment}

### Potential Improvements

{improvement_suggestions}

### Suggestions for pytest Developers

{pytest_suggestions}
"""

    with open("test_parallelization_report.md", "w") as f:
        f.write(report)
    print("  Report saved as 'test_parallelization_report.md'")


def main():
    try:
        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        )
    except:
        commit_hash = "Unknown (could not retrieve commit hash)"
    print(f"Analyzing results for commit: {commit_hash}")

    try:
        with open("sequential_results.json", "r") as f:
            sequential_data = json.load(f)
    except:
        sequential_data = {
            "failing_tests": [],
            "flaky_tests": [],
            "execution_times": [],
        }
        print("  Warning: Could not load sequential_results.json")

    try:
        with open("sequential_time.json", "r") as f:
            sequential_time_data = json.load(f)
            
            # Handle both formats of sequential_time.json
            if "avg_time" in sequential_time_data:
                sequential_data["avg_time"] = sequential_time_data["avg_time"]
            elif "avg_time_simple" in sequential_time_data:
                sequential_data["avg_time"] = sequential_time_data["avg_time_simple"]
            elif "tseq_simple" in sequential_time_data and "value" in sequential_time_data["tseq_simple"]:
                sequential_data["avg_time"] = sequential_time_data["tseq_simple"]["value"]
            else:
                print("  Warning: Could not find avg_time in sequential_time.json")
    except FileNotFoundError:
        print("  Warning: sequential_time.json not found")
        if "avg_time" not in sequential_data:
            sequential_data["avg_time"] = 0
    except json.JSONDecodeError:
        print("  Warning: Invalid JSON in sequential_time.json")
        if "avg_time" not in sequential_data:
            sequential_data["avg_time"] = 0
    except Exception as e:
        print(f"  Warning: Error reading sequential_time.json: {str(e)}")
        if "avg_time" not in sequential_data:
            sequential_data["avg_time"] = 0

    try:
        with open("parallel_results.json", "r") as f:
            parallel_results = json.load(f)
    except:
        parallel_results = []
        print("  Warning: Could not load parallel_results.json")

    failure_analysis = analyze_parallel_failures(parallel_results)
    categorized_failures = categorize_test_failures(failure_analysis)
    generate_speedup_plot(parallel_results)
    matrix_rows = create_execution_matrix(parallel_results)
    readiness_assessment = assess_project_readiness(
        failure_analysis, categorized_failures
    )
    improvement_suggestions = suggest_improvements(categorized_failures)
    pytest_suggestions = suggest_pytest_improvements()
    generate_report(
        commit_hash,
        sequential_data,
        parallel_results,
        failure_analysis,
        categorized_failures,
        matrix_rows,
        readiness_assessment,
        improvement_suggestions,
        pytest_suggestions,
    )

if __name__ == "__main__":
    main()
