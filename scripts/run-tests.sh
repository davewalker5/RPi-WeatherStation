#!/usr/bin/env bash

clear

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_FOLDER/venv/bin/activate"
export PYTHONPATH="$PROJECT_FOLDER/src:$PROJECT_FOLDER/tests"

echo Project root      = $PROJECT_FOLDER
echo Python Path       = $PYTHONPATH

python -m pytest "$PROJECT_FOLDER/tests/unit"
