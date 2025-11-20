#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/../.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

python3 "$PROJECT_FOLDER/tests/device/dump-bme-trimming.py" \
    --bus $BUS_NUMBER \
    --bme-addr $BME_ADDR
