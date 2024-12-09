#!/bin/sh

set -e
./modular.py init
./modular.py create-indexes
./modular.py run --gunicorn
