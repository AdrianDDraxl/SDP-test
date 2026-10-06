#!/usr/bin/env bash
#
# RAT - Repo Analysis Tool
# One-command startup: installs dependencies and starts the backend + frontend.
#
# Usage:  ./start.sh
# Then open http://localhost:3000 in your browser.
#
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

# ---------- pick a Python interpreter ----------
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Error: Python 3 is required but was not found on PATH." >&2
  exit 1
fi

# ---------- check npm ----------
if ! command -v npm >/dev/null 2>&1; then
  echo "Error: Node.js / npm is required but was not found on PATH." >&2
  exit 1
fi

cleanup() {
  echo
  echo "==> Shutting down RAT..."
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  echo "==> Stopped."
}
trap cleanup EXIT INT TERM

# ---------- backend ----------
echo "==> Checking backend dependencies..."
if ! (cd "$ROOT_DIR/backend" && "$PY" -c "import flask, flask_cors" >/dev/null 2>&1); then
  echo "==> Installing backend dependencies (pip)..."
  (cd "$ROOT_DIR/backend" && "$PY" -m pip install -q -r requirements.txt) \
    || (cd "$ROOT_DIR/backend" && "$PY" -m pip install -q --user -r requirements.txt) \
    || (cd "$ROOT_DIR/backend" && "$PY" -m pip install -q --break-system-packages -r requirements.txt)
fi

echo "==> Starting backend on http://localhost:5000 ..."
(cd "$ROOT_DIR/backend" && "$PY" app.py) &
BACKEND_PID=$!

# ---------- frontend ----------
echo "==> Installing frontend dependencies (npm install)..."
npm install --prefix "$ROOT_DIR/frontend" --no-fund --no-audit

echo "==> Starting frontend on http://localhost:3000 ..."
npm run dev --prefix "$ROOT_DIR/frontend" &
FRONTEND_PID=$!

echo
echo "======================================================"
echo "  RAT - Repo Analysis Tool is running"
echo ""
echo "    Frontend:  http://localhost:3000"
echo "    Backend:   http://localhost:5000"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo "======================================================"
echo

wait
