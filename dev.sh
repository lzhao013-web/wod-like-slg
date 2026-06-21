#!/usr/bin/env bash
# One-shot launcher (bash / git-bash / WSL): starts backend (:8000) + frontend (:5173).
# Ctrl+C stops both. Ports are configurable via env, e.g. BACKEND_PORT=9000 ./dev.sh
set -euo pipefail

cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo
    echo "[dev] stopping services..."
    [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
    [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
    # Reap any child processes (uvicorn --reload workers, vite).
    jobs -p | xargs -r kill 2>/dev/null || true
    echo "[dev] stopped."
}
trap cleanup EXIT INT TERM

echo "============================================================"
echo "  wod-like-slg dev launcher"
echo "============================================================"

# --- pick the Python interpreter -------------------------------------------
PY=""
if [[ -x ".venv/Scripts/python.exe" ]]; then
    PY=".venv/Scripts/python.exe"
elif command -v uv >/dev/null 2>&1; then
    PY="uv run python"
elif command -v python >/dev/null 2>&1; then
    PY="python"
fi
if [[ -z "$PY" ]]; then
    echo "[ERROR] No Python found. Create a venv (python -m venv .venv) or install uv."
    exit 1
fi
echo "Using Python: $PY"

# --- install frontend deps if missing --------------------------------------
if [[ ! -d "frontend/node_modules" ]]; then
    echo "[setup] Installing frontend dependencies..."
    (cd frontend && npm install)
fi

# --- start backend ----------------------------------------------------------
echo "[backend] starting uvicorn on http://127.0.0.1:$BACKEND_PORT ..."
$PY -m uvicorn backend.app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!

# --- start frontend ---------------------------------------------------------
echo "[frontend] starting vite on http://127.0.0.1:$FRONTEND_PORT ..."
(cd frontend && npm run dev -- --port "$FRONTEND_PORT") &
FRONTEND_PID=$!

echo
echo "============================================================"
echo "  App:  http://127.0.0.1:$FRONTEND_PORT"
echo "  API:  http://127.0.0.1:$BACKEND_PORT/docs"
echo "  Ctrl+C to stop both."
echo "============================================================"

# Wait for either process to exit, then cleanup runs via trap.
wait
