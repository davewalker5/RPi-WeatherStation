#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
. "$PROJECT_ROOT/scripts/config.sh"

python3 "$PROJECT_FOLDER/src/main/read-bme.py" \
    --bus $BUS_NUMBER \
    --addr $ADDR
