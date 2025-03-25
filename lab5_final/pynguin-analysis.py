#!/usr/bin/env python3
import re
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict, Counter
import pandas as pd
import seaborn as sns

def parse_output_file(output_file='output.txt'):
    try:
        with open(output_file, 'r') as f:
            output_content = f.read()
    except FileNotFoundError:
        print(f"Warning: {output_file} not found")
        return None
    
    # Extract file processing information
    processing_pattern = re.compile(r"Processing file (\d+)/(\d+): ([\w./]+)")
    processing_matches = processing_pattern.findall(output_content)
    
    # Extract success/failure information
    success_pattern = re.compile(r"Successfully generated tests for ([\w./]+)")
    success_matches = success_pattern.findall(output_content)
    
    # Extract timeout/termination information
    timeout_pattern = re.compile(r"Pynguin is taking too long for ([\w./]+), terminating")
    timeout_matches = timeout_pattern.findall(output_content)
    
    # Extract total statistics
    total_pattern = re.compile(r"Test generation complete: (\d+)/(\d+) files processed successfully")
    total_match = total_pattern.search(output_content)
    
    total_success = int(total_match.group(1)) if total_match else len(success_matches)
    total_files = int(total_match.group(2)) if total_match else len(processing_matches)
    
    # Compile the results
    results = {
        'total_files': total_files,
        'successful_files': total_success,
        'failed_files': total_files - total_success,
        'success_rate': total_success / total_files if total_files > 0 else 0,
        'timeout_files': len(timeout_matches),
        'processing_details': processing_matches,
        'successful_modules': [m.split('.')[1] if len(m.split('.')) > 1 else m for m in success_matches],
        'timeout_modules': [m.split('.')[1] if len(m.split('.')) > 1 else m for m in timeout_matches]
    }
    
    return results

