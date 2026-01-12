#!/usr/bin/env bash

# LawyerFactory Production-Grade Launch Orchestrator
# Zero-defect deployment pipeline with comprehensive monitoring
# Version: 6.0.0 - Soviet Industrial Command Center Edition
# Enhanced with automatic recovery, dependency validation, and comprehensive diagnostics

set -euo pipefail

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

SCRIPT_VERSION="6.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"
HEALTH_DIR="$SCRIPT_DIR/.health"
DATA_DIR="$SCRIPT_DIR/data"
UPLOADS_DIR="$SCRIPT_DIR/uploads"
WORKFLOW_DIR="$SCRIPT_DIR/workflow_storage"
OUTPUT_DIR="$SCRIPT_DIR/output"

# Environment Detection
ENVIRONMENT="${ENVIRONMENT:-development}"
NODE_ENV="${NODE_ENV:-development}"

# Service Configuration
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-5000}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
HEALTH_CHECK_INTERVAL=3
MAX_HEALTH_RETRIES=20
SERVICE_TIMEOUT=100
DEPENDENCY_TIMEOUT=60

# Process Control
BACKEND_PID=""
FRONTEND_PID=""
QDRANT_PID=""
HEALTH_MONITOR_PID=""
CLEANUP_REGISTERED=false
QDRANT_STARTED=false

# Color System (Soviet Industrial Aesthetic)
readonly COLOR_BRASS='\033[38;2;184;115;51m'
readonly COLOR_CRIMSON='\033[38;2;220;20;60m'
readonly COLOR_EMERALD='\033[38;2;0;86;63m'
readonly COLOR_SILVER='\033[38;2;192;192;192m'
readonly COLOR_AMBER='\033[38;2;255;176;0m'
readonly COLOR_STEEL='\033[38;2;30;33;36m'
readonly COLOR_RESET='\033[0m'

# =============================================================================
# LOGGING & OUTPUT SYSTEM
# =============================================================================

setup_logging() {
    mkdir -p "$LOG_DIR" "$PID_DIR" "$HEALTH_DIR"
    
    # Master log with timestamp
    readonly MASTER_LOG="$LOG_DIR/production-$(date '+%Y%m%d-%H%M%S').log"
    readonly HEALTH_LOG="$LOG_DIR/health-monitor.log"
    
    # Redirect all output to log while preserving terminal output
    exec 1> >(tee -a "$MASTER_LOG")
    exec 2> >(tee -a "$MASTER_LOG" >&2)
}

log_message() {
    local level="$1"
    local message="$2"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S UTC')"
    
    case "$level" in
        "SYSTEM")   echo -e "${COLOR_BRASS}[SYSTEM]${COLOR_RESET} ${COLOR_SILVER}$message${COLOR_RESET}" ;;
        "SUCCESS")  echo -e "${COLOR_EMERALD}[SUCCESS]${COLOR_RESET} $message" ;;
        "WARNING")  echo -e "${COLOR_AMBER}[WARNING]${COLOR_RESET} $message" ;;
        "ERROR")    echo -e "${COLOR_CRIMSON}[ERROR]${COLOR_RESET} $message" ;;
        "HEALTH")   echo -e "${COLOR_STEEL}[HEALTH]${COLOR_RESET} $message" >> "$HEALTH_LOG" ;;
        *)          echo -e "${COLOR_SILVER}[INFO]${COLOR_RESET} $message" ;;
    esac
}

# =============================================================================
# SYSTEM HEALTH MONITORING
# =============================================================================

