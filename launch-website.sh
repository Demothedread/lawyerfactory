#!/usr/bin/env bash

# LawyerFactory Website Launcher (improved)
# Serves the repository root and opens the most feature-rich HTML template in the default browser (macOS)
# Usage: ./launch-website.sh [port]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PORT=8000
LOG_FILE="$SCRIPT_DIR/website-launch.log"

# Candidate HTML files (absolute paths)
CANDIDATES=(
  "$SCRIPT_DIR/templates/orchestration/dashboard.html"
  "$SCRIPT_DIR/apps/ui/templates/consolidated_factory.html"
  "$SCRIPT_DIR/apps/ui/templates/modern_dashboard.html"
  "$SCRIPT_DIR/apps/ui/templates/factory.html"
  "$SCRIPT_DIR/apps/ui/templates/intake_form.html"
)

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

# Choose port
PORT="${1:-$DEFAULT_PORT}"

# Ensure Python
if command_exists python3; then
  PYTHON_CMD=python3
elif command_exists python; then
  PYTHON_CMD=python
else
  err "Python is required but not found. Install Python 3."
  exit 1
fi

# Pick the largest (most feature-rich) existing candidate
RECOMMENDED_FILE=""
RECOMMENDED_SIZE=0
for p in "${CANDIDATES[@]}"; do
  if [[ -f "$p" ]]; then
    size=$(stat -f%z "$p" 2>/dev/null || stat -c%s "$p" 2>/dev/null || echo 0)
    if (( size > RECOMMENDED_SIZE )); then
      RECOMMENDED_SIZE=$size
      RECOMMENDED_FILE="$p"
    fi
  fi
done

if [[ -z "$RECOMMENDED_FILE" ]]; then
  warn "No candidate HTML files found; falling back to root index if present."
  if [[ -f "$SCRIPT_DIR/index.html" ]]; then
    RECOMMENDED_FILE="$SCRIPT_DIR/index.html"
  else
    err "No HTML file found to launch. Exiting."
    exit 1
  fi
fi

# --- Changed: prefer consolidated factory as the main UI and remove stray characters ---
# If the consolidated factory exists prefer it explicitly (user request)
PREFERRED_CONSOLIDATED="$SCRIPT_DIR/apps/ui/templates/consolidated_factory.html"
if [[ -f "$PREFERRED_CONSOLIDATED" ]]; then
  RECOMMENDED_FILE="$PREFERRED_CONSOLIDATED"
  info "Preferring consolidated UI: $RECOMMENDED_FILE"
fi

# Serve from apps/ so app-specific absolute paths resolve (fall back to repo root)
SERVE_DIR="$SCRIPT_DIR/apps"
if [[ ! -d "$SERVE_DIR" ]]; then
  warn "Serve directory $SERVE_DIR not found; falling back to repository root."
  SERVE_DIR="$SCRIPT_DIR"
fi

# If the chosen file is not under the current SERVE_DIR, switch SERVE_DIR to repo root so the file is accessible
if [[ "$RECOMMENDED_FILE" != "$SERVE_DIR/"* ]]; then
  warn "Chosen file $RECOMMENDED_FILE is outside $SERVE_DIR; serving from repository root so the file is accessible."
  SERVE_DIR="$SCRIPT_DIR"
fi

# Compute path to open relative to the chosen serve dir
REL_PATH="${RECOMMENDED_FILE#$SERVE_DIR/}"

# Find free port
find_available_port() {
  local port=$1
  while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
    port=$((port + 1))
  done
  echo $port
}

PORT=$(find_available_port "$PORT")

start_server() {
  log "Starting HTTP server in $SERVE_DIR serving $REL_PATH on port $PORT"
  cd "$SERVE_DIR"
  # run in background, redirect stdout/stderr to logfile
  "$PYTHON_CMD" -m http.server "$PORT" --bind 127.0.0.1 >"$LOG_FILE" 2>&1 &
  SERVER_PID=$!
  sleep 1
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    info "Server started (PID: $SERVER_PID)"
    log "Server PID: $SERVER_PID"
  else
    err "Server failed to start; check $LOG_FILE"
    exit 1
  fi
}

health_check() {
  local url=$1
  local tries=0
  local max=10
  while [[ $tries -lt $max ]]; do
    if command_exists curl; then
      if curl -s --head "$url" >/dev/null 2>&1; then
        return 0
      fi
    else
      # Try netcat check as fallback
      if nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1; then
        return 0
      fi
    fi
    tries=$((tries + 1))
    sleep 0.5
  done
  return 1
}

open_browser() {
  local url=$1
  # macOS open
  if command_exists open; then
    open "$url"
  else
    info "No 'open' command found; print URL to open manually: $url"
  fi
}

cleanup() {
  if [[ -n "${SERVER_PID-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    warn "Stopping server (PID: $SERVER_PID)"
    kill "$SERVER_PID" 2>/dev/null || true
  fi
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start
start_server
URL="http://127.0.0.1:$PORT/$REL_PATH"

info "Waiting for server to become ready at $URL"
if health_check "$URL"; then
  info "Server ready. Opening browser..."
  open_browser "$URL"
  info "Launched: $URL"
  info "Logs: $LOG_FILE"
  echo "To stop the server: kill $SERVER_PID"
else
  err "Server health check failed; see $LOG_FILE"
  exit 1
fi

# Keep script running to keep background server alive when invoked interactively
# (user can Ctrl+C to trigger cleanup and kill server)
wait "$SERVER_PID"