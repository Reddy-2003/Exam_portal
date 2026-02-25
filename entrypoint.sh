#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until python manage.py migrate --check > /dev/null 2>&1 || python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assignment_platform.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
" > /dev/null 2>&1; do
  echo "PostgreSQL not ready yet - retrying in 2 seconds..."
  sleep 2
done

echo "PostgreSQL is ready."

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn server..."
exec gunicorn assignment_platform.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
