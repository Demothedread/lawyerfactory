#!/usr/bin/env bash
# filepath: scripts/stop-services.sh
# Stop all LawyerFactory services gracefully

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

log() {
    echo -e "\033[0;32m[LawyerFactory]\033[0m $1"
}

error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

log "Stopping LawyerFactory services..."

# Stop backend
if [ -f .pids/backend.pid ]; then
    BACKEND_PID=$(cat .pids/backend.pid)
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null && log "Backend stopped (PID: $BACKEND_PID)"
    fi
    rm .pids/backend.pid
fi

# Stop frontend
if [ -f .pids/frontend.pid ]; then
    FRONTEND_PID=$(cat .pids/frontend.pid)
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null && log "Frontend stopped (PID: $FRONTEND_PID)"
    fi
    rm .pids/frontend.pid
fi

# Stop health monitor
if [ -f .pids/health-monitor.pid ]; then
    HEALTH_PID=$(cat .pids/health-monitor.pid)
    if kill -0 "$HEALTH_PID" 2>/dev/null; then
        kill "$HEALTH_PID" 2>/dev/null && log "Health monitor stopped"
    fi
    rm .pids/health-monitor.pid
fi

# Stop Qdrant if running via Docker
if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
        docker stop qdrant 2>/dev/null && log "Qdrant stopped"
    fi
fi

log "All services stopped successfully"