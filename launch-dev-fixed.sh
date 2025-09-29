#!/usr/bin/env bash

# LawyerFactory Development Environment Launcher v4.0.0 - DEBUG VERSION
# Enhanced with comprehensive debugging for launch failure diagnosis
# Usage: ./launch-dev-debug.sh [options]

set -euo pipefail

# Script metadata
readonly SCRIPT_VERSION="4.0.0-DEBUG"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="$SCRIPT_DIR/logs"
readonly CONFIG_DIR="$SCRIPT_DIR/configs"
readonly VITE_APP_DIR="$SCRIPT_DIR/apps/ui/react-app/"
readonly BACKEND_DIR="$SCRIPT_DIR/apps/api"

# Environment detection
ENVIRONMENT="${ENVIRONMENT:-development}"
NODE_ENV="${NODE_ENV:-development}"

# Default configuration
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-5000}"
SKIP_DEPS="${SKIP_DEPS:-false}"
VERBOSE="${VERBOSE:-true}"  # Force verbose in debug mode
DRY_RUN="${DRY_RUN:-false}"
LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
SETUP_MODE="${SETUP_MODE:-false}"
OPEN_BROWSER="${OPEN_BROWSER:-true}"
PRODUCTION_MODE="${PRODUCTION_MODE:-false}"
USE_HTTPS="${USE_HTTPS:-false}"
WATCH_MODE="${WATCH_MODE:-true}"

# Process tracking
FRONTEND_PID=""
BACKEND_PID=""
CLEANUP_REGISTERED=false

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Enhanced logging functions with detailed debugging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "${timestamp} - $message" >> "$LOG_DIR/launch-dev-debug-$(date '+%Y%m%d').log"
}

info() {
    echo -e "${GREEN}[INFO]${NC} $*"
    log "INFO" "$*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
    log "WARN" "$*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
    log "ERROR" "$*"
}

debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $*"
        log "DEBUG" "$*"
    fi
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
    log "SUCCESS" "$*"
}

header() {
    echo -e "${BOLD}${CYAN}$*${NC}"
    log "HEADER" "$*"
}

# Enhanced utility functions with debugging
command_exists() {
    debug "Checking if command exists: $1"
    command -v "$1" >/dev/null 2>&1
}

check_port_available() {
    local port="$1"
    debug "=== PORT AVAILABILITY CHECK FOR PORT $port ==="

    # Show current port usage
    debug "Current processes using ports:"
    if command_exists lsof; then
        lsof -i -P -n | grep LISTEN | head -10 || true
    fi

    if command_exists lsof; then
        local lsof_result=$(lsof -Pi :"$port" -sTCP:LISTEN -t 2>/dev/null || true)
        if [[ -n "$lsof_result" ]]; then
            debug "Port $port is IN USE by processes: $lsof_result"
            debug "Process details:"
            lsof -Pi :"$port" -sTCP:LISTEN 2>/dev/null || true
            return 1
        else
            debug "Port $port is AVAILABLE (lsof check)"
            return 0
        fi
    elif command_exists nc; then
        if nc -z 127.0.0.1 "$port" 2>/dev/null; then
            debug "Port $port is IN USE (nc check)"
            return 1
        else
            debug "Port $port is AVAILABLE (nc check)"
            return 0
        fi
    elif command_exists netstat; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            debug "Port $port is IN USE (netstat check)"
            netstat -tuln 2>/dev/null | grep ":$port " || true
            return 1
        else
            debug "Port $port is AVAILABLE (netstat check)"
            return 0
        fi
    else
        warn "No port checking tool available. Assuming port $port is available."
        return 0
    fi
}

find_available_port() {
    local port="$1"
    local max_attempts=100
    local attempts=0
    local original_port="$port"

    debug "=== FINDING AVAILABLE PORT STARTING FROM $port ==="

    while ! check_port_available "$port" && [[ $attempts -lt $max_attempts ]]; do
        debug "Port $port is not available, trying $((port + 1))"
        port=$((port + 1))
        attempts=$((attempts + 1))
    done

    if [[ $attempts -eq $max_attempts ]]; then
        error "Could not find available port after $max_attempts attempts from $original_port"
        exit 1
    fi

    debug "Found available port: $port (after $attempts attempts)"
    echo "$port"
}

# Environment setup functions (simplified for debugging)
setup_directories() {
    info "Setting up directory structure..."

    local dirs=(
        "$LOG_DIR"
        "$CONFIG_DIR"
        "$SCRIPT_DIR/data"
        "$SCRIPT_DIR/data/storage"
        "$SCRIPT_DIR/data/evidence"
        "$SCRIPT_DIR/data/vectors"
        "$SCRIPT_DIR/uploads"
        "$SCRIPT_DIR/output"
        "$SCRIPT_DIR/workflow_storage"
        "$SCRIPT_DIR/data/kg"
        "$SCRIPT_DIR/data/intake_storage"
    )

    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            debug "Created directory: $dir"
        fi
    done

    success "Directory structure ready"
}

