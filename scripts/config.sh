#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
export PYTHONPATH="$PROJECT_FOLDER/src"
export BUS_NUMBER=0
export BME_ADDR=0x76

# Make sure the data folder exists so the database can be created if needed
mkdir -p "$PROJECT_FOLDER/data"
