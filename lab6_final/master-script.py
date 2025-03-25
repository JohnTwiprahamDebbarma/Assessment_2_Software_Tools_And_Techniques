#!/usr/bin/env python3
import os
import subprocess
import sys
import time

def print_separator():
    print("\n" + "=" * 80 + "\n")

def run_command(command, description=None):
    if description:
        print(f"\n{description}")

    print(f"$ {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    for line in process.stdout:
        print(line.rstrip())

    return_code = process.wait()
    if return_code != 0:
        print(f"Command failed with return code {return_code}")
    return return_code

def setup_environment():
    print_separator()
    print("SETTING UP ENVIRONMENT")
    print_separator()
    if not os.path.exists("algorithms"):
        success = (
            run_command(
                "git clone https://github.com/keon/algorithms.git",
                "Cloning repository...",
            )
            == 0
        )
        if not success:
            return False, None

    os.chdir("algorithms")
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    )
    commit_hash = result.stdout.strip()
    print(f"Current commit hash: {commit_hash}")

    # venv:
    if not os.path.exists("venv"):
        if sys.platform == "win32":
            success = (
                run_command("python -m venv venv", "Creating virtual environment...")
                == 0
            )
        else:
            success = (
                run_command("python3 -m venv venv", "Creating virtual environment...")
                == 0
            )

        if not success:
            return False, commit_hash

    if sys.platform == "win32":
        activate_cmd = ".\\venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"
    success = (
        run_command(
            f"{activate_cmd} && pip install pytest pytest-xdist pytest-run-parallel",
            "Installing dependencies...",
        )
        == 0
    )
    if not success:
        return False, commit_hash

    # Installing repository dependencies:
    success = (
        run_command(
            f"{activate_cmd} && pip install -e .",
            "Installing repository dependencies...",
        )
        == 0
    )
    if not success:
        return False, commit_hash
    return True, commit_hash

def run_sequential_tests(activate_cmd):
    print_separator()
    print("RUNNING SEQUENTIAL TESTS")
    print_separator()

    # Copying sequential test script to the repository directory:
    with open("sequential_tests.py", "w") as f:
        with open("../sequential-test-script.py", "r") as src:
            f.write(src.read())

    # Making the script executable:
    if sys.platform != "win32":
        os.chmod("sequential_tests.py", 0o755)

    # Running sequential tests:
    success = (
        run_command(
            f"{activate_cmd} && python sequential_tests.py",
            "Running sequential tests...",
        )
        == 0
    )
    return success

def run_parallel_tests(activate_cmd):
    print_separator()
    print("RUNNING PARALLEL TESTS")
    print_separator()

    # Copying parallel test script to repository directory:
    with open("parallel_tests.py", "w") as f:
        with open("../parallel-test-script.py", "r") as src:
            f.write(src.read())

    # Making script executable:
    if sys.platform != "win32":
        os.chmod("parallel_tests.py", 0o755)

    # Running parallel tests:
    success = (
        run_command(
            f"{activate_cmd} && python parallel_tests.py", "Running parallel tests..."
        )
        == 0
    )
    return success

def analyze_results(activate_cmd, commit_hash):
    print_separator()
    print("ANALYZING RESULTS")
    print_separator()

    # Copying analysis script to repository directory:
    with open("analyze_results.py", "w") as f:
        with open("../analysis-script.py", "r") as src:
            f.write(src.read())

    # Making the script executable:
    if sys.platform != "win32":
        os.chmod("analyze_results.py", 0o755)

    # Running analysis:
    success = (
        run_command(
            f"{activate_cmd} && python analyze_results.py", "Analyzing results..."
        )
        == 0
    )

    # Updating report with commit hash if needed:
    try:
        with open("test_parallelization_report.md", "r") as f:
            report_content = f.read()

        report_content = report_content.replace(
            "Unknown (could not retrieve commit hash)", commit_hash
        )

        with open("test_parallelization_report.md", "w") as f:
            f.write(report_content)
    except:
        print("Warning: Could not update commit hash in report")

    return success


def main():
    start_time = time.time()

    print("\nPython Test Parallelization Lab")
    print("===============================\n")

    success, commit_hash = setup_environment()
    if not success:
        print("Error: Failed to set up environment")
        return 1
    if sys.platform == "win32":
        activate_cmd = ".\\venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"

    # (a):
    success = run_sequential_tests(activate_cmd)
    if not success:
        print("Error: Failed to run sequential tests")
        return 1

    # (b):
    success = run_parallel_tests(activate_cmd)
    if not success:
        print("Error: Failed to run parallel tests")
        return 1

    # (c) & (d):
    success = analyze_results(activate_cmd, commit_hash)
    if not success:
        print("Error: Failed to analyze results")
        return 1
    end_time = time.time()
    total_time = end_time - start_time
    print_separator()
    print(f"Lab completed successfully in {total_time:.2f} seconds")
    print(f"Report generated: {os.path.abspath('test_parallelization_report.md')}")
    print_separator()
    return 0

if __name__ == "__main__":
    sys.exit(main())
