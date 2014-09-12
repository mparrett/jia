#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SRC_PY_PATH=/usr/local/python-2.7/bin

echo "Reinstalling virtualenv..."
rm -rf ENV-2.7
$SRC_PY_PATH/virtualenv ENV-2.7
source ENV-2.7/bin/activate || exit 1

pip install -r $SCRIPT_DIR/requirements-2.7.txt
