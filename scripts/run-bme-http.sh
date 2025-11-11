#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_ROOT/config.sh"

python3 "$PROJECT_FOLDER/src/bme280-http.py" \
    --bus $BUS_NUMBER \
    --addr $ADDR \
    --db "$PROJECT_FOLDER/data/bme280.db" \
    --host 0.0.0.0 \
    --port 8080
