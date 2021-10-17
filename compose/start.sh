#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -o errexit

# The return value of a pipeline is the status of the last command to exit with
# a non-zero status, or zero if no command exited with a non-zero status
set -o pipefail

# Treat unset variables as an error when substituting.
set -o nounset

# Print commands and their arguments as they are executed.
set -o xtrace

# prepare something
# ...

cd /app

# run uvicorn over gunicorn in docker in production
# https://www.uvicorn.org/#running-with-gunicorn
# replaces: uvicorn application.main:app --reload
gunicorn application.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 300 --preload
