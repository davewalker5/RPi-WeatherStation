#!/usr/bin/env bash

# Get the absolute path to this file and then use it to get the project path
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/.." && pwd )

# Set the environment
export PYTHONPATH="$PROJECT_FOLDER/src:$PROJECT_FOLDER/tests"

# Make sure the data folder exists so the database can be created if needed
mkdir -p "$PROJECT_FOLDER/data"

echo
echo "PYTHONPATH       : $PYTHONPATH"
echo
