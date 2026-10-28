#!/bin/zsh
# Run the WearWise FastAPI backend in development mode.
# Usage: ./run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate the FastAPI virtual environment
source fastapi_env/bin/activate

# Start uvicorn with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
