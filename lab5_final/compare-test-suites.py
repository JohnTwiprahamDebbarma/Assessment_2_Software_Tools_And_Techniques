#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import os
import re
from pathlib import Path

def load_coverage_data(suite_a_file='coverage.suite_a.json', 
                      suite_b_file='coverage.suite_b.json'):
    suite_a_data = {}
    suite_b_data = {}
    
    try:
        with open(suite_a_file, 'r') as f:
            suite_a_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {suite_a_file} not found")
    
    try:
        with open(suite_b_file, 'r') as f:
            suite_b_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {suite_b_file} not found")
    
    return suite_a_data, suite_b_data

def analyze_coverage(data):
    """Analyze line, branch, and function coverage"""
    if not data:
        return {
            'line_coverage': 0,
            'branch_coverage': 0,
            'file_coverage': {}
        }
    
    total_lines = 0
    covered_lines = 0
    file_coverage = {}
    
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
    
    # Calculate overall metrics
    line_coverage = covered_lines / total_lines if total_lines > 0 else 0
    branch_coverage = data.get('totals', {}).get('percent_covered', 0) / 100 if isinstance(data.get('totals', {}).get('percent_covered'), (int, float)) else 0
    
    return {
        'line_coverage': line_coverage,
        'branch_coverage': branch_coverage,
        'file_coverage': file_coverage
    }

def plot_comparison(suite_a_data, suite_b_data):
    """Plot the coverage comparison between test suites A and B"""
    # Plot the coverage comparison
    labels = ['Line Coverage', 'Branch Coverage']
    suite_a_values = [
        suite_a_data['line_coverage'] * 100,
        suite_a_data['branch_coverage'] * 100
    ]
    suite_b_values = [
        suite_b_data['line_coverage'] * 100,
        suite_b_data['branch_coverage'] * 100
    ]
    
    x = range(len(labels))
    width = 0.35
    
    plt.figure(figsize=(10, 6))
    bars1 = plt.bar(x, suite_a_values, width, label='Test Suite A')
    bars2 = plt.bar([i + width for i in x], suite_b_values, width, label='Test Suite B')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
    
    plt.ylabel('Coverage (%)')
    plt.title('Test Suite A vs Test Suite B Coverage Comparison')
    plt.xticks([i + width/2 for i in x], labels)
    plt.ylim(0, 100)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('coverage_comparison.png')
    plt.close()
    
    # Compare file coverage for files that were targeted by test suite B
    improved_files = {}
    
    for file in suite_b_data['file_coverage']:
        if file in suite_a_data['file_coverage']:
            a_coverage = suite_a_data['file_coverage'][file]['line_coverage']
            b_coverage = suite_b_data['file_coverage'][file]['line_coverage']
            
            if b_coverage > a_coverage:
                improved_files[file] = {
                    'suite_a': a_coverage,
                    'suite_b': b_coverage,
                    'improvement': b_coverage - a_coverage
                }
    
    # Plot top improved files
    if improved_files:
        sorted_files = sorted(improved_files.items(), 
                             key=lambda x: x[1]['improvement'], 
                             reverse=True)[:10]
        
        plt.figure(figsize=(12, 8))
        file_names = [os.path.basename(f[0]) for f in sorted_files]
        improvement_values = [f[1]['improvement'] * 100 for f in sorted_files]
        
        bars = plt.barh(file_names, improvement_values, color='green')
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 1, bar.get_y() + bar.get_height()/2.,
                    f'+{width:.1f}%', ha='left', va='center')
        
        plt.xlabel('Coverage Improvement (%)')
        plt.title('Top Files with Improved Coverage')
        plt.tight_layout()
        plt.savefig('file_improvement.png')
        plt.close()
    
    return improved_files

def find_uncovered_scenarios(data):
    """Find and categorize uncovered scenarios based on missing lines"""
    scenarios = []
    
    for file_path, file_data in data.get('files', {}).items():
        # Skip test files
        if '/tests/' in file_path or file_path.endswith('__init__.py'):
            continue
        
        if file_data.get('missing_lines'):
            # Try to read the file content
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                try:
                    with open(file_path_obj, 'r') as f:
                        content = f.readlines()
                    
                    # Check each missing line to identify patterns/scenarios
                    for line_num in file_data.get('missing_lines', []):
                        if 0 <= line_num-1 < len(content):
                            line = content[line_num-1].strip()
                            
                            # Look for error handling
                            if re.search(r'except|raise|error|exception|try', line, re.IGNORECASE):
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Error handling'
                                })
                            
                            # Look for boundary conditions
                            elif re.search(r'if.*==|if.*<=|if.*>=|if.*>|if.*<', line):
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Boundary condition'
                                })
                            
                            # Look for null/empty checks
                            elif re.search(r'if.*None|if.*is None|if not|if.*empty', line):
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Null/empty check'
                                })
                            
                            # Look for complex logic
                            elif re.search(r'and|or|not|all|any', line):
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Complex logic'
                                })
                            
                            # Default case
                            else:
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Uncategorized'
                                })
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
    
    return scenarios

