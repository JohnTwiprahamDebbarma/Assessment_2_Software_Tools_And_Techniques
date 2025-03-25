#!/usr/bin/env python3
import json
import os
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

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

def extract_hierarchical_coverage(coverage_data):
    """Extract hierarchical coverage data for sunburst chart"""
    hierarchy = {}
    
    for file_path, file_data in coverage_data.get('files', {}).items():
        # Skip test files
        if '/tests/' in file_path or 'pynguin_tests' in file_path or file_path.endswith('__init__.py'):
            continue
        
        # Parse the path (e.g., algorithms/arrays/array_file.py)
        parts = file_path.split('/')
        if len(parts) >= 3 and parts[0] == 'algorithms':
            module = parts[1]
            submodule = parts[2].replace('.py', '')
            
            # Get coverage metrics
            summary = file_data.get('summary', {})
            covered_lines = summary.get('covered_lines', 0)
            total_lines = summary.get('num_statements', 0)
            coverage_pct = covered_lines / total_lines * 100 if total_lines > 0 else 0
            
            # Build hierarchy
            if module not in hierarchy:
                hierarchy[module] = {'files': {}, 'total_lines': 0, 'covered_lines': 0}
            
            hierarchy[module]['files'][submodule] = {
                'total_lines': total_lines,
                'covered_lines': covered_lines,
                'coverage_pct': coverage_pct
            }
            
            hierarchy[module]['total_lines'] += total_lines
            hierarchy[module]['covered_lines'] += covered_lines
    
    # Calculate coverage percentages for modules
    for module, data in hierarchy.items():
        if data['total_lines'] > 0:
            data['coverage_pct'] = data['covered_lines'] / data['total_lines'] * 100
        else:
            data['coverage_pct'] = 0
    
    return hierarchy

def create_sunburst_data(hierarchy_a, hierarchy_b=None):
    """Create data for sunburst chart"""
    # Prepare data structures for plotting
    labels = ["algorithms"]  # Root
    parents = [""]  # Root has no parent
    values = [100]  # Arbitrary value for root
    coverage_a = [0]  # Will be calculated based on children
    coverage_b = [0] if hierarchy_b else None  # Only if suite B is provided
    
    # Total lines for root calculation
    total_lines_a = sum(data['total_lines'] for data in hierarchy_a.values())
    covered_lines_a = sum(data['covered_lines'] for data in hierarchy_a.values())
    root_coverage_a = covered_lines_a / total_lines_a * 100 if total_lines_a > 0 else 0
    coverage_a[0] = root_coverage_a
    
    if hierarchy_b:
        total_lines_b = sum(data['total_lines'] for data in hierarchy_b.values())
        covered_lines_b = sum(data['covered_lines'] for data in hierarchy_b.values())
        root_coverage_b = covered_lines_b / total_lines_b * 100 if total_lines_b > 0 else 0
        coverage_b[0] = root_coverage_b
    
    # Add modules
    all_modules = sorted(set(hierarchy_a.keys()) | (set(hierarchy_b.keys()) if hierarchy_b else set()))
    
    for module in all_modules:
        labels.append(module)
        parents.append("algorithms")
        
        # Get module data for suite A
        module_data_a = hierarchy_a.get(module, {'total_lines': 0, 'coverage_pct': 0})
        values.append(module_data_a['total_lines'])
        coverage_a.append(module_data_a['coverage_pct'])
        
        if hierarchy_b:
            # Get module data for suite B
            module_data_b = hierarchy_b.get(module, {'total_lines': 0, 'coverage_pct': 0})
            coverage_b.append(module_data_b['coverage_pct'])
        
        # Add files for this module
        module_files_a = module_data_a.get('files', {})
        module_files_b = hierarchy_b.get(module, {}).get('files', {}) if hierarchy_b else {}
        all_files = sorted(set(module_files_a.keys()) | set(module_files_b.keys()))
        
        for file in all_files:
            labels.append(file)
            parents.append(module)
            
            # Get file data for suite A
            file_data_a = module_files_a.get(file, {'total_lines': 0, 'coverage_pct': 0})
            values.append(file_data_a['total_lines'])
            coverage_a.append(file_data_a['coverage_pct'])
            
            if hierarchy_b:
                # Get file data for suite B
                file_data_b = module_files_b.get(file, {'total_lines': 0, 'coverage_pct': 0})
                coverage_b.append(file_data_b['coverage_pct'])
    
    # Prepare result
    result = {
        'labels': labels,
        'parents': parents,
        'values': values,
        'coverage_a': coverage_a
    }
    
    if hierarchy_b:
        result['coverage_b'] = coverage_b
    
    return result

