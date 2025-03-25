#!/usr/bin/env python3
import os
import subprocess
import json
import csv
import re
from datetime import datetime

def get_last_100_non_merge_commits(repo_path):
    os.chdir(repo_path)
    
    # Getting list of non-merge commits:
    result = subprocess.run(
        ['git', 'log', '--no-merges', '--pretty=format:%H,%an,%at,%s', 'HEAD~200..HEAD'],
        capture_output=True, text=True
    )
    
    commits = []
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split(',', 3)
            if len(parts) == 4:
                commit_hash, author, timestamp, message = parts
                commits.append({
                    'hash': commit_hash,
                    'author': author,
                    'timestamp': int(timestamp),
                    'date': datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S'),
                    'message': message
                })
    
    # Returning the last 100 commits (or all if < 100):
    return commits[:100]

def run_bandit_on_commit(repo_path, commit_hash, output_file):
    os.chdir(repo_path)
    
    # Checking out the specific commit:
    subprocess.run(['git', 'checkout', commit_hash], capture_output=True)
    
    # Command to run Bandit with JSON output
    subprocess.run(
        ['bandit', '-r', '.', '-f', 'json', '-o', output_file],
        capture_output=True
    )

def parse_bandit_results(output_file):
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
            
        metrics = {
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'high_severity': 0,
            'medium_severity': 0,
            'low_severity': 0,
            'unique_cwes': set()
        }
        
        for result in data.get('results', []):
            # Counting by confidence
            if result.get('issue_confidence') == 'HIGH':
                metrics['high_confidence'] += 1
            elif result.get('issue_confidence') == 'MEDIUM':
                metrics['medium_confidence'] += 1
            elif result.get('issue_confidence') == 'LOW':
                metrics['low_confidence'] += 1
            
            # Counting by severity
            if result.get('issue_severity') == 'HIGH':
                metrics['high_severity'] += 1
            elif result.get('issue_severity') == 'MEDIUM':
                metrics['medium_severity'] += 1
            elif result.get('issue_severity') == 'LOW':
                metrics['low_severity'] += 1
            
            # Extracting CWE from issue_cwe if available
            if 'issue_cwe' in result and 'id' in result['issue_cwe']:
                metrics['unique_cwes'].add(str(result['issue_cwe']['id']))
            # Fallback to regex on issue_text (as in original code)
            else:
                cwe_match = re.search(r'CWE-(\d+)', result.get('issue_text', ''))
                if cwe_match:
                    metrics['unique_cwes'].add(cwe_match.group(1))
        
        # Convert set to list for serialization
        metrics['unique_cwes'] = list(metrics['unique_cwes'])
        return metrics
    except Exception as e:
        print(f"Error parsing {output_file}: {e}")
        return None

# def parse_bandit_results(output_file):
#     try:
#         with open(output_file, 'r') as f:
#             data = json.load(f)
            
#         metrics = {
#             'high_confidence': 0,
#             'medium_confidence': 0,
#             'low_confidence': 0,
#             'high_severity': 0,
#             'medium_severity': 0,
#             'low_severity': 0,
#             'unique_cwes': set()
#         }
        
#         for result in data.get('results', []):
#             # Counting by confidence:
#             if result.get('issue_confidence') == 'HIGH':
#                 metrics['high_confidence'] += 1
#             elif result.get('issue_confidence') == 'MEDIUM':
#                 metrics['medium_confidence'] += 1
#             elif result.get('issue_confidence') == 'LOW':
#                 metrics['low_confidence'] += 1
            
#             # Counting by severity:
#             if result.get('issue_severity') == 'HIGH':
#                 metrics['high_severity'] += 1
#             elif result.get('issue_severity') == 'MEDIUM':
#                 metrics['medium_severity'] += 1
#             elif result.get('issue_severity') == 'LOW':
#                 metrics['low_severity'] += 1
            
#             # Extracting CWE from issue text if available:
#             cwe_match = re.search(r'CWE-(\d+)', result.get('issue_text', ''))
#             if cwe_match:
#                 metrics['unique_cwes'].add(cwe_match.group(1))
        
#         metrics['unique_cwes'] = list(metrics['unique_cwes'])
#         return metrics
#     except Exception as e:
#         print(f"Error parsing {output_file}: {e}")
#         return None

def main():
    base_dir = os.path.abspath("bandit_analysis_results")
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created base directory: {base_dir}")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repositories = [
        {
            'name': 'bandit',
            'path': os.path.join(current_dir, 'bandit')
        },
        {
            'name': 'manim',
            'path': os.path.join(current_dir, 'manim')
        },
        {
            'name': 'flask',
            'path': os.path.join(current_dir, 'flask')
        }
    ]
    
    for repo in repositories:
        repo_name = repo['name']
        repo_path = repo['path']
        
        print(f"\nProcessing repository: {repo_name}")
        print(f"Repository path: {repo_path}")
        
        if not os.path.exists(repo_path):
            print(f"Repository not found at {repo_path}. Skipping.")
            continue
        
        repo_output_dir = os.path.join(base_dir, repo_name)
        if not os.path.exists(repo_output_dir):
            os.makedirs(repo_output_dir)
            print(f"Created repository output directory: {repo_output_dir}")
        
        # Creating bandit outputs directory:
        bandit_outputs_dir = os.path.join(repo_output_dir, 'bandit_outputs')
        if not os.path.exists(bandit_outputs_dir):
            os.makedirs(bandit_outputs_dir)
            print(f"Created bandit outputs directory: {bandit_outputs_dir}")
        
        print(f"Getting last 100 non-merge commits for {repo_name}...")
        commits = get_last_100_non_merge_commits(repo_path)
        results_file = os.path.join(repo_output_dir, "results.csv")
        print(f"Writing results to: {results_file}")
        with open(results_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'commit_hash', 'author', 'date', 'message',
                'high_confidence', 'medium_confidence', 'low_confidence',
                'high_severity', 'medium_severity', 'low_severity',
                'unique_cwes'
            ])
            
            # Processing each commit:
            for i, commit in enumerate(commits):
                print(f"Processing commit {i+1}/{len(commits)}: {commit['hash']}")
                
                # Runing Bandit cmd on the commit:
                output_file = os.path.join(bandit_outputs_dir, f"{commit['hash']}.json")
                try:
                    run_bandit_on_commit(repo_path, commit['hash'], output_file)
                    
                    metrics = parse_bandit_results(output_file)
                    if metrics:
                        writer.writerow([
                            commit['hash'],
                            commit['author'],
                            commit['date'],
                            commit['message'],
                            metrics['high_confidence'],
                            metrics['medium_confidence'],
                            metrics['low_confidence'],
                            metrics['high_severity'],
                            metrics['medium_severity'],
                            metrics['low_severity'],
                            ','.join(metrics['unique_cwes'])
                        ])
                except Exception as e:
                    print(f"Error processing commit {commit['hash']}: {e}")
            
        os.chdir(repo_path)
        try:
            subprocess.run(['git', 'checkout', 'main'], capture_output=True)
            current_branch = subprocess.run(['git', 'branch', '--show-current'], 
                                          capture_output=True, text=True).stdout.strip()
            if current_branch != 'main':
                subprocess.run(['git', 'checkout', 'master'], capture_output=True)
        except Exception as e:
            print(f"Error returning to main branch: {e}")
        print(f"Analysis complete for {repo_name}")
    print("\nAll analyses complete!")

if __name__ == "__main__":
    main()