def report_findings(suite_a_data, suite_b_data, improved_files, uncovered_scenarios):
    """Generate a comprehensive report on the findings"""
    # Calculate overall improvements
    line_improvement = suite_b_data['line_coverage'] - suite_a_data['line_coverage']
    branch_improvement = suite_b_data['branch_coverage'] - suite_a_data['branch_coverage']
    
    # Group scenarios by type
    scenario_types = {}
    for scenario in uncovered_scenarios:
        if scenario['scenario'] not in scenario_types:
            scenario_types[scenario['scenario']] = []
        scenario_types[scenario['scenario']].append(scenario)
    
    # Create the report
    report = [
        "# Code Coverage Analysis and Test Generation Report",
        "\n## Overall Coverage Metrics",
        "\n### Test Suite A (Original Tests)",
        f"- Line Coverage: {suite_a_data['line_coverage']:.2%}",
        f"- Branch Coverage: {suite_a_data['branch_coverage']:.2%}",
        "\n### Test Suite B (Generated Tests)",
        f"- Line Coverage: {suite_b_data['line_coverage']:.2%}",
        f"- Branch Coverage: {suite_b_data['branch_coverage']:.2%}",
        "\n### Improvement",
        f"- Line Coverage: {'+' if line_improvement >= 0 else ''}{line_improvement:.2%}",
        f"- Branch Coverage: {'+' if branch_improvement >= 0 else ''}{branch_improvement:.2%}",
        "\n## Files with Significant Improvement",
    ]
    
    if improved_files:
        for file_path, info in sorted(improved_files.items(), 
                                    key=lambda x: x[1]['improvement'], 
                                    reverse=True)[:10]:
            report.append(f"- {file_path}: {info['suite_a']:.2%} → {info['suite_b']:.2%} "
                         f"({'+' if info['improvement'] >= 0 else ''}{info['improvement']:.2%})")
    else:
        report.append("No files showed significant improvement.")
    
    report.append("\n## Uncovered Scenarios")
    report.append(f"Total uncovered scenarios found: {len(uncovered_scenarios)}")
    
    for scenario_type, scenarios in scenario_types.items():
        report.append(f"\n### {scenario_type} ({len(scenarios)} instances)")
        for i, scenario in enumerate(scenarios[:5]):  # Show top 5 examples of each type
            report.append(f"- {os.path.basename(scenario['file'])}:{scenario['line']} - `{scenario['code']}`")
        
        if len(scenarios) > 5:
            report.append(f"- ... and {len(scenarios) - 5} more instances")
    
    # Write the report to a file
    with open('coverage_report.md', 'w') as f:
        f.write('\n'.join(report))
    
    print("Report generated and saved to coverage_report.md")

def main():
    print("Comparing test suites and analyzing results...")
    
    # Load the coverage data for both test suites
    suite_a_data_raw, suite_b_data_raw = load_coverage_data()
    if not suite_a_data_raw or not suite_b_data_raw:
        print("Error: One or both coverage data files are missing or empty.")
        return
    
    # Analyze coverage for both test suites
    suite_a_data = analyze_coverage(suite_a_data_raw)
    suite_b_data = analyze_coverage(suite_b_data_raw)
    
    # Plot the comparison
    improved_files = plot_comparison(suite_a_data, suite_b_data)
    
    # Find uncovered scenarios
    uncovered_scenarios = find_uncovered_scenarios(suite_b_data_raw)
    
    # Generate a comprehensive report
    report_findings(suite_a_data, suite_b_data, improved_files, uncovered_scenarios)
    
    print("Analysis complete!")
    print(f"Line Coverage: {suite_a_data['line_coverage']:.2%} → {suite_b_data['line_coverage']:.2%}")
    print(f"Branch Coverage: {suite_a_data['branch_coverage']:.2%} → {suite_b_data['branch_coverage']:.2%}")

if __name__ == '__main__':
    main()
