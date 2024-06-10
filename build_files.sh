#!/bin/bash

# Use the correct Python environment path
PYTHON_BIN_PATH=$(which python3 || which python)
PIP_BIN_PATH=$(which pip3 || which pip)

# Install dependencies
$PIP_BIN_PATH install -r requirements.txt

# Collect static files
$PYTHON_BIN_PATH manage.py collectstatic --noinput

# Create the SQLite database
$PYTHON_BIN_PATH manage.py migrate