create_required_directories() {
    log_message "SYSTEM" "📁 Creating required directory structure..."
    
    local required_dirs=(
        "$LOG_DIR"
        "$PID_DIR"
        "$HEALTH_DIR"
        "$DATA_DIR"
        "$DATA_DIR/evidence"
        "$DATA_DIR/kg"
        "$DATA_DIR/storage"
        "$DATA_DIR/vectors"
        "$UPLOADS_DIR"
        "$WORKFLOW_DIR"
        "$OUTPUT_DIR"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_message "SUCCESS" "  ✅ Created: $dir"
        fi
    done
}

validate_dependencies() {
    log_message "SYSTEM" "🔍 Validating system dependencies..."
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    fi
    
    # Check Node.js
    if ! command -v node >/dev/null 2>&1; then
        missing_deps+=("node")
    fi
    
    # Check npm
    if ! command -v npm >/dev/null 2>&1; then
        missing_deps+=("npm")
    fi
    
    # Check curl for health checks
    if ! command -v curl >/dev/null 2>&1; then
        log_message "WARNING" "curl not found - health checks may be limited"
    fi
    
    # Check lsof for port management
    if ! command -v lsof >/dev/null 2>&1; then
        log_message "WARNING" "lsof not found - port detection may be limited"
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_message "ERROR" "Missing required dependencies: ${missing_deps[*]}"
        log_message "ERROR" "Please install missing dependencies and retry"
        return 1
    fi
    
    log_message "SUCCESS" "✅ All required dependencies present"
}

check_qdrant_service() {
    if check_port_health "$QDRANT_PORT" "qdrant"; then
        log_message "SUCCESS" "✅ Qdrant vector database already running on port $QDRANT_PORT"
        return 0
    fi
    
    log_message "WARNING" "Qdrant not running - attempting to start..."
    
    # Try Docker-based Qdrant
    if command -v docker >/dev/null 2>&1; then
        # Check if Qdrant container exists
        if docker ps -a --format '{{.Names}}' | grep -q '^qdrant$'; then
            log_message "SYSTEM" "Found existing Qdrant container, starting..."
            docker start qdrant >/dev/null 2>&1 || {
                log_message "WARNING" "Failed to start existing container, recreating..."
                docker rm -f qdrant >/dev/null 2>&1
            }
        fi
        
        # Start Qdrant if not running
        if ! docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
            log_message "SYSTEM" "Launching Qdrant container..."
            docker run -d --name qdrant \
                -p "${QDRANT_PORT}:6333" \
                -v "$DATA_DIR/vectors:/qdrant/storage" \
                qdrant/qdrant >/dev/null 2>&1 && {
                QDRANT_STARTED=true
                QDRANT_PID=$(docker inspect -f '{{.State.Pid}}' qdrant)
                log_message "SUCCESS" "✅ Qdrant started via Docker"
                
                # Wait for Qdrant to be ready
                local retry=0
                while [[ $retry -lt 10 ]]; do
                    if check_port_health "$QDRANT_PORT" "qdrant"; then
                        return 0
                    fi
                    sleep 1
                    ((retry++))
                done
            }
        fi
    fi
    
    log_message "WARNING" "⚠️  Qdrant not available - vector features will be limited"
    log_message "SYSTEM" "To enable Qdrant: docker run -p 6333:6333 qdrant/qdrant"
    return 0
}

# =============================================================================
# SYSTEM HEALTH MONITORING
# =============================================================================

check_port_health() {
    local port="$1"
    local service="$2"
    
    if command -v nc >/dev/null 2>&1; then
        if nc -z localhost "$port" 2>/dev/null; then
            return 0
        fi
    elif command -v lsof >/dev/null 2>&1; then
        if lsof -i:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

check_service_health() {
    local service="$1"
    local port="$2"
    local endpoint="$3"
    
    # Port check
    if ! check_port_health "$port" "$service"; then
        return 1
    fi
    
    # HTTP health check
    if command -v curl >/dev/null 2>&1; then
        local response
        response=$(curl -s --connect-timeout 5 --max-time 10 "$endpoint" 2>/dev/null || echo "FAIL")
        if [[ "$response" != "FAIL" ]]; then
            echo "$(date '+%H:%M:%S') $service: ✓ HEALTHY" > "$HEALTH_DIR/$service.status"
            return 0
        fi
    fi
    
    echo "$(date '+%H:%M:%S') $service: ✗ UNHEALTHY" > "$HEALTH_DIR/$service.status"
    return 1
}

continuous_health_monitor() {
    while true; do
        local backend_healthy=false
        local frontend_healthy=false
        
        # Check backend health
        if check_service_health "backend" "$BACKEND_PORT" "http://localhost:$BACKEND_PORT/api/health"; then
            backend_healthy=true
        fi
        
        # Check frontend health
        if check_service_health "frontend" "$FRONTEND_PORT" "http://localhost:$FRONTEND_PORT/"; then
            frontend_healthy=true
        fi
        
        # System status report
        local status_emoji="🔴"
        if $backend_healthy && $frontend_healthy; then
            status_emoji="🟢"
        elif $backend_healthy || $frontend_healthy; then
            status_emoji="🟡"
        fi
        
        log_message "HEALTH" "$status_emoji Backend: $($backend_healthy && echo "✓" || echo "✗") | Frontend: $($frontend_healthy && echo "✓" || echo "✗")"
        
        sleep "$HEALTH_CHECK_INTERVAL"
    done
}

# =============================================================================
# ENVIRONMENT PREPARATION
# =============================================================================

validate_environment() {
    log_message "SYSTEM" "🔧 Validating system environment..."
    
    # Create required directories first
    create_required_directories
    
    # Validate system dependencies
    validate_dependencies
    
    # Check Python virtual environment
    if [[ ! -f "$SCRIPT_DIR/law_venv/bin/activate" ]]; then
        log_message "WARNING" "Python virtual environment not found, creating..."
        python3 -m venv "$SCRIPT_DIR/law_venv" || {
            log_message "ERROR" "Failed to create virtual environment"
            return 1
        }
    fi
    
    # Check Node.js version
    local node_version=$(node -v | sed 's/v//')
    local node_major=$(echo "$node_version" | cut -d. -f1)
    if [[ $node_major -lt 16 ]]; then
        log_message "WARNING" "Node.js version $node_version detected (minimum: v16.0.0)"
    fi
    
    # Check required directories
    local required_dirs=("apps/api" "apps/ui/react-app" "src/lawyerfactory")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
            log_message "ERROR" "Required directory missing: $dir"
            return 1
        fi
    done
    
    # Check critical files
    local critical_files=(
        "apps/api/server.py"
        "apps/ui/react-app/package.json"
        "apps/ui/react-app/vite.config.js"
    )
    for file in "${critical_files[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
            log_message "ERROR" "Critical file missing: $file"
            return 1
        fi
    done
    
    # Check for .env file
    if [[ ! -f "$SCRIPT_DIR/.env" ]] && [[ ! -f "$SCRIPT_DIR/law_venv/.env" ]]; then
        log_message "WARNING" "No .env file found - using defaults"
        log_message "SYSTEM" "Create .env with API keys for full functionality"
    fi
    
    log_message "SUCCESS" "✅ Environment validation complete"
}

activate_python_environment() {
    log_message "SYSTEM" "🐍 Activating Python virtual environment..."
    
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/law_venv/bin/activate"
    
    # Load environment variables from multiple possible locations
    local env_loaded=false
    
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        set -a
        # shellcheck disable=SC1091
        source "$SCRIPT_DIR/.env"
        set +a
        env_loaded=true
        log_message "SUCCESS" "  ✅ Loaded .env from project root"
    fi
    
    if [[ -f "$SCRIPT_DIR/law_venv/.env" ]]; then
        set -a
        # shellcheck disable=SC1091
        source "$SCRIPT_DIR/law_venv/.env"
        set +a
        env_loaded=true
        log_message "SUCCESS" "  ✅ Loaded .env from law_venv/"
    fi
    
    if [[ "$env_loaded" == "false" ]]; then
        log_message "WARNING" "  ⚠️  No .env file loaded - using system defaults"
    fi
    
    # Set Python path
    export PYTHONPATH="$SCRIPT_DIR/src:${PYTHONPATH:-}"
    
    # Verify Python environment
    local python_version=$(python --version 2>&1 | awk '{print $2}')
    log_message "SUCCESS" "✅ Python environment activated (v$python_version)"
    
    # Check for required Python packages
    if ! python -c "import flask" 2>/dev/null; then
        log_message "WARNING" "Flask not installed - installing dependencies..."
        pip install -q -r "$SCRIPT_DIR/requirements.txt" || {
            log_message "ERROR" "Failed to install Python dependencies"
            return 1
        }
    fi
}

prepare_frontend_dependencies() {
    log_message "SYSTEM" "⚛️  Preparing React frontend dependencies..."
    
    cd "$SCRIPT_DIR/apps/ui/react-app"
    
    # Ensure clean node_modules
    if [[ -f "package-lock.json" ]] && [[ -d "node_modules" ]]; then
        local lock_time=$(stat -c %Y package-lock.json 2>/dev/null || stat -f %m package-lock.json)
        local modules_time=$(stat -c %Y node_modules 2>/dev/null || stat -f %m node_modules)
        
        if [[ $lock_time -gt $modules_time ]]; then
            log_message "SYSTEM" "📦 Package lock newer than node_modules, reinstalling..."
            rm -rf node_modules
        fi
    fi
    
    # Install/update dependencies
    if [[ ! -d "node_modules" ]] || [[ ! -f "node_modules/.bin/vite" ]]; then
        npm ci --silent
    fi
    
    # Verify Vite executable
    if [[ ! -f "node_modules/.bin/vite" ]]; then
        log_message "ERROR" "Vite executable missing after npm install"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    log_message "SUCCESS" "✅ Frontend dependencies ready"
}

# =============================================================================
# SERVICE ORCHESTRATION
# =============================================================================

start_backend_service() {
    log_message "SYSTEM" "🚀 Starting LawyerFactory Backend (Flask + Socket.IO)"
    
    cd "$SCRIPT_DIR/apps/api"
    
    # Start backend server with explicit port
    python server.py --port $BACKEND_PORT > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    
    echo "$BACKEND_PID" > "$PID_DIR/backend.pid"
    
    # Wait for backend startup
    local retry_count=0
    while [[ $retry_count -lt $MAX_HEALTH_RETRIES ]]; do
        if check_port_health "$BACKEND_PORT" "backend"; then
            log_message "SUCCESS" "✅ Backend service started (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
            return 0
        fi
        
        # Check if process still running
        if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            log_message "ERROR" "Backend process died during startup - check $LOG_DIR/backend.log"
            return 1
        fi
        
        sleep 2
        ((retry_count++))
    done
    
    log_message "ERROR" "Backend failed to start within timeout"
    return 1
}

start_frontend_service() {
    log_message "SYSTEM" "⚛️  Starting React Frontend (Vite Development Server)"
    
    cd "$SCRIPT_DIR/apps/ui/react-app"
    
    # Set backend URL for frontend and start Vite dev server with explicit port/host
    VITE_BACKEND_URL="http://localhost:$BACKEND_PORT" npm run dev -- --port $FRONTEND_PORT --host > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    
    echo "$FRONTEND_PID" > "$PID_DIR/frontend.pid"
    
    # Wait for frontend startup
    local retry_count=0
    while [[ $retry_count -lt $MAX_HEALTH_RETRIES ]]; do
        if check_port_health "$FRONTEND_PORT" "frontend"; then
            log_message "SUCCESS" "✅ Frontend service started (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
            return 0
        fi
        
        # Check if process still running
        if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            log_message "ERROR" "Frontend process died during startup - check $LOG_DIR/frontend.log"
            return 1
        fi
        
        sleep 2
        ((retry_count++))
    done
    
    log_message "ERROR" "Frontend failed to start within timeout"
    return 1
}

start_health_monitoring() {
    log_message "SYSTEM" "💊 Starting continuous health monitoring..."
    
    continuous_health_monitor &
    HEALTH_MONITOR_PID=$!
    
    echo "$HEALTH_MONITOR_PID" > "$PID_DIR/health-monitor.pid"
    log_message "SUCCESS" "✅ Health monitoring active (PID: $HEALTH_MONITOR_PID)"
}

# =============================================================================
# CLEANUP & SIGNAL HANDLING
# =============================================================================

open_browser() {
    local url="http://localhost:$FRONTEND_PORT"
    
    # Wait a moment for services to stabilize
    sleep 2
    
    log_message "SYSTEM" "🌐 Opening browser to $url..."
    
    # Detect OS and open browser
    case "$(uname -s)" in
        Darwin*)
            open "$url" 2>/dev/null || log_message "WARNING" "Failed to open browser automatically"
            ;;
        Linux*)
            if command -v xdg-open >/dev/null 2>&1; then
                xdg-open "$url" 2>/dev/null || log_message "WARNING" "Failed to open browser automatically"
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            start "$url" 2>/dev/null || log_message "WARNING" "Failed to open browser automatically"
            ;;
        *)
            log_message "WARNING" "Unknown OS - please open $url manually"
            ;;
    esac
}

