#!/bin/bash

# Expects python 2.7

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR=./venv

echo "Installing virtualenv..."
rm -rf $VENV_DIR
virtualenv $VENV_DIR

source $VENV_DIR/bin/activate || (echo "Could not prepare virtualenv. How's your python install?"; exit 1)

pip install -r $SCRIPT_DIR/requirements-2.7.txt
