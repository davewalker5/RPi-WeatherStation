#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/../.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

python3 "$PROJECT_FOLDER/tests/device/read-veml.py" \
    --bus $BUS_NUMBER \
    --veml-addr $VEML_ADDR \
    --veml-gain $VEML_GAIN \
    --veml-integration-ms $VEML_INTEGRATION_TIME \
