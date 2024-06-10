#!/bin/bash
# Install dependencies
/vercel/path0/.python/bin/pip install -r requirements.txt

# Collect static files
/vercel/path0/.python/bin/python manage.py collectstatic --noinput

# Create the SQLite database
/vercel/path0/.python/bin/python manage.py migrate
