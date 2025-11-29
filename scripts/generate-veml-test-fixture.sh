#!/usr/bin/env bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

if [[ -z $1 ]]; then
    python3 "$PROJECT_FOLDER/tests/main/generate_veml_test_fixture.py" \
        --veml-gain $VEML_GAIN \
        --veml-integration-ms $VEML_INTEGRATION_TIME

else
    python3 "$PROJECT_FOLDER/tests/main/generate_veml_test_fixture.py" \
        --illuminance "$1" \
        --veml-gain $VEML_GAIN \
        --veml-integration-ms $VEML_INTEGRATION_TIME

fi
