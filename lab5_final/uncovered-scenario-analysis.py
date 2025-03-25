#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import re
import pandas as pd
import seaborn as sns
from collections import defaultdict, Counter
from pathlib import Path

def load_coverage_data(suite_a_file='results/coverage.suite_a.json', 
                      suite_b_file='results/coverage.suite_b.json'):
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

def find_uncovered_scenarios(data):
    scenarios = []
    
    for file_path, file_data in data.get('files', {}).items():
        # Skip test files
        if '/tests/' in file_path or 'pynguin_tests' in file_path or file_path.endswith('__init__.py'):
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
                            
                            # Skip empty lines and comments
                            if not line or line.startswith('#'):
                                continue
                            
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
                            
                            # Look for class/method definitions
                            elif re.search(r'def |class ', line):
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Function/class definition'
                                })
                            
                            # Look for loops and iterations
                            elif re.search(r'for |while |continue|break', line):
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Loop/iteration'
                                })
                            
                            # Look for return statements
                            elif re.search(r'return ', line):
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Return statement'
                                })
                            
                            # Default case
                            else:
                                scenarios.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'code': line,
                                    'scenario': 'Other'
                                })
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
    
    return scenarios

def plot_scenario_distribution(scenarios, output_file='uncovered_scenarios_dist.png'):
    if not scenarios:
        print("No uncovered scenarios found")
        return
    
    # Count scenarios by type
    scenario_counts = Counter(scenario['scenario'] for scenario in scenarios)
    
    # Sort by count in descending order
    sorted_scenarios = dict(sorted(scenario_counts.items(), key=lambda x: x[1], reverse=True))
    
    plt.figure(figsize=(12, 8))
    bars = plt.bar(sorted_scenarios.keys(), sorted_scenarios.values(), color='#8e44ad')
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height}', ha='center', va='bottom', fontweight='bold')

    plt.xlabel('Scenario Category', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.title('Distribution of Uncovered Scenarios', fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved scenario distribution chart to {output_file}")

def plot_module_scenario_heatmap(scenarios, output_file='module_scenario_heatmap.png'):
    if not scenarios:
        print("No uncovered scenarios found")
        return
    
    # Extract module from file path
    for scenario in scenarios:
        file_path = scenario['file']
        match = re.search(r'algorithms/([^/]+)', file_path)
        if match:
            scenario['module'] = match.group(1)
        else:
            scenario['module'] = 'other'
    
    module_scenario_counts = defaultdict(lambda: defaultdict(int))
    for scenario in scenarios:
        module = scenario['module']
        scenario_type = scenario['scenario']
        module_scenario_counts[module][scenario_type] += 1
    
    modules = sorted(module_scenario_counts.keys())
    scenario_types = sorted(set(scenario['scenario'] for scenario in scenarios))
    data = []
    for module in modules:
        for scenario_type in scenario_types:
            count = module_scenario_counts[module][scenario_type]
            data.append({
                'Module': module,
                'Scenario Type': scenario_type,
                'Count': count
            })
    
    df = pd.DataFrame(data)
    

    pivot_table = df.pivot(index='Module', columns='Scenario Type', values='Count')
    pivot_table = pivot_table.fillna(0)
    plt.figure(figsize=(14, max(8, len(modules) * 0.4)))    
    heatmap = sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlOrRd',
                         linewidths=0.5, cbar_kws={'label': 'Uncovered Cases'})
    plt.title('Uncovered Scenarios by Module and Type', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved module-scenario heatmap to {output_file}")

def plot_complex_scenarios(scenarios, output_file='complex_scenarios.png'):
    complex_categories = ['Complex logic', 'Boundary condition', 'Error handling']
    complex_scenarios = [s for s in scenarios if s['scenario'] in complex_categories]
    if not complex_scenarios:
        print("No complex scenarios found")
        return
    
    module_complex_counts = defaultdict(lambda: defaultdict(int))
    for scenario in complex_scenarios:
        module = scenario.get('module', 'unknown')
        category = scenario['scenario']
        module_complex_counts[module][category] += 1
    
    # Prepare data for grouped bar chart:
    modules = sorted(module_complex_counts.keys())
    categories = complex_categories
    plt.figure(figsize=(14, max(8, len(modules) * 0.4)))
    width = 0.25
    x = np.arange(len(modules))
    for i, category in enumerate(categories):
        counts = [module_complex_counts[module][category] for module in modules]
        plt.bar(x + i*width, counts, width, label=category, 
               alpha=0.8, edgecolor='black', linewidth=1)
    plt.xlabel('Module', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.title('Distribution of Complex Uncovered Scenarios by Module', fontsize=16, fontweight='bold')
    plt.xticks(x + width, modules, rotation=45, ha='right')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved complex scenarios chart to {output_file}")

def generate_examples_report(scenarios, output_file='uncovered_scenarios_examples.md'):
    if not scenarios:
        print("No uncovered scenarios found")
        return
    
    # Group scenarios by type
    scenario_types = defaultdict(list)
    for scenario in scenarios:
        scenario_types[scenario['scenario']].append(scenario)
    report = ["# Uncovered Scenarios Analysis", 
              "\nThis report provides examples of code lines that were not covered by the test suites.\n"]
    for scenario_type, examples in sorted(scenario_types.items(), key=lambda x: len(x[1]), reverse=True):
        report.append(f"## {scenario_type} ({len(examples)} instances)")
        report.append("\nExample uncovered code lines:")
        report.append("```python")
        for i, example in enumerate(examples[:10]):
            file_name = os.path.basename(example['file'])
            report.append(f"# From {file_name}:{example['line']}")
            report.append(example['code'])
            if i < len(examples[:10]) - 1:
                report.append("")
        
        report.append("```")
        if len(examples) > 10:
            report.append(f"\n*And {len(examples) - 10} more instances.*")
        report.append("\n")
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))
    print(f"Generated uncovered scenarios report at {output_file}")

def plot_improvement_by_scenario(suite_a_scenarios, suite_b_scenarios, output_file='scenario_improvement.png'):
    """Visualize the improvement from Test Suite A to Test Suite B by scenario type"""
    if not suite_a_scenarios or not suite_b_scenarios:
        print("Missing scenario data for one or both test suites")
        return
    
    # Count scenarios by type for each suite
    suite_a_counts = Counter(scenario['scenario'] for scenario in suite_a_scenarios)
    suite_b_counts = Counter(scenario['scenario'] for scenario in suite_b_scenarios)
    
    # Get all unique scenario types
    all_scenario_types = sorted(set(suite_a_counts.keys()) | set(suite_b_counts.keys()))
    
    # Calculate improvements
    improvements = []
    for scenario_type in all_scenario_types:
        count_a = suite_a_counts.get(scenario_type, 0)
        count_b = suite_b_counts.get(scenario_type, 0)
        
        # Only include if there's an improvement
        if count_a > count_b:
            improvements.append({
                'scenario': scenario_type,
                'improvement': count_a - count_b,
                'percent': (count_a - count_b) / count_a * 100 if count_a > 0 else 0
            })
    
    # Sort by absolute improvement
    improvements = sorted(improvements, key=lambda x: x['improvement'], reverse=True)
    
    if not improvements:
        print("No improvements found in scenario coverage")
        return
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12), gridspec_kw={'height_ratios': [2, 1]})
    scenarios = [item['scenario'] for item in improvements]
    abs_improvements = [item['improvement'] for item in improvements]
    bars1 = ax1.bar(scenarios, abs_improvements, color='#3498db')
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height}', ha='center', va='bottom', fontweight='bold')
    
    ax1.set_title('Absolute Reduction in Uncovered Scenarios', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Number of Scenarios Fixed', fontsize=14)
    ax1.set_xticklabels([])  # Hide x labels for top plot
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Plot percentage improvement
    pct_improvements = [item['percent'] for item in improvements]
    
    bars2 = ax2.bar(scenarios, pct_improvements, color='#2ecc71')
    
    # Add data labels
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    ax2.set_title('Percentage Reduction in Uncovered Scenarios', fontsize=16, fontweight='bold')
    ax2.set_ylabel('Percentage Improved', fontsize=14)
    ax2.set_xticks(range(len(scenarios)))
    ax2.set_xticklabels(scenarios, rotation=45, ha='right')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved scenario improvement chart to {output_file}")

def main():
    os.makedirs('visualizations', exist_ok=True)
    suite_a_data, suite_b_data = load_coverage_data()
    if not suite_a_data or not suite_b_data:
        print("Error: Coverage data is missing or empty.")
        return
    suite_a_scenarios = find_uncovered_scenarios(suite_a_data)
    suite_b_scenarios = find_uncovered_scenarios(suite_b_data)
    print(f"Found {len(suite_a_scenarios)} uncovered scenarios in Test Suite A")
    print(f"Found {len(suite_b_scenarios)} uncovered scenarios in Test Suite B")
    
    # Generate visualizations for Test Suite B (most relevant for final analysis)
    plot_scenario_distribution(suite_b_scenarios, 'visualizations/uncovered_scenarios_dist.png')
    plot_module_scenario_heatmap(suite_b_scenarios, 'visualizations/module_scenario_heatmap.png')
    plot_complex_scenarios(suite_b_scenarios, 'visualizations/complex_scenarios.png')
    
    # Generate improvement visualization (Suite A to Suite B)
    plot_improvement_by_scenario(suite_a_scenarios, suite_b_scenarios, 
                               'visualizations/scenario_improvement.png')
    
    # Generate example report
    generate_examples_report(suite_b_scenarios, 'visualizations/uncovered_scenarios_examples.md')
    
    print("All uncovered scenario visualizations generated successfully!")

if __name__ == "__main__":
    main()
