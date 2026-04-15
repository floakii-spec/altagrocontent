#!/bin/bash
set -e

export PYTHONPATH=/app:$PYTHONPATH

echo "DATABASE_URL is set: ${DATABASE_URL:+yes}"
echo "DATABASE_URL prefix: ${DATABASE_URL:0:20}"
echo "Running database migrations..."
alembic upgrade head

echo "Starting Streamlit..."
streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
