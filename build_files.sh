#!/bin/bash
# Install dependencies
pip3 install -r requirements.txt

# Collect static files
python3 manage.py collectstatic --noinput

# Create the SQLite database
python3 manage.py migrate