def create_plotly_sunburst(sunburst_data, output_file='coverage_sunburst.html'):
    """Create interactive sunburst chart using Plotly"""
    # Determine if we have both test suites
    has_both_suites = 'coverage_b' in sunburst_data
    
    # Create traces for each test suite
    fig = go.Figure()
    
    # Color scale function
    def get_color(coverage):
        if coverage < 20:
            return 'rgb(165, 0, 38)'  # Dark red
        elif coverage < 40:
            return 'rgb(215, 48, 39)'  # Red
        elif coverage < 60:
            return 'rgb(244, 109, 67)'  # Orange
        elif coverage < 80:
            return 'rgb(253, 174, 97)'  # Light orange
        else:
            return 'rgb(116, 196, 118)'  # Green
    
    # Convert coverage percentages to colors
    colors_a = [get_color(cov) for cov in sunburst_data['coverage_a']]
    
    if has_both_suites:
        # Create figure with subplots
        from plotly.subplots import make_subplots
        fig = make_subplots(1, 2, specs=[[{'type': 'domain'}, {'type': 'domain'}]])
        
        # Test Suite A Sunburst
        fig.add_trace(go.Sunburst(
            labels=sunburst_data['labels'],
            parents=sunburst_data['parents'],
            values=sunburst_data['values'],
            marker=dict(colors=colors_a),
            hovertemplate='<b>%{label}</b><br>Coverage: %{customdata:.1f}%<br>Lines: %{value}<extra></extra>',
            customdata=sunburst_data['coverage_a'],
            name='Test Suite A',
            domain=dict(column=0)
        ), 1, 1)
        
        # Test Suite B Sunburst
        colors_b = [get_color(cov) for cov in sunburst_data['coverage_b']]
        fig.add_trace(go.Sunburst(
            labels=sunburst_data['labels'],
            parents=sunburst_data['parents'],
            values=sunburst_data['values'],
            marker=dict(colors=colors_b),
            hovertemplate='<b>%{label}</b><br>Coverage: %{customdata:.1f}%<br>Lines: %{value}<extra></extra>',
            customdata=sunburst_data['coverage_b'],
            name='Test Suite B',
            domain=dict(column=1)
        ), 1, 2)
        
        # Update figure layout
        fig.update_layout(
            title_text='Code Coverage Comparison: Test Suite A vs. Test Suite B',
            grid=dict(columns=2, rows=1),
            annotations=[
                dict(text="Test Suite A", x=0.20, y=1.0, showarrow=False, font_size=16),
                dict(text="Test Suite B", x=0.80, y=1.0, showarrow=False, font_size=16)
            ]
        )
    else:
        # Single sunburst for Test Suite A only
        fig.add_trace(go.Sunburst(
            labels=sunburst_data['labels'],
            parents=sunburst_data['parents'],
            values=sunburst_data['values'],
            marker=dict(colors=colors_a),
            hovertemplate='<b>%{label}</b><br>Coverage: %{customdata:.1f}%<br>Lines: %{value}<extra></extra>',
            customdata=sunburst_data['coverage_a'],
            name='Test Suite A'
        ))
        
        # Update figure layout
        fig.update_layout(
            title_text='Code Coverage: Test Suite A'
        )
    
    # Common layout settings
    fig.update_layout(
        autosize=True,
        margin=dict(t=60, l=0, r=0, b=0),
        font=dict(size=12),
        height=800,
        width=1200
    )
    
    # Save to HTML file
    fig.write_html(output_file)
    print(f"Saved interactive sunburst chart to {output_file}")
    
    return fig

