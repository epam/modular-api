#!/bin/sh

set -e
./modular.py init
./modular.py run --gunicorn
