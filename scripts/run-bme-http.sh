#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

python3 "$PROJECT_FOLDER/src/main/bme-http.py" \
    --bus $BUS_NUMBER \
    --addr $ADDR \
    --db "$PROJECT_FOLDER/data/bme280.db" \
    --host 0.0.0.0 \
    --port 8080
