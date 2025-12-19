#!/usr/bin/env bash
set -e

PORT=8080

echo "Starting deployment..."

# Kill existing server on the port
if lsof -i :$PORT >/dev/null 2>&1; then
  echo "Port $PORT is in use. Stopping existing server..."
  lsof -ti :$PORT | xargs kill -9
fi

# Create venv
if [ ! -d "venv" ]; then
  virtualenv venv
fi

source venv/bin/activate
pip install --upgrade pip

# Install uv if not present
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$PATH"
fi

uv pip install -r requirements.txt

echo "Starting server on port $PORT..."
nohup python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port $PORT \
  > server.log 2>&1 &

echo "Deployment completed successfully."
