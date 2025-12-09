#!/usr/bin/env bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/../.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

python3 "$PROJECT_FOLDER/tests/device/test-lcd-loop.py"