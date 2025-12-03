#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
    echo Usage: $(basename "$0") device
    exit 1
fi

diskutil unmountDisk $1 | true
sudo diskutil eraseDisk FAT32 PI $1