def create_matplotlib_sunburst(sunburst_data, output_file='coverage_sunburst.png'):
    """Create static sunburst chart using Matplotlib (simpler version)"""
    # This is a simplified version since matplotlib doesn't have built-in sunburst
    # We'll create a nested pie chart instead
    
    # Group data by level
    root = {'name': 'algorithms', 'coverage': sunburst_data['coverage_a'][0], 'children': {}}
    
    for i in range(1, len(sunburst_data['labels'])):
        label = sunburst_data['labels'][i]
        parent = sunburst_data['parents'][i]
        value = sunburst_data['values'][i]
        coverage = sunburst_data['coverage_a'][i]
        
        if parent == 'algorithms':
            # This is a module
            root['children'][label] = {
                'name': label,
                'coverage': coverage,
                'value': value,
                'children': {}
            }
        else:
            # This is a file
            if parent in root['children']:
                root['children'][parent]['children'][label] = {
                    'name': label,
                    'coverage': coverage,
                    'value': value
                }
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 14))
    
    # Color map
    cmap = plt.cm.RdYlGn
    
    # Draw module level (outer ring)
    modules = list(root['children'].values())
    module_sizes = [m['value'] for m in modules]
    module_colors = [cmap(m['coverage']/100) for m in modules]
    module_labels = [f"{m['name']}\n({m['coverage']:.1f}%)" for m in modules]
    
    # Draw outer ring (modules)
    ax.pie(module_sizes, radius=1, colors=module_colors, labels=module_labels,
          wedgeprops=dict(width=0.3, edgecolor='w'), labeldistance=1.05,
          textprops={'fontsize': 10, 'fontweight': 'bold'})
    
    # Draw inner ring (files - simplified, no labels due to potential clutter)
    file_sizes = []
    file_colors = []
    
    # Group files by module to maintain the same ordering
    for module in modules:
        for file in module['children'].values():
            file_sizes.append(file['value'])
            file_colors.append(cmap(file['coverage']/100))
    
    if file_sizes:
        ax.pie(file_sizes, radius=0.7, colors=file_colors,
              wedgeprops=dict(width=0.3, edgecolor='w'), labels=None)
    
    # Draw center circle for the root
    ax.pie([1], radius=0.4, colors=[cmap(root['coverage']/100)],
          wedgeprops=dict(width=0.4, edgecolor='w'), labels=None)
    
    # Add root label in center
    ax.text(0, 0, f"algorithms\n({root['coverage']:.1f}%)", ha='center', va='center',
           fontsize=14, fontweight='bold')
    
    # Add title
    plt.title('Code Coverage Sunburst Chart (Test Suite A)', fontsize=16, fontweight='bold', pad=20)
    
    # Add color bar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 100))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', pad=0.05, shrink=0.6)
    cbar.set_label('Coverage Percentage')
    
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved static sunburst chart to {output_file}")

