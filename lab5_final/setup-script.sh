#!/bin/bash
# Exit on error
set -e

echo "Setting up environment for Code Coverage Analysis..."

# Create and activate a Python virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install required dependencies - explicitly install each one to handle any failures
echo "Installing pytest..."
pip install pytest || echo "Warning: Failed to install pytest"

echo "Installing pytest-cov..."
pip install pytest-cov || echo "Warning: Failed to install pytest-cov"

echo "Installing pytest-func-cov..."
pip install pytest-func-cov || echo "Warning: Failed to install pytest-func-cov"

echo "Installing coverage..."
pip install coverage || echo "Warning: Failed to install coverage"

echo "Installing pynguin..."
pip install pynguin || echo "Warning: Failed to install pynguin"

echo "Installing matplotlib..."
pip install matplotlib || echo "Warning: Failed to install matplotlib"

# Clone the repository
if [ ! -d "algorithms" ]; then
    echo "Cloning repository..."
    git clone https://github.com/keon/algorithms.git
    cd algorithms
    
    # Record the commit hash
    COMMIT_HASH=$(git rev-parse HEAD)
    echo "Current commit hash: $COMMIT_HASH" > ../commit_hash.txt
    
    # Install the algorithms package in editable mode
    echo "Installing algorithms package in editable mode..."
    pip install -e . || echo "Warning: Failed to install algorithms package"
    
    cd ..
else
    echo "Repository already exists"
    cd algorithms
    COMMIT_HASH=$(git rev-parse HEAD)
    echo "Current commit hash: $COMMIT_HASH" > ../commit_hash.txt
    
    # Install the algorithms package in editable mode
    echo "Installing algorithms package in editable mode..."
    pip install -e . || echo "Warning: Failed to install algorithms package"
    
    cd ..
fi

# Check if all required packages are installed
echo -e "\nChecking installed packages:"
pip list | grep -E 'pytest|coverage|pynguin|matplotlib' || echo "Some packages may be missing"

echo "Setup completed successfully!"
