#!/usr/bin/env bash

# LawyerFactory Full System Launcher
# Launches both frontend (HTTP server) and backend (Flask + Socket.IO) servers
# Usage: ./launch-full-system.sh [frontend_port] [backend_port]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_PORT="${1:-8000}"
BACKEND_PORT="${2:-5000}"
LOG_FILE="$SCRIPT_DIR/full-system-launch.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"; }
info() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERROR]${NC} $*"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# Check Python
if command_exists python3; then
  PYTHON_CMD=python3
elif command_exists python; then
  PYTHON_CMD=python
else
  err "Python is required but not found. Install Python 3."
  exit 1
fi

# Cross-platform port checking
check_port_available() {
  local port="$1"
  if command_exists nc; then
    if nc -z 127.0.0.1 "$port" 2>/dev/null; then
      return 1  # Port is in use
    else
      return 0  # Port is available
    fi
  elif command_exists lsof; then
    if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
      return 1  # Port is in use
    else
      return 0  # Port is available
    fi
  else
    warn "No port checking tool available. Assuming port $port is available."
    return 0
  fi
}

# Find available ports
find_available_port() {
  local port="$1"
  while ! check_port_available "$port"; do
    port=$((port + 1))
  done
  echo "$port"
}

FRONTEND_PORT=$(find_available_port "$FRONTEND_PORT")
BACKEND_PORT=$(find_available_port "$BACKEND_PORT")

# Setup backend
setup_backend() {
  info "Setting up backend server..."

  if [[ ! -f "$SCRIPT_DIR/apps/api/requirements.txt" ]]; then
    err "Backend requirements.txt not found"
    exit 1
  fi

  # Install Python dependencies
  if command_exists pip3; then
    PIP_CMD=pip3
  elif command_exists pip; then
    PIP_CMD=pip
  else
    err "pip is required but not found"
    exit 1
  fi

  info "Installing backend dependencies..."
  cd "$SCRIPT_DIR/apps/api"
  "$PIP_CMD" install -r requirements.txt

  if [[ ! -f "$SCRIPT_DIR/apps/api/server.py" ]]; then
    err "Backend server.py not found"
    exit 1
  fi

  info "Backend setup complete"
}

# Start backend server
start_backend() {
  info "Starting backend server on port $BACKEND_PORT..."
  cd "$SCRIPT_DIR/apps/api"

  # Start backend in background
  "$PYTHON_CMD" server.py --host 127.0.0.1 --port "$BACKEND_PORT" >"$SCRIPT_DIR/backend.log" 2>&1 &
  BACKEND_PID=$!

  # Wait for backend to start
  local tries=0
  local max_tries=30
  while [[ $tries -lt $max_tries ]]; do
    if check_port_available "$BACKEND_PORT"; then
      sleep 1
      tries=$((tries + 1))
    else
      info "Backend server started (PID: $BACKEND_PID)"
      return 0
    fi
  done

  err "Backend server failed to start"
  exit 1
}

# Start frontend server
start_frontend() {
  info "Starting frontend server on port $FRONTEND_PORT..."
  cd "$SCRIPT_DIR"

  # Start frontend in background
  "$PYTHON_CMD" -m http.server "$FRONTEND_PORT" --bind 127.0.0.1 >"$SCRIPT_DIR/frontend.log" 2>&1 &
  FRONTEND_PID=$!

  sleep 2

  if kill -0 "$FRONTEND_PID" 2>/dev/null; then
    info "Frontend server started (PID: $FRONTEND_PID)"
  else
    err "Frontend server failed to start"
    exit 1
  fi
}

# Health check
health_check() {
  local service="$1"
  local url="$2"
  local max_tries=10
  local tries=0

  info "Checking $service health at $url..."

  while [[ $tries -lt $max_tries ]]; do
    if command_exists curl; then
      if curl -s --head "$url" >/dev/null 2>&1; then
        info "$service is healthy"
        return 0
      fi
    else
      # Fallback to netcat
      local port="${url##*:}"
      if nc -z 127.0.0.1 "$port" >/dev/null 2>&1; then
        info "$service is healthy"
        return 0
      fi
    fi

    tries=$((tries + 1))
    sleep 1
  done

  warn "$service health check failed"
  return 1
}

# Open browser
open_browser() {
  local url="$1"
  if command_exists open; then
    open "$url"
  elif command_exists xdg-open; then
    xdg-open "$url"
  elif command_exists start; then
    start "$url"
  else
    info "Open this URL in your browser: $url"
  fi
}

# Cleanup function
cleanup() {
  info "Shutting down servers..."

  if [[ -n "${FRONTEND_PID-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    info "Stopping frontend server (PID: $FRONTEND_PID)"
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${BACKEND_PID-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    info "Stopping backend server (PID: $BACKEND_PID)"
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM EXIT

# Main execution
log "=== LawyerFactory Full System Launch ==="
log "Frontend Port: $FRONTEND_PORT"
log "Backend Port: $BACKEND_PORT"

# Setup and start backend
setup_backend
start_backend

# Start frontend
start_frontend

# Health checks
BACKEND_URL="http://127.0.0.1:$BACKEND_PORT/api/health"
FRONTEND_URL="http://127.0.0.1:$FRONTEND_PORT/apps/ui/templates/consolidated_factory.html"

if health_check "Backend" "$BACKEND_URL" && health_check "Frontend" "$FRONTEND_URL"; then
  info "🎉 All systems ready!"
  info "Backend API: $BACKEND_URL"
  info "Frontend UI: $FRONTEND_URL"

  # Open browser to frontend
  open_browser "$FRONTEND_URL"

  info "System is running. Press Ctrl+C to stop."
  info "Frontend PID: $FRONTEND_PID"
  info "Backend PID: $BACKEND_PID"
  info "Logs: $LOG_FILE"

  # Keep script running
  wait "$FRONTEND_PID" "$BACKEND_PID"
else
  err "System health check failed. Check logs for details."
  exit 1
fi