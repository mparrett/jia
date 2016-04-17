#!/bin/bash

# Convenience script that runs a python script with args from any directory

# Allows script to be run from any directory
BASEDIR=$(cd -P -- "$(dirname -- "$0")" && printf '%s\n' "$(pwd -P)")
cd $BASEDIR

# Import environment variables
[ -e .env ] && source .env

source venv/bin/activate

# Pass original args
python jia.py $@
