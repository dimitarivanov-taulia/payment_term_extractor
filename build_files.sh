#!/bin/bash

# Install SQLite3
apt-get update && apt-get install -y sqlite3 libsqlite3-dev

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Create the SQLite database
python manage.py migrate
