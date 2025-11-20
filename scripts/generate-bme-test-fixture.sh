#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

python3 "$PROJECT_FOLDER/tests/main/generate_bme_test_fixture.py" \
    --temperature "$1" \
    --pressure "$2" \
    --humidity "$3"
