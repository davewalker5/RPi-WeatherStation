#!/usr/bin/env bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

# Set default host and port
PI_HOSTNAME="weatherpi"
PI_PORT=8080

# Parse the arguments, if any, to override default hostname and port
while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      PI_HOSTNAME="$2"
      shift 2
      ;;
    --port)
      PI_PORT="$2"
      shift 2
      ;;
    --device)
      DEVICE="$2"
      shift 2
      ;;
    --state)
      STATE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done


# Construct the URL
url="http://${PI_HOSTNAME}:${PI_PORT}/api/${DEVICE}/${STATE}"

echo
echo "Calling ${url} ..."
curl -X PUT "$url"
echo