setup_node_environment() {
    info "Setting up Node.js environment..."

    # Check Node.js version
    if ! command_exists node; then
        error "Node.js is required but not found. Please install Node.js 18+."
        exit 1
    fi

    local node_version
    node_version=$(node --version | sed 's/v//')
    local major_version=$(echo "$node_version" | cut -d'.' -f1)

    if [[ "$major_version" -lt 18 ]]; then
        error "Node.js 18+ is required. Found: v$node_version"
        exit 1
    fi

    info "Found Node.js v$node_version"

    # Check npm
    if ! command_exists npm; then
        error "npm is required but not found"
        exit 1
    fi

    info "Found npm $(npm --version)"

    success "Node.js environment ready"
}

setup_python_environment() {
    info "Setting up Python environment..."

    # Check Python version
    local python_cmd=""
    if command_exists python3; then
        python_cmd=python3
    elif command_exists python; then
        python_cmd=python
    else
        error "Python is required but not found. Install Python 3.9+."
        exit 1
    fi

    local python_version
    python_version=$($python_cmd --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
    info "Found Python $python_version"

    # Verify Python version compatibility
    local major=$(echo "$python_version" | cut -d'.' -f1)
    local minor=$(echo "$python_version" | cut -d'.' -f2)

    if [[ "$major" -lt 3 ]] || [[ "$major" -eq 3 && "$minor" -lt 9 ]]; then
        error "Python 3.9+ is required. Found: $python_version"
        exit 1
    fi

    # Activate virtual environment if it exists
    if [[ -d "$SCRIPT_DIR/law_venv" ]]; then
        info "Activating virtual environment: law_venv"
        source "$SCRIPT_DIR/law_venv/bin/activate"
        export PYTHON_CMD="$SCRIPT_DIR/law_venv/bin/python"
        export PIP_CMD="$SCRIPT_DIR/law_venv/bin/pip"
    elif [[ -d "$SCRIPT_DIR/venv" ]]; then
        info "Activating virtual environment: venv"
        source "$SCRIPT_DIR/venv/bin/activate"
        export PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"
        export PIP_CMD="$SCRIPT_DIR/venv/bin/pip"
    else
        warn "No virtual environment found. Using system Python."
        export PYTHON_CMD="$python_cmd"
        export PIP_CMD="${python_cmd/python/pip}"
    fi

    success "Python environment ready"
}

# Simplified main execution for debugging
main() {
    header "🚀 LawyerFactory Development Environment - DEBUG MODE"
    info "Debug version with enhanced logging enabled"

    # Initialize logging and directories
    setup_directories

    # Find available ports if needed
    info "=== PORT ALLOCATION DEBUG ==="
    info "Requested frontend port: $FRONTEND_PORT"
    info "Requested backend port: $BACKEND_PORT"

    FRONTEND_PORT=$(find_available_port "$FRONTEND_PORT")
    BACKEND_PORT=$(find_available_port "$BACKEND_PORT")

    info "Allocated frontend port: $FRONTEND_PORT"
    info "Allocated backend port: $BACKEND_PORT"

    # Setup environments
    setup_node_environment
    setup_python_environment

    # Show system info after detection is complete
    show_system_info() {
        header "System Configuration"
        info "  Frontend (React + Vite): http://localhost:$FRONTEND_PORT"
        info "  Backend (Flask + Socket.IO): http://localhost:$BACKEND_PORT"
        info "  Environment: $ENVIRONMENT"
        info "  Node ENV: $NODE_ENV"
        info "  Python CMD: $PYTHON_CMD"
        info "  Log Directory: $LOG_DIR"
    }

    show_system_info

    if [[ "$DRY_RUN" == "false" ]]; then
        # Start services
        start_backend_server
        start_frontend_server

        # Display success information
        header "🎉 LawyerFactory Development Environment Ready!"
        echo ""
        info "📊 Application URLs:"
        info "  • Frontend: ${BOLD}http://localhost:$FRONTEND_PORT${NC}"
        info "  • Backend API: http://localhost:$BACKEND_PORT/api/health"
        info "  • Socket.IO: ws://localhost:$BACKEND_PORT"
        echo ""
        info "🔧 Development Features:"
        info "  • Hot Reload: ${WATCH_MODE:-true}"
        info "  • Debug Mode: ${DEBUG:-true}"
        info "  • Environment: $ENVIRONMENT"
        info "  • Node ENV: $NODE_ENV"
        echo ""
        info "📝 Process Information:"
        info "  • Frontend PID: $FRONTEND_PID (React + Vite)"
        info "  • Backend PID: $BACKEND_PID (Flask + Socket.IO)"
        info "  • Log Directory: $LOG_DIR"
        echo ""
        info "🛑 To stop: Press Ctrl+C or kill PIDs above"
        echo ""
        info "Debug log: $LOG_DIR/launch-dev-debug-$(date '+%Y%m%d').log"

        # Keep script running and monitor processes
        info "System is running. Monitoring processes..."

        while true; do
            # Check if processes are still running
            if [[ -n "$FRONTEND_PID" ]] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
                error "Frontend process died unexpectedly"
                break
            fi

            if [[ -n "$BACKEND_PID" ]] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
                error "Backend process died unexpectedly"
                break
            fi

            sleep 5
        done

    else
        success "🧪 DRY RUN completed successfully - no services started"
        info "Would have started:"
        info "  • Frontend: React + Vite on port $FRONTEND_PORT"
        info "  • Backend: Flask + Socket.IO on port $BACKEND_PORT"
    fi
}

start_backend_server() {
    info "=== BACKEND SERVER STARTUP ==="
    debug "Backend directory: $BACKEND_DIR"
    debug "Python command: $PYTHON_CMD"
    debug "Port to use: $BACKEND_PORT"

    cd "$BACKEND_DIR"

    local server_file
    if [[ -f "simple_server.py" ]]; then
        server_file="simple_server.py"
        debug "Found backend server file: simple_server.py"
    elif [[ -f "server.py" ]]; then
        server_file="server.py"
        debug "Found backend server file: server.py"
    else
        error "No backend server file found!"
        ls -la "$BACKEND_DIR" | grep -E "\.(py)$" || true
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would start backend: $PYTHON_CMD $server_file"
        return 0
    fi

    # Create backend log file
    local backend_log="$LOG_DIR/backend-debug-$(date '+%Y%m%d-%H%M%S').log"

    # Start backend server in background
    info "Starting backend: $PYTHON_CMD $server_file"
    $PYTHON_CMD "$server_file" > "$backend_log" 2>&1 &
    BACKEND_PID=$!

    # Wait for backend to start
    local max_wait=30
    local wait_count=0

    info "Waiting for backend to start (PID: $BACKEND_PID)..."
    while [[ $wait_count -lt $max_wait ]]; do
        if ! check_port_available "$BACKEND_PORT"; then
            # Test if backend is responding
            if command_exists curl; then
                local health_url="http://localhost:$BACKEND_PORT/api/health"
                if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
                    success "✓ Backend server started successfully (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
                    debug "Backend log: $backend_log"
                    return 0
                fi
            else
                success "✓ Backend server started (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
                debug "Backend log: $backend_log"
                return 0
            fi
        fi

        # Check if process is still running
        if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            error "Backend process died unexpectedly"
            if [[ -f "$backend_log" ]]; then
                error "Backend log:"
                tail -20 "$backend_log" | sed 's/^/  /'
            fi
            return 1
        fi

        sleep 1
        wait_count=$((wait_count + 1))
        debug "Backend startup wait: $wait_count/$max_wait"
    done

    error "Backend server failed to start within $max_wait seconds"
    if [[ -f "$backend_log" ]]; then
        error "Backend log:"
        tail -20 "$backend_log" | sed 's/^/  /'
    fi
    return 1
}

start_frontend_server() {
    info "=== FRONTEND SERVER STARTUP ==="
    debug "Frontend directory: $VITE_APP_DIR"
    debug "Port to use: $FRONTEND_PORT"

    cd "$VITE_APP_DIR"

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would start frontend: VITE_PORT=$FRONTEND_PORT npm run dev"
        return 0
    fi

    # Create frontend log file
    local frontend_log="$LOG_DIR/frontend-debug-$(date '+%Y%m%d-%H%M%S').log"

    # Set Vite environment variables
    export VITE_API_URL="http://localhost:$BACKEND_PORT"
    export VITE_WS_URL="ws://localhost:$BACKEND_PORT"
    export VITE_ENVIRONMENT="$ENVIRONMENT"

    # Start Vite development server
    info "Starting Vite development server..."
    VITE_PORT="$FRONTEND_PORT" npm run dev > "$frontend_log" 2>&1 &
    FRONTEND_PID=$!

    # Wait for frontend to start
    local max_wait=60
    local wait_count=0

    info "Waiting for frontend to start (PID: $FRONTEND_PID)..."
    while [[ $wait_count -lt $max_wait ]]; do
        if ! check_port_available "$FRONTEND_PORT"; then
            # Test if frontend is responding
            if command_exists curl; then
                local frontend_url="http://localhost:$FRONTEND_PORT"
                if curl -s --max-time 2 "$frontend_url" >/dev/null 2>&1; then
                    success "✓ Frontend server started successfully (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
                    debug "Frontend log: $frontend_log"
                    return 0
                fi
            else
                success "✓ Frontend server started (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
                debug "Frontend log: $frontend_log"
                return 0
            fi
        fi

        # Check if process is still running
        if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            error "Frontend process died unexpectedly"
            if [[ -f "$frontend_log" ]]; then
                error "Frontend log:"
                tail -20 "$frontend_log" | sed 's/^/  /'
            fi
            return 1
        fi

        sleep 1
        wait_count=$((wait_count + 1))
        debug "Frontend startup wait: $wait_count/$max_wait"
    done

    error "Frontend server failed to start within $max_wait seconds"
    if [[ -f "$frontend_log" ]]; then
        error "Frontend log:"
        tail -20 "$frontend_log" | sed 's/^/  /'
    fi
    return 1
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi