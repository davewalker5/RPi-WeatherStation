#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
export PYTHONPATH="$PROJECT_FOLDER/src"
export BUS_NUMBER=0
export ADDR=0x76

echo
echo "Project Root : $PROJECT_FOLDER"
echo "Bus Number   : $BUS_NUMBER"
echo "Address      : $ADDR"
echo
