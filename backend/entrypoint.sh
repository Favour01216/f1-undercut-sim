#!/bin/bash
# Railway entrypoint script

# Use Railway's PORT if set, otherwise default to 8000
export PORT=${PORT:-8000}

# Start the FastAPI application
exec uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1