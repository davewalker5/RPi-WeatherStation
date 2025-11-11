#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_ROOT/config.sh"

export PYTHONPATH="$PROJECT_FOLDER/src"

python3 "$PROJECT_FOLDER/src/main/read-bme.py" \
    --bus $BUS_NUMBER \
    --addr $ADDR
