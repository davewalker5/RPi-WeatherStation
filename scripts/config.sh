#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
export PYTHONPATH="$PROJECT_FOLDER/src:$PROJECT_FOLDER/tests"
export BUS_NUMBER=0
export BME_ADDR=0x76
export VEML_ADDR=0x10
export VEML_GAIN=0.25
export VEML_INTEGRATION_TIME=100

# Make sure the data folder exists so the database can be created if needed
mkdir -p "$PROJECT_FOLDER/data"

echo
echo "PYTHONPATH       : $PYTHONPATH"
echo "I2C Bus Number   : $BUS_NUMBER"
echo "BME280 Address   : $BME_ADDR"
echo "VEML7700 Address : $VEML_ADDR"
echo "VEML7700 Gain    : $VEML_GAIN"
echo "VEML7700 IT      : $VEML_INTEGRATION_TIME"
echo