def create_coverage_treemap(sunburst_data, output_file='coverage_treemap.html'):
    """Create interactive treemap using Plotly"""
    # Determine if we have both test suites
    has_both_suites = 'coverage_b' in sunburst_data
    
    # Create figure
    fig = go.Figure()
    
    # Color scale function
    def get_color(coverage):
        if coverage < 20:
            return 'rgb(165, 0, 38)'  # Dark red
        elif coverage < 40:
            return 'rgb(215, 48, 39)'  # Red
        elif coverage < 60:
            return 'rgb(244, 109, 67)'  # Orange
        elif coverage < 80:
            return 'rgb(253, 174, 97)'  # Light orange
        else:
            return 'rgb(116, 196, 118)'  # Green
    
    if has_both_suites:
        # Create figure with subplots
        from plotly.subplots import make_subplots
        fig = make_subplots(1, 2, specs=[[{'type': 'domain'}, {'type': 'domain'}]])
        
        # Test Suite A Treemap
        fig.add_trace(go.Treemap(
            labels=sunburst_data['labels'],
            parents=sunburst_data['parents'],
            values=sunburst_data['values'],
            marker=dict(
                colors=[get_color(cov) for cov in sunburst_data['coverage_a']],
                line=dict(width=1)
            ),
            hovertemplate='<b>%{label}</b><br>Coverage: %{customdata:.1f}%<br>Lines: %{value}<extra></extra>',
            customdata=sunburst_data['coverage_a'],
            name='Test Suite A',
            domain=dict(column=0)
        ), 1, 1)
        
        # Test Suite B Treemap
        fig.add_trace(go.Treemap(
            labels=sunburst_data['labels'],
            parents=sunburst_data['parents'],
            values=sunburst_data['values'],
            marker=dict(
                colors=[get_color(cov) for cov in sunburst_data['coverage_b']],
                line=dict(width=1)
            ),
            hovertemplate='<b>%{label}</b><br>Coverage: %{customdata:.1f}%<br>Lines: %{value}<extra></extra>',
            customdata=sunburst_data['coverage_b'],
            name='Test Suite B',
            domain=dict(column=1)
        ), 1, 2)
        
        # Update figure layout
        fig.update_layout(
            title_text='Code Coverage Treemap: Test Suite A vs. Test Suite B',
            grid=dict(columns=2, rows=1),
            annotations=[
                dict(text="Test Suite A", x=0.20, y=1.0, showarrow=False, font_size=16),
                dict(text="Test Suite B", x=0.80, y=1.0, showarrow=False, font_size=16)
            ]
        )
    else:
        # Single treemap for Test Suite A only
        fig.add_trace(go.Treemap(
            labels=sunburst_data['labels'],
            parents=sunburst_data['parents'],
            values=sunburst_data['values'],
            marker=dict(
                colors=[get_color(cov) for cov in sunburst_data['coverage_a']],
                line=dict(width=1)
            ),
            hovertemplate='<b>%{label}</b><br>Coverage: %{customdata:.1f}%<br>Lines: %{value}<extra></extra>',
            customdata=sunburst_data['coverage_a'],
            name='Test Suite A'
        ))
        
        # Update figure layout
        fig.update_layout(
            title_text='Code Coverage Treemap: Test Suite A'
        )
    
    # Common layout settings
    fig.update_layout(
        autosize=True,
        margin=dict(t=60, l=0, r=0, b=0),
        font=dict(size=12),
        height=800,
        width=1200
    )
    
    # Save to HTML file
    fig.write_html(output_file)
    print(f"Saved interactive treemap to {output_file}")
    
    return fig

def main():
    os.makedirs('visualizations', exist_ok=True)
    suite_a_data, suite_b_data = load_coverage_data()
    if not suite_a_data:
        print("Error: Test Suite A coverage data is missing.")
        return
    
    # Extract hierarchical coverage
    hierarchy_a = extract_hierarchical_coverage(suite_a_data)
    hierarchy_b = extract_hierarchical_coverage(suite_b_data) if suite_b_data else None
    
    # Create sunburst data
    sunburst_data = create_sunburst_data(hierarchy_a, hierarchy_b)
    
    # Create visualizations
    try:
        # Create interactive sunburst chart (requires plotly)
        create_plotly_sunburst(sunburst_data, 'visualizations/coverage_sunburst.html')
        
        # Create interactive treemap (requires plotly)
        create_coverage_treemap(sunburst_data, 'visualizations/coverage_treemap.html')
    except ImportError:
        print("Plotly not installed. Skipping interactive visualizations.")
    
    # Create static sunburst chart (simplified version with matplotlib)
    create_matplotlib_sunburst(sunburst_data, 'visualizations/coverage_sunburst.png')
    
    print("All hierarchical coverage visualizations generated successfully!")

if __name__ == "__main__":
    main()
