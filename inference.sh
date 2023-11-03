#!/bin/bash

if [ -d $(dirname $0)/inference/venv ]; then
  source $(dirname $0)/inference/venv/bin/activate
fi

if [ -z "$2" ]; then
    python $(dirname $0)/inference/inference.py -i $1
else
    python $(dirname $0)/inference/inference.py -i $1 -r $2
fi