# =============================================================================
# CLEANUP & SIGNAL HANDLING
# =============================================================================

cleanup_processes() {
    log_message "SYSTEM" "🧹 Shutting down LawyerFactory services..."
    
    # Stop health monitor
    if [[ -n "$HEALTH_MONITOR_PID" ]] && kill -0 "$HEALTH_MONITOR_PID" 2>/dev/null; then
        kill "$HEALTH_MONITOR_PID" 2>/dev/null || true
        log_message "SUCCESS" "  ✅ Health monitor stopped"
    fi
    
    # Stop frontend
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
        log_message "SUCCESS" "  ✅ Frontend stopped"
    fi
    
    # Stop backend
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
        log_message "SUCCESS" "  ✅ Backend stopped"
    fi
    
    # Stop Qdrant if we started it
    if [[ "$QDRANT_STARTED" == "true" ]] && command -v docker >/dev/null 2>&1; then
        if docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
            docker stop qdrant >/dev/null 2>&1 || true
            log_message "SUCCESS" "  ✅ Qdrant stopped"
        fi
    fi
    
    # Cleanup PID files
    rm -f "$PID_DIR"/*.pid
    rm -f "$HEALTH_DIR"/*.status
    
    log_message "SUCCESS" "✅ LawyerFactory shutdown complete"
    log_message "SYSTEM" ""
}

register_cleanup() {
    if [[ "$CLEANUP_REGISTERED" == "false" ]]; then
        trap cleanup_processes EXIT INT TERM
        CLEANUP_REGISTERED=true
    fi
}

# =============================================================================
# MAIN ORCHESTRATION LOGIC
# =============================================================================

display_banner() {
    cat << 'EOF'
 ╔══════════════════════════════════════════════════════════════╗
║                                                               ║
║    ██████╗ ██████╗ ██╗███████╗███████╗                        ║
║    ██╔══██╗██╔══██╗██║██╔════╝██╔════╝                        ║
║    ██████╔╝██████╔╝██║█████╗  █████╗                          ║
║    ██╔══██╗██╔══██╗██║██╔══╝  ██╔══╝                          ║
║    ██████╔╝██║  ██║██║███████╗██║                             ║
║    ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝                             ║
║                                                               ║
║       ██████╗ █████╗ ███████╗███████╗██████╗                  ║
║      ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗                 ║
║      ██║     ███████║███████╗█████╗  ██████╔╝                 ║
║      ██║     ██╔══██║╚════██║██╔══╝  ██╔══██╗                 ║
║      ╚██████╗██║  ██║███████║███████╗██║  ██║                 ║
║       ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝                 ║
║                                                               ║
║              Industrial Command Center v5.0.0                 ║
║                    Production-Grade Release                   ║
 ╚══════════════════════════════════════════════════════════════╝  
EOF
}

display_system_status() {
    log_message "SYSTEM" ""
    log_message "SYSTEM" "🏭 LawyerFactory Development Environment v$SCRIPT_VERSION"
    log_message "SYSTEM" "┌─────────────────────────────────────────────────────────────┐"
    log_message "SYSTEM" "│  Environment: $ENVIRONMENT (Node: $NODE_ENV)"
    log_message "SYSTEM" "│  Frontend:    http://localhost:$FRONTEND_PORT (React + Vite)"
    log_message "SYSTEM" "│  Backend:     http://localhost:$BACKEND_PORT (Flask + Socket.IO)"
    log_message "SYSTEM" "│  Vector DB:   http://localhost:$QDRANT_PORT (Qdrant)"
    log_message "SYSTEM" "│  Health API:  http://localhost:$BACKEND_PORT/api/health"
    log_message "SYSTEM" "│  WebSocket:   ws://localhost:$BACKEND_PORT"
    log_message "SYSTEM" "│  Monitoring:  $HEALTH_CHECK_INTERVAL second intervals"
    log_message "SYSTEM" "│  Logs:        $LOG_DIR/"
    log_message "SYSTEM" "│  Data:        $DATA_DIR/"
    log_message "SYSTEM" "│  Uploads:     $UPLOADS_DIR/"
    log_message "SYSTEM" "│  Workflows:   $WORKFLOW_DIR/"
    log_message "SYSTEM" "│  Output:      $OUTPUT_DIR/"
    log_message "SYSTEM" "└─────────────────────────────────────────────────────────────┘"
    log_message "SYSTEM" ""
}

main() {
    display_banner
    setup_logging
    register_cleanup
    
    log_message "SYSTEM" "🚀 Initiating LawyerFactory Development Launch Sequence..."
    log_message "SYSTEM" ""
    
    # Phase 1: Environment Validation & Setup
    log_message "SYSTEM" "📋 Phase 1: Environment Validation & Setup"
    validate_environment
    activate_python_environment
    check_qdrant_service
    prepare_frontend_dependencies
    log_message "SUCCESS" "✅ Phase 1 Complete: Environment Ready"
    log_message "SYSTEM" ""
    
    # Phase 2: Service Orchestration
    log_message "SYSTEM" "🔧 Phase 2: Service Orchestration"
    display_system_status
    
    # Check return codes to fail fast on startup issues
    if ! start_backend_service; then
        log_message "ERROR" "Aborting launch due to backend startup failure"
        exit 1
    fi
    if ! start_frontend_service; then
        log_message "ERROR" "Aborting launch due to frontend startup failure"
        exit 1
    fi
    start_health_monitoring
    log_message "SUCCESS" "✅ Phase 2 Complete: All Services Running"
    log_message "SYSTEM" ""
    
    # Phase 3: System Ready
    log_message "SUCCESS" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_message "SUCCESS" "🎉 LawyerFactory Development Environment Ready!"
    log_message "SUCCESS" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_message "SUCCESS" ""
    log_message "SUCCESS" "🌐 Frontend:  http://localhost:$FRONTEND_PORT"
    log_message "SUCCESS" "⚡ Backend:   http://localhost:$BACKEND_PORT"
    log_message "SUCCESS" "🔍 Health:    http://localhost:$BACKEND_PORT/api/health"
    log_message "SYSTEM" ""
    log_message "SYSTEM" "📊 System Status: All services monitored - Press Ctrl+C to shutdown"
    log_message "SYSTEM" "📁 Logs available at: $LOG_DIR/"
    log_message "SYSTEM" ""
    
    # Open browser automatically
    open_browser &
    
    # Wait for services (blocks until interrupted)
    wait
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@"
