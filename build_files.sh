#!/bin/bash

# Install dependencies
pip3 install -r requirements.txt

# Collect static files
python3 manage.py collectstatic --noinput

# If needed, create a minimal database (this can be skipped if not using any database functionality)
python3 manage.py migrate --noinput || true