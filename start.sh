#!/bin/bash
set -e

export PYTHONPATH=/app:$PYTHONPATH

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI..."
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}
