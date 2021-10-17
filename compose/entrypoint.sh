#!/usr/bin/env bash

set -o errexit
set -o pipefail


cmd="$@"

if [ -z "$DATABASE_URL" ]; then
    echo "env: DATABASE_URL not set"
    exit 1
fi

if [ -z "$SERVER_HOST" ]; then
    echo "env: SERVER_HOST not set"
    exit 1
fi

if [ -z "$CORS_ORIGINS" ]; then
    echo "env: CORS_ORIGINS not set"
    exit 1
fi

if [ -z "$TRUSTED_HOSTS" ]; then
    echo "env: TRUSTED_HOSTS not set"
    exit 1
fi


>&2 echo "Configuration valid - starting FastAPI via uvicorn over gunicorn..."
exec $cmd
