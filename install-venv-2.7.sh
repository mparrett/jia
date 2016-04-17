#!/bin/bash

# Expects python 2.7

BASE_DIR=$(cd -P -- "$(dirname -- "$0")" && printf '%s\n' "$(pwd -P)")
VENV_DIR=./venv

echo "Installing virtualenv..."
rm -rf $VENV_DIR
virtualenv $VENV_DIR

source $VENV_DIR/bin/activate || (echo "Could not prepare virtualenv. How's your python install?"; exit 1)

pip install -r $BASE_DIR/requirements-2.7.txt
