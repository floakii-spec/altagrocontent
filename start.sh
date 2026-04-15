#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Streamlit..."
streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
