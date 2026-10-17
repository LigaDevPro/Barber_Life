#!/bin/sh
set -e
python manage.py collectstatic --noinput
python manage.py migrate --noinput
exec daphne --proxy-headers -b 0.0.0.0 -p "${PORT:-8000}" core.asgi:application