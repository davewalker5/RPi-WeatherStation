#!/usr/bin/env bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

python3 "$PROJECT_FOLDER/src/main/bme-logger.py" \
    --bus $BUS_NUMBER \
    --bme-addr $BME_ADDR \
    --db "$PROJECT_FOLDER/data/weather.db" \
    "$@"
