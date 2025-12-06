#!/usr/bin/env bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

# Define the API endpoints to be tested
endpoints=(
  "health"
  "bme"
  "veml"
  "sgp"
)

# Iterate over the endpoints
for i in "${!endpoints[@]}"; do
    url="http://${PI_HOSTNAME}:${PI_PORT}/api/${endpoints[$i]}"
    echo
    echo "Calling ${url} ..."
    curl "$url"
    echo
done

echo
