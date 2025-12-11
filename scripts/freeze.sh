#!/usr/bin/env bash

pip list --format=freeze | cut -d= -f1 > requirements.txt
