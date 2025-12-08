#!/usr/bin/env bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_FOLDER=$( cd "$( dirname "$SCRIPT_PATH" )/.." && pwd )
. "$PROJECT_FOLDER/scripts/config.sh"

# Capture the path to the database
DB_PATH="$1"

# Define the API queries to run
queries=(
  "query-bme"
  "query-veml"
  "query-sgp"
)

# Iterate over the endpoints
for i in "${!queries[@]}"; do
    query_file="$PROJECT_FOLDER/sql/${queries[$i]}.sql"
    echo
    sqlite3 "$DB_PATH" "$query_file"
    echo
done

echo
