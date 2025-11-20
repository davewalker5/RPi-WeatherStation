#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

python3 "$PROJECT_FOLDER/tests/main/generate_veml_test_fixture.py" \
    --illuminance "$1" \
    --veml-gain $VEML_GAIN \
    --veml-integration-ms $VEML_INTEGRATION_TIME
