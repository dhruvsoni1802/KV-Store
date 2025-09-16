#!/bin/bash

# Database cleanup script wrapper
# This script provides easy access to the Python cleanup script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/clean_databases.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: clean_databases.py not found in $SCRIPT_DIR"
    exit 1
fi

# Pass all arguments to the Python script
python3 "$PYTHON_SCRIPT" "$@"
