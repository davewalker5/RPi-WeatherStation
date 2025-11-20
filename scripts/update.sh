#!/usr/bin/env bash

PROJECT_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
cd "$PROJECT_FOLDER"
. "$PROJECT_FOLDER/venv/bin/activate"

pip freeze --local | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip3 install -U 
pip freeze > requirements.txt
