#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
BUS_NUMBER=0
ADDR=0x76

python3 "$PROJECT_FOLDER/src/bme280-http.py" \
    --bus $BUS_NUMBER \
    --addr $ADDR \
    --db "$PROJECT_FOLDER/data/bme280.db" \
    --host 0.0.0.0 \
    --port 8080
