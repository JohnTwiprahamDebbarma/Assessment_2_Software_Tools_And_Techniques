#!/usr/bin/env python3
import os

def create_directory_structure():
    base_dir = "bandit_analysis_results"
    repositories = [
        'bandit',
        'manim',
        'flask'
    ]
    
    os.makedirs(base_dir, exist_ok=True)
    print(f"Created directory: {os.path.abspath(base_dir)}")
    for repo in repositories:
        repo_dir = os.path.join(base_dir, repo)
        os.makedirs(repo_dir, exist_ok=True)
        print(f"Created directory: {os.path.abspath(repo_dir)}")
        
        # Bandit outputs directory:
        bandit_dir = os.path.join(repo_dir, 'bandit_outputs')
        os.makedirs(bandit_dir, exist_ok=True)
        print(f"Created directory: {os.path.abspath(bandit_dir)}")
    
    # Creating analysis outputs directory:
    analysis_dir = os.path.join(base_dir, 'analysis_outputs')
    os.makedirs(analysis_dir, exist_ok=True)
    print(f"Created directory: {os.path.abspath(analysis_dir)}")
    
    # Creating repository-specific analysis directories:
    for repo in repositories:
        repo_analysis_dir = os.path.join(analysis_dir, repo)
        os.makedirs(repo_analysis_dir, exist_ok=True)
        print(f"Created directory: {os.path.abspath(repo_analysis_dir)}")
    
    print("\nDirectory structure created successfully!")
    print(f"Base directory: {os.path.abspath(base_dir)}")

if __name__ == "__main__":
    create_directory_structure()
