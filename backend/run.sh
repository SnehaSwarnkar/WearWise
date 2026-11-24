#!/bin/zsh
# WearWise FastAPI Backend — start in development mode
# Usage: ./run.sh [port]
#
# Prerequisites:
#   cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${1:-8000}"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f "fastapi_env/bin/activate" ]; then
  source fastapi_env/bin/activate
else
  echo "⚠️  No virtual environment found. Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

echo "🚀 Starting WearWise API on http://localhost:${PORT}"
echo "📚 Swagger docs: http://localhost:${PORT}/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"
