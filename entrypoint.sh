#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Running initial import check..."
python manage.py import_lerninhalte || echo "Import check completed (may have no new files)"

echo "Starting application (background import scheduler will start automatically)..."
exec "$@"
