#!/usr/bin/env bash

# Get the absolute path to this file and then use it to get the project path
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/.." && pwd )

# Set the environment
export PYTHONPATH="$PROJECT_FOLDER/src:$PROJECT_FOLDER/tests"
export PI_HOSTNAME=weatherpi
export PI_PORT=8080
export SAMPLE_INTERVAL=60.0
export DISPLAY_INTERVAL=5.0
export BUS_NUMBER=1
export MUX_ADDR=0x70
export BME_ADDR=0x76
export BME_CHANNEL=5
export VEML_ADDR=0x10
export VEML_CHANNEL=6
export VEML_GAIN=0.25
export VEML_INTEGRATION_TIME=100
export SGP_ADDR=0x59
export SGP_CHANNEL=7
export LCD_ADDR=0x27
export LCD_CHANNEL=4

# Make sure the data folder exists so the database can be created if needed
mkdir -p "$PROJECT_FOLDER/data"

echo
echo "PYTHONPATH       : $PYTHONPATH"
echo "I2C Bus Number   : $BUS_NUMBER"
echo "MUX Address      : $MUX_ADDR"
echo "BME280 Address   : $BME_ADDR"
echo "BME280 Channel   : $MUX_ADDR"
echo "VEML7700 Address : $VEML_ADDR"
echo "VEML7700 Channel : $VEML_CHANNEL"
echo "VEML7700 Gain    : $VEML_GAIN"
echo "VEML7700 IT      : $VEML_INTEGRATION_TIME"
echo "SGP40 Address    : $SGP_ADDR"
echo "SGP40 Channel    : $SGP_CHANNEL"
echo "LCD Address      : $LCD_ADDR"
echo "LCD Channel      : $LCD_CHANNEL"
echo "Sample Interval  : $SAMPLE_INTERVAL"
echo "Display Interval : $DISPLAY_INTERVAL"
echo