def plot_success_failure_pie(results, output_file='pynguin_success_pie.png'):
    if not results:
        print("No results data available")
        return
    
    plt.figure(figsize=(10, 8))
    
    # Data for pie chart
    labels = ['Successful', 'Failed']
    sizes = [results['successful_files'], results['failed_files']]
    explode = (0.1, 0)  # Explode the successful slice
    colors = ['#2ecc71', '#e74c3c']
    
    # Create pie chart
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 14})
    
    plt.axis('equal')
    plt.title('Pynguin Test Generation Success vs. Failure', fontsize=16, fontweight='bold')
    plt.annotate(f"Total files: {results['total_files']}\n"
                f"Successful: {results['successful_files']}\n"
                f"Failed: {results['failed_files']}", 
                xy=(0, 0), 
                xytext=(0.85, 0.15),
                xycoords='figure fraction',
                textcoords='figure fraction',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved Pynguin success/failure pie chart to {output_file}")

def plot_module_success_rate(results, output_file='module_success_rate.png'):
    """Create a bar chart showing success rate by module"""
    if not results or not results['successful_modules']:
        print("No success data available by module")
        return
    
    # Count successes by module
    module_successes = Counter(results['successful_modules'])
    
    # Count timeouts by module (if available)
    module_timeouts = Counter(results.get('timeout_modules', []))
    
    # Calculate total attempts by module
    module_attempts = defaultdict(int)
    for module in set(module_successes.keys()) | set(module_timeouts.keys()):
        module_attempts[module] = module_successes.get(module, 0) + module_timeouts.get(module, 0)
    
    # Calculate success rate
    module_success_rates = {}
    for module, attempts in module_attempts.items():
        module_success_rates[module] = module_successes.get(module, 0) / attempts
    
    # Sort modules by success rate
    sorted_modules = sorted(module_success_rates.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare data for plotting
    modules = [m[0] for m in sorted_modules]
    success_rates = [m[1] * 100 for m in sorted_modules]
    
    # Create horizontal bar chart
    plt.figure(figsize=(12, max(8, len(modules) * 0.3)))
    
    bars = plt.barh(modules, success_rates, color=plt.cm.viridis(np.array(success_rates)/100))
    
    # Add data labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}%', ha='left', va='center', fontweight='bold')
    
    # Customize plot
    plt.xlabel('Success Rate (%)', fontsize=14)
    plt.title('Pynguin Test Generation Success Rate by Module', fontsize=16, fontweight='bold')
    plt.xlim(0, 100)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved module success rate chart to {output_file}")

def plot_time_series_generation(results, output_file='generation_time_series.png'):
    """Create a time series visualization of the test generation process"""
    if not results or not results['processing_details']:
        print("No processing details available")
        return
    
    # Extract data from processing details
    indices = []
    file_paths = []
    successes = []
    
    successful_files = set(results.get('successful_modules', []))
    
    for idx, total, file_path in results['processing_details']:
        module_name = file_path.split('/')[-1].replace('.py', '')
        indices.append(int(idx))
        file_paths.append(module_name)
        
        # Check if this file was successful
        if module_name in successful_files or file_path in successful_files:
            successes.append(1)
        else:
            successes.append(0)
    
    # Create the time series plot
    plt.figure(figsize=(15, 8))
    
    # Plot success/failure as points
    successful_indices = [i for i, s in zip(indices, successes) if s == 1]
    failed_indices = [i for i, s in zip(indices, successes) if s == 0]
    
    plt.scatter(successful_indices, [1] * len(successful_indices), 
               color='green', label='Success', s=100, marker='o')
    plt.scatter(failed_indices, [0] * len(failed_indices), 
               color='red', label='Failure', s=100, marker='x')
    
    # Calculate running success rate
    running_success = np.cumsum(successes)
    running_rate = [running_success[i] / (i+1) * 100 for i in range(len(running_success))]
    
    # Plot running success rate
    ax1 = plt.gca()
    ax2 = ax1.twinx()
    ax2.plot(indices, running_rate, 'b-', label='Running Success Rate')
    
    # Customize plot
    ax1.set_xlabel('File Index', fontsize=14)
    ax1.set_ylabel('Generation Result', fontsize=14)
    ax2.set_ylabel('Running Success Rate (%)', fontsize=14, color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    plt.title('Pynguin Test Generation Time Series', fontsize=16, fontweight='bold')
    
    # Add a legend for the first axis
    ax1.legend(loc='upper left')
    
    # Mark every 10th file name on x-axis
    step = max(1, len(indices) // 20)  # Show at most 20 file names
    plt.xticks(indices[::step], file_paths[::step], rotation=90)
    
    # Add horizontal lines at success/failure levels
    ax1.axhline(y=1, color='green', alpha=0.3, linestyle='--')
    ax1.axhline(y=0, color='red', alpha=0.3, linestyle='--')
    
    # Set y-axis limits for first axis
    ax1.set_ylim(-0.5, 1.5)
    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(['Failure', 'Success'])
    
    # Set y-axis limits for second axis
    ax2.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved generation time series chart to {output_file}")

def plot_file_type_success_rate(results, output_file='file_type_success_rate.png'):
    """Analyze success rate by file type/complexity"""
    if not results or not results['processing_details']:
        print("No processing details available")
        return
    
    # Extract file extensions and suffixes as indicators of file type
    file_types = defaultdict(lambda: {'success': 0, 'failure': 0})
    
    # Process successful files
    for file_path in results.get('successful_modules', []):
        # Extract file suffix (last part of path)
        parts = file_path.split('_')
        suffix = parts[-1] if parts else 'unknown'
        file_types[suffix]['success'] += 1
    
    # Process timeout/failed files
    for file_path in results.get('timeout_modules', []):
        # Extract file suffix
        parts = file_path.split('_')
        suffix = parts[-1] if parts else 'unknown'
        file_types[suffix]['failure'] += 1
    
    # Calculate success rates
    success_rates = {}
    for suffix, counts in file_types.items():
        total = counts['success'] + counts['failure']
        if total > 0:
            success_rates[suffix] = (counts['success'] / total * 100, total)
    
    # Filter out types with very few files
    min_files = 2
    success_rates = {k: v for k, v in success_rates.items() if v[1] >= min_files}
    
    # Sort by success rate
    sorted_types = sorted(success_rates.items(), key=lambda x: x[1][0], reverse=True)
    
    if not sorted_types:
        print("Not enough data to analyze file types")
        return
    
    # Prepare data for plotting
    suffixes = [t[0] for t in sorted_types]
    rates = [t[1][0] for t in sorted_types]
    counts = [t[1][1] for t in sorted_types]
    
    # Create horizontal bar chart
    plt.figure(figsize=(12, max(8, len(suffixes) * 0.4)))
    
    bars = plt.barh(suffixes, rates, color=plt.cm.viridis(np.array(rates)/100))
    
    # Add data labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}% (n={counts[i]})', ha='left', va='center', fontweight='bold')
    
    # Customize plot
    plt.xlabel('Success Rate (%)', fontsize=14)
    plt.title('Pynguin Test Generation Success Rate by File Type', fontsize=16, fontweight='bold')
    plt.xlim(0, 100)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved file type success rate chart to {output_file}")

def plot_success_factor_heatmap(results, output_file='success_factor_heatmap.png'):
    """Create a heatmap visualization of success factors"""
    if not results or not results['processing_details']:
        print("No processing details available")
        return
    
    # Define potential success factors (keywords in file names)
    success_factors = ['sort', 'search', 'tree', 'list', 'stack', 'queue', 'heap', 
                      'graph', 'array', 'string', 'hash', 'matrix']
    
    # Initialize counts
    factor_data = {factor: {'success': 0, 'failure': 0} for factor in success_factors}
    
    # Process successful files
    for file_path in results.get('successful_modules', []):
        file_path_lower = file_path.lower()
        for factor in success_factors:
            if factor in file_path_lower:
                factor_data[factor]['success'] += 1
    
    # Process timeout/failed files
    for file_path in results.get('timeout_modules', []):
        file_path_lower = file_path.lower()
        for factor in success_factors:
            if factor in file_path_lower:
                factor_data[factor]['failure'] += 1
    
    # Calculate success rates and total counts
    success_rates = []
    total_counts = []
    
    for factor, counts in factor_data.items():
        total = counts['success'] + counts['failure']
        if total > 0:
            success_rates.append(counts['success'] / total * 100)
            total_counts.append(total)
        else:
            success_rates.append(0)
            total_counts.append(0)
    
    # Create a DataFrame for the heatmap
    df = pd.DataFrame({
        'Factor': success_factors,
        'Success Rate (%)': success_rates,
        'Total Count': total_counts
    })
    
    # Sort by success rate
    df = df.sort_values('Success Rate (%)', ascending=False)
    
    # Create heatmap data
    heatmap_data = pd.pivot_table(
        pd.DataFrame({
            'Factor': df['Factor'],
            'Category': ['Success Rate'] * len(df),
            'Value': df['Success Rate (%)']
        }),
        values='Value',
        index='Factor',
        columns='Category'
    )
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), 
                                  gridspec_kw={'height_ratios': [2, 1]})
    
    # Create heatmap
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlGnBu', 
               linewidths=0.5, cbar=True, ax=ax1)
    
    ax1.set_title('Test Generation Success Rate by Algorithm Type (%)', 
                 fontsize=16, fontweight='bold')
    
    # Create bar chart of counts
    bars = ax2.bar(df['Factor'], df['Total Count'], color='skyblue')
    
    # Add count labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height}', ha='center', va='bottom', fontweight='bold')
    
    ax2.set_title('Number of Files by Algorithm Type', fontsize=16, fontweight='bold')
    ax2.set_ylabel('Count', fontsize=14)
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved success factor heatmap to {output_file}")

def main():
    os.makedirs('visualizations', exist_ok=True)
    
    # Parse the output file
    results = parse_output_file('output.txt')
    
    if not results:
        print("Error: Could not parse output file.")
        return
    
    # Generate visualizations
    plot_success_failure_pie(results, 'visualizations/pynguin_success_pie.png')
    plot_module_success_rate(results, 'visualizations/module_success_rate.png')
    plot_time_series_generation(results, 'visualizations/generation_time_series.png')
    plot_file_type_success_rate(results, 'visualizations/file_type_success_rate.png')
    plot_success_factor_heatmap(results, 'visualizations/success_factor_heatmap.png')
    
    print("All Pynguin analysis visualizations generated successfully!")

if __name__ == "__main__":
    main()