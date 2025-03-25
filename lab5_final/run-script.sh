#!/bin/bash
# This script activates the virtual environment and runs the main script

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting up environment first..."
    ./setup-script.sh
fi

# Activate the virtual environment
source venv/bin/activate

# Run the main script
./main-script.sh

# Deactivate the virtual environment
deactivate

echo "Execution completed!"