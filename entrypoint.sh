#!/bin/sh

set -e
./modular.py init
./modular.py create-indexes
exec ./modular.py run --gunicorn --workers "${MODULAR_API_GUNICORN_WORKERS:-2}"