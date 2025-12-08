#!/usr/bin/env bash

clear

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/.." && pwd )
. "$PROJECT_FOLDER/venv/bin/activate"
export PYTHONPATH="$PROJECT_FOLDER/src:$PROJECT_FOLDER/tests"

python -m dashboard
