#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

python3 "$PROJECT_FOLDER/src/main/weather-service.py" \
    --bus $BUS_NUMBER \
    --bme-addr $BME_ADDR \
    --veml-addr $VEML_ADDR \
    --veml-gain $VEML_GAIN \
    --veml-integration-ms $VEML_INTEGRATION_TIME \
    --db "$PROJECT_FOLDER/data/weather.db" \
    --host 0.0.0.0 \
    --port 8080
