#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
BUS_NUMBER=0
ADDR=0x76

export PYTHONPATH="$PROJECT_FOLDER/src"

python3 "$PROJECT_FOLDER/src/main/read-bme.py" \
    --bus $BUS_NUMBER \
    --addr $ADDR
