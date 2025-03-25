#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import numpy as np
import os
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

def extract_coverage_metrics(data):
    if not data or 'totals' not in data:
        return {
            'line_coverage': 0,
            'branch_coverage': 0,
            'missing_lines': 0,
            'num_statements': 0
        }
    
    totals = data['totals']
    line_coverage = totals.get('covered_lines', 0) / totals.get('num_statements', 1) if totals.get('num_statements', 0) > 0 else 0
    branch_coverage = totals.get('percent_covered', 0) / 100 if isinstance(totals.get('percent_covered'), (int, float)) else 0
    
    return {
        'line_coverage': line_coverage,
        'branch_coverage': branch_coverage,
        'missing_lines': totals.get('missing_lines', 0),
        'num_statements': totals.get('num_statements', 0)
    }

def plot_overall_comparison(suite_a_metrics, suite_b_metrics, output_file='coverage_comparison.png'):
    """Create a bar chart comparing the two test suites"""
    # Data preparation
    metrics = ['Line Coverage', 'Branch Coverage']
    suite_a_values = [
        suite_a_metrics['line_coverage'] * 100,
        suite_a_metrics['branch_coverage'] * 100
    ]
    suite_b_values = [
        suite_b_metrics['line_coverage'] * 100,
        suite_b_metrics['branch_coverage'] * 100
    ]
    
    # Setup plot
    plt.figure(figsize=(12, 7))
    x = np.arange(len(metrics))
    width = 0.35
    
    # Create bars
    bars1 = plt.bar(x - width/2, suite_a_values, width, label='Test Suite A (Original)', color='#3498db')
    bars2 = plt.bar(x + width/2, suite_b_values, width, label='Test Suite B (Generated)', color='#e74c3c')
    
    # Add value labels
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    add_labels(bars1)
    add_labels(bars2)
    
    # Customize plot
    plt.ylabel('Coverage (%)', fontsize=14)
    plt.title('Test Suite A vs Test Suite B Coverage Comparison', fontsize=16, fontweight='bold')
    plt.xticks(x, metrics, fontsize=12)
    plt.ylim(0, 100)
    plt.legend(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add percentage difference annotations
    for i, (a, b) in enumerate(zip(suite_a_values, suite_b_values)):
        diff = b - a
        color = 'green' if diff >= 0 else 'red'
        plt.annotate(f"{diff:+.1f}%", 
                    xy=(i, max(a, b) + 5), 
                    ha='center', 
                    color=color,
                    fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", alpha=0.2, fc=color))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved overall comparison chart to {output_file}")

def analyze_file_coverage(suite_a_data, suite_b_data):
    """Analyze coverage at the file level"""
    file_metrics = {}
    
    # Process Suite A files
    for file_path, file_data in suite_a_data.get('files', {}).items():
        # Skip test files
        if '/tests/' in file_path or 'pynguin_tests' in file_path or file_path.endswith('__init__.py'):
            continue
        
        summary = file_data.get('summary', {})
        file_metrics[file_path] = {
            'suite_a': {
                'covered_lines': summary.get('covered_lines', 0),
                'num_statements': summary.get('num_statements', 0),
                'coverage': summary.get('covered_lines', 0) / summary.get('num_statements', 1) 
                           if summary.get('num_statements', 0) > 0 else 0
            }
        }
    
    # Process Suite B files
    for file_path, file_data in suite_b_data.get('files', {}).items():
        # Skip test files
        if '/tests/' in file_path or 'pynguin_tests' in file_path or file_path.endswith('__init__.py'):
            continue
        
        summary = file_data.get('summary', {})
        if file_path in file_metrics:
            file_metrics[file_path]['suite_b'] = {
                'covered_lines': summary.get('covered_lines', 0),
                'num_statements': summary.get('num_statements', 0),
                'coverage': summary.get('covered_lines', 0) / summary.get('num_statements', 1) 
                           if summary.get('num_statements', 0) > 0 else 0
            }
        else:
            file_metrics[file_path] = {
                'suite_b': {
                    'covered_lines': summary.get('covered_lines', 0),
                    'num_statements': summary.get('num_statements', 0),
                    'coverage': summary.get('covered_lines', 0) / summary.get('num_statements', 1) 
                               if summary.get('num_statements', 0) > 0 else 0
                }
            }
    
    # Calculate improvement for files present in both suites
    for file_path, metrics in file_metrics.items():
        if 'suite_a' in metrics and 'suite_b' in metrics:
            metrics['improvement'] = metrics['suite_b']['coverage'] - metrics['suite_a']['coverage']
    
    return file_metrics

def plot_file_improvements(file_metrics, output_file='file_improvements.png', top_n=15):
    """Create a horizontal bar chart showing files with the most improvement"""
    # Find files with improvement data
    improved_files = {file: data for file, data in file_metrics.items() 
                     if 'improvement' in data and data['improvement'] > 0}
    
    if not improved_files:
        print("No files showed coverage improvement")
        return
    
    # Sort by improvement and take top N
    sorted_files = sorted(improved_files.items(), key=lambda x: x[1]['improvement'], reverse=True)[:top_n]
    
    # Extract data for plotting
    file_names = [os.path.basename(file) for file, _ in sorted_files]
    improvements = [data['improvement'] * 100 for _, data in sorted_files]
    
    # Create horizontal bar chart
    plt.figure(figsize=(12, max(8, len(file_names) * 0.4)))
    bars = plt.barh(file_names, improvements, color='#2ecc71')
    
    # Add data labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                f'+{width:.1f}%', ha='left', va='center', fontweight='bold')
    
    # Customize plot
    plt.xlabel('Coverage Improvement (%)', fontsize=14)
    plt.title(f'Top {len(sorted_files)} Files With Most Coverage Improvement', fontsize=16, fontweight='bold')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved file improvement chart to {output_file}")

def plot_module_coverage(file_metrics, output_file='module_coverage.png'):
    """Plot coverage by module/package"""
    if not file_metrics:
        print("No file metrics available for module coverage analysis")
        return
    
    # Extract module names from file paths
    modules = {}
    for file_path, metrics in file_metrics.items():
        # Extract module from path (e.g., algorithms/arrays/...)
        parts = file_path.split('/')
        if len(parts) >= 2:
            module = parts[1]  # Assuming the pattern is 'algorithms/module/...'
            
            if module not in modules:
                modules[module] = {'suite_a': [], 'suite_b': []}
            
            # Store coverages for each suite
            if 'suite_a' in metrics:
                modules[module]['suite_a'].append(metrics['suite_a']['coverage'])
            
            if 'suite_b' in metrics:
                modules[module]['suite_b'].append(metrics['suite_b']['coverage'])
    
    # Calculate average coverage for each module
    module_coverage = {}
    for module, data in modules.items():
        module_coverage[module] = {
            'suite_a': np.mean(data['suite_a']) if data['suite_a'] else 0,
            'suite_b': np.mean(data['suite_b']) if data['suite_b'] else 0
        }
    
    # Filter out modules with no data and sort by name
    module_coverage = {k: v for k, v in module_coverage.items() if v['suite_a'] > 0 or v['suite_b'] > 0}
    module_coverage = dict(sorted(module_coverage.items()))
    
    if not module_coverage:
        print("No valid module coverage data available")
        return
    
    # Prepare data for plotting
    module_names = list(module_coverage.keys())
    suite_a_values = [data['suite_a'] * 100 for data in module_coverage.values()]
    suite_b_values = [data['suite_b'] * 100 for data in module_coverage.values()]
    
    # Create grouped bar chart
    plt.figure(figsize=(14, max(8, len(module_names) * 0.4)))
    
    x = np.arange(len(module_names))
    width = 0.35
    
    bars1 = plt.barh([i - width/2 for i in x], suite_a_values, width, label='Test Suite A', color='#3498db')
    bars2 = plt.barh([i + width/2 for i in x], suite_b_values, width, label='Test Suite B', color='#e74c3c')
    
    # Customize plot
    plt.ylabel('Module', fontsize=14)
    plt.xlabel('Average Coverage (%)', fontsize=14)
    plt.title('Module Coverage Comparison', fontsize=16, fontweight='bold')
    plt.yticks(x, module_names, fontsize=10)
    plt.xlim(0, 100)
    plt.legend(fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved module coverage chart to {output_file}")

def plot_coverage_distribution(file_metrics, output_file='coverage_distribution.png'):
    """Create histograms showing the distribution of file coverage percentages"""
    if not file_metrics:
        print("No file metrics available for coverage distribution analysis")
        return
    
    # Extract coverage percentages
    suite_a_coverage = [metrics['suite_a']['coverage'] * 100 
                       for _, metrics in file_metrics.items() 
                       if 'suite_a' in metrics]
    
    suite_b_coverage = [metrics['suite_b']['coverage'] * 100 
                       for _, metrics in file_metrics.items() 
                       if 'suite_b' in metrics]
    
    if not suite_a_coverage and not suite_b_coverage:
        print("No coverage data available for distribution analysis")
        return
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    # Suite A histogram
    if suite_a_coverage:
        bins = np.linspace(0, 100, 11)  # 0, 10, 20, ..., 100
        ax1.hist(suite_a_coverage, bins=bins, alpha=0.7, color='#3498db', edgecolor='black')
        ax1.set_title('Test Suite A Coverage Distribution', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Coverage Percentage', fontsize=12)
        ax1.set_ylabel('Number of Files', fontsize=12)
        ax1.set_xlim(0, 100)
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add average line
        avg_a = np.mean(suite_a_coverage)
        ax1.axvline(avg_a, color='red', linestyle='--', linewidth=2)
        ax1.text(avg_a + 1, ax1.get_ylim()[1] * 0.9, f'Avg: {avg_a:.1f}%', 
                color='red', fontweight='bold')
    
    # Suite B histogram
    if suite_b_coverage:
        bins = np.linspace(0, 100, 11)  # 0, 10, 20, ..., 100
        ax2.hist(suite_b_coverage, bins=bins, alpha=0.7, color='#e74c3c', edgecolor='black')
        ax2.set_title('Test Suite B Coverage Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Coverage Percentage', fontsize=12)
        ax2.set_ylabel('Number of Files', fontsize=12)
        ax2.set_xlim(0, 100)
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add average line
        avg_b = np.mean(suite_b_coverage)
        ax2.axvline(avg_b, color='red', linestyle='--', linewidth=2)
        ax2.text(avg_b + 1, ax2.get_ylim()[1] * 0.9, f'Avg: {avg_b:.1f}%', 
                color='red', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved coverage distribution chart to {output_file}")

def analyze_pynguin_results(output_file='pynguin_success_rate.png'):
    """Analyze Pynguin results from output.txt to create success/failure visualization"""
    try:
        with open('output.txt', 'r') as f:
            output_content = f.read()
    except FileNotFoundError:
        print("Warning: output.txt not found")
        return
    
    # Count successful and failed test generations
    successful_count = output_content.count("Successfully generated tests for")
    processing_count = output_content.count("Processing file")
    
    if processing_count == 0:
        print("No processing records found in output.txt")
        return
    
    # Calculate success rate
    success_rate = successful_count / processing_count
    failure_rate = 1 - success_rate
    
    # Create a pie chart
    plt.figure(figsize=(10, 7))
    labels = ['Success', 'Failure']
    sizes = [success_rate * 100, failure_rate * 100]
    colors = ['#2ecc71', '#e74c3c']
    explode = (0.1, 0)  # explode the 1st slice (Success)
    
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct='%1.1f%%', shadow=True, startangle=140, textprops={'fontsize': 14})
    
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
    plt.title('Pynguin Test Generation Success Rate', fontsize=16, fontweight='bold')
    
    # Add absolute numbers
    plt.annotate(f"Total: {processing_count} files\nSuccessful: {successful_count}", 
                xy=(0, 0), 
                xytext=(0.9, 0.1),
                xycoords='figure fraction',
                textcoords='figure fraction',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved Pynguin success rate chart to {output_file}")

def main():
    os.makedirs('visualizations', exist_ok=True)
    suite_a_data, suite_b_data = load_coverage_data()
    if not suite_a_data or not suite_b_data:
        print("Error: Coverage data is missing or empty.")
        return
    
    # Extract coverage metrics
    suite_a_metrics = extract_coverage_metrics(suite_a_data)
    suite_b_metrics = extract_coverage_metrics(suite_b_data)
    
    # 1. Overall coverage comparison
    plot_overall_comparison(suite_a_metrics, suite_b_metrics, 'visualizations/overall_coverage_comparison.png')
    
    # 2. Analyze file-level coverage
    file_metrics = analyze_file_coverage(suite_a_data, suite_b_data)
    
    # 3. File improvements
    plot_file_improvements(file_metrics, 'visualizations/file_improvements.png')
    
    # 4. Module coverage
    plot_module_coverage(file_metrics, 'visualizations/module_coverage.png')
    
    # 5. Coverage distribution
    plot_coverage_distribution(file_metrics, 'visualizations/coverage_distribution.png')
    
    # 6. Pynguin success rate
    analyze_pynguin_results('visualizations/pynguin_success_rate.png')
    
    print("All visualizations generated successfully!")

if __name__ == "__main__":
    main()
