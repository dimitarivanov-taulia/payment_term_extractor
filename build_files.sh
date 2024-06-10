#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Ensure SQLite is installed
apt-get update
apt-get install -y sqlite3 libsqlite3-dev

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
