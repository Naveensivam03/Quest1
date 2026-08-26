#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# --------------------------------------------------
# Runtime directories
# --------------------------------------------------

mkdir -p "$BACKEND_DIR/outputs"

# --------------------------------------------------
# Cleanup
# --------------------------------------------------

cleanup() {
  echo
  echo "Stopping Quest1..."

  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [ -n "${FRONTEND_PID:-}" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  wait 2>/dev/null || true

  echo "Quest1 stopped."
}

trap cleanup SIGINT SIGTERM EXIT

# --------------------------------------------------
# Start
# --------------------------------------------------

echo "======================================"
echo " Starting Quest1 (macOS)"
echo "======================================"

# --------------------------------------------------
# Backend
# --------------------------------------------------

echo
echo "Starting backend on http://127.0.0.1:8000..."

cd "$BACKEND_DIR"

uv run uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000 &

BACKEND_PID=$!

# --------------------------------------------------
# Frontend
# --------------------------------------------------

echo "Starting frontend on http://127.0.0.1:5500..."

cd "$FRONTEND_DIR"

uv run python -m http.server 5500 \
  --bind 127.0.0.1 &

FRONTEND_PID=$!

# --------------------------------------------------
# Status
# --------------------------------------------------

echo
echo "======================================"
echo " Quest1 is running"
echo "======================================"
echo
echo "Frontend:"
echo "  http://127.0.0.1:5500"
echo
echo "Backend:"
echo "  http://127.0.0.1:8000"
echo
echo "Press Ctrl+C to stop."
echo

wait
