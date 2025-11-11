#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_ROOT/config.sh"

export PYTHONPATH="$PROJECT_FOLDER/src"

python3 "$PROJECT_FOLDER/src/main/bme-logger.py" \
    --bus $BUS_NUMBER \
    --addr $ADDR \
    --db "$PROJECT_FOLDER/data/bme280.db" \
    "$@"
