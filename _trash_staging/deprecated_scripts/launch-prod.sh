#!/usr/bin/env bash

# LawyerFactory Production Environment Launcher v4.0.0
# Canonical production launch script for Briefcaser + LawyerFactory backend
# Optimized for production deployment with security and performance features
# Usage: ./launch-prod.sh [options]

set -euo pipefail

# Script metadata
readonly SCRIPT_VERSION="4.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="$SCRIPT_DIR/logs"
readonly CONFIG_DIR="$SCRIPT_DIR/configs"
readonly VITE_APP_DIR="$SCRIPT_DIR/apps/ui/react-app"
readonly BACKEND_DIR="$SCRIPT_DIR/apps/api"

# Environment detection
ENVIRONMENT="${ENVIRONMENT:-production}"
NODE_ENV="${NODE_ENV:-production}"

# Default configuration
FRONTEND_PORT="${FRONTEND_PORT:-80}"    # Standard HTTP port for production
BACKEND_PORT="${BACKEND_PORT:-5000}"
SKIP_DEPS="${SKIP_DEPS:-false}"
VERBOSE="${VERBOSE:-false}"
DRY_RUN="${DRY_RUN:-false}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
SETUP_MODE="${SETUP_MODE:-false}"
OPEN_BROWSER="${OPEN_BROWSER:-false}"  # Don't auto-open in production
USE_SSL="${USE_SSL:-false}"
SSL_CERT_PATH="${SSL_CERT_PATH:-}"
SSL_KEY_PATH="${SSL_KEY_PATH:-}"

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

# Logging functions with timestamp and file logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "${timestamp} - [$level] $message" >> "$LOG_DIR/launch-prod-$(date '+%Y%m%d').log"
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

# Utility functions
command_exists() { command -v "$1" >/dev/null 2>&1; }

check_port_available() {
    local port="$1"
    if command_exists lsof; then
        ! lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1
    elif command_exists nc; then
        ! nc -z 127.0.0.1 "$port" 2>/dev/null
    elif command_exists netstat; then
        ! netstat -tuln 2>/dev/null | grep -q ":$port "
    else
        warn "No port checking tool available. Assuming port $port is available."
        return 0
    fi
}

find_available_port() {
    local port="$1"
    local max_attempts=100
    local attempts=0
    
    while ! check_port_available "$port" && [[ $attempts -lt $max_attempts ]]; do
        port=$((port + 1))
        attempts=$((attempts + 1))
    done
    
    if [[ $attempts -eq $max_attempts ]]; then
        error "Could not find available port starting from $1"
        exit 1
    fi
    
    echo "$port"
}

# Environment setup functions
setup_directories() {
    info "Setting up production directory structure..."
    
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
        "$SCRIPT_DIR/backups"
        "$SCRIPT_DIR/ssl"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            debug "Created directory: $dir"
        fi
    done
    
    # Set secure permissions for production
    chmod 750 "$LOG_DIR" "$CONFIG_DIR" "$SCRIPT_DIR/data"
    chmod 700 "$SCRIPT_DIR/ssl" 2>/dev/null || true
    
    # Set up logs with rotation
    if [[ -f "$LOG_DIR/launch-prod-$(date '+%Y%m%d').log" ]]; then
        # Rotate if file is too large (>50MB in production)
        if [[ $(stat -f%z "$LOG_DIR/launch-prod-$(date '+%Y%m%d').log" 2>/dev/null || echo 0) -gt 52428800 ]]; then
            mv "$LOG_DIR/launch-prod-$(date '+%Y%m%d').log" "$LOG_DIR/launch-prod-$(date '+%Y%m%d')-$(date '+%H%M%S').log"
        fi
    fi
    
    success "Production directory structure ready"
}

validate_production_requirements() {
    info "Validating production requirements..."
    
    local requirements_met=true
    
    # Check required environment variables
    local required_env_vars=("OPENAI_API_KEY" "JWT_SECRET_KEY" "ENCRYPTION_KEY" "SESSION_SECRET")
    for var in "${required_env_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable '$var' is not set"
            requirements_met=false
        fi
    done
    
    # Check SSL configuration if enabled
    if [[ "$USE_SSL" == "true" ]]; then
        if [[ -z "$SSL_CERT_PATH" ]] || [[ -z "$SSL_KEY_PATH" ]]; then
            error "SSL enabled but SSL_CERT_PATH or SSL_KEY_PATH not set"
            requirements_met=false
        fi
        
        if [[ ! -f "$SSL_CERT_PATH" ]]; then
            error "SSL certificate file not found: $SSL_CERT_PATH"
            requirements_met=false
        fi
        
        if [[ ! -f "$SSL_KEY_PATH" ]]; then
            error "SSL key file not found: $SSL_KEY_PATH"
            requirements_met=false
        fi
    fi
    
    # Check for production-ready dependencies
    if [[ ! -f "$VITE_APP_DIR/dist/index.html" ]]; then
        warn "Production build not found. Will build frontend..."
    fi
    
    if [[ "$requirements_met" == "false" ]]; then
        error "Production requirements not met. Please check configuration."
        exit 1
    fi
    
    success "Production requirements validated"
}

setup_node_environment() {
    info "Setting up Node.js production environment..."
    
    # Check Node.js version
    if ! command_exists node; then
        error "Node.js is required but not found. Please install Node.js 18+."
        exit 1
    fi
    
    local node_version
    node_version=$(node --version | sed 's/v//')
    local major_version=$(echo "$node_version" | cut -d'.' -f1)
    
    if [[ "$major_version" -lt 18 ]]; then
        error "Node.js 18+ is required for production. Found: v$node_version"
        exit 1
    fi
    
    info "Found Node.js v$node_version"
    
    # Check npm
    if ! command_exists npm; then
        error "npm is required but not found"
        exit 1
    fi
    
    info "Found npm $(npm --version)"
    
    success "Node.js production environment ready"
}

setup_python_environment() {
    info "Setting up Python production environment..."
    
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
        error "Python 3.9+ is required for production. Found: $python_version"
        exit 1
    fi
    
    # Use virtual environment (required for production)
    if [[ -d "$SCRIPT_DIR/law_venv" ]]; then
        info "Activating production virtual environment: law_venv"
        source "$SCRIPT_DIR/law_venv/bin/activate"
        export PYTHON_CMD="$SCRIPT_DIR/law_venv/bin/python"
        export PIP_CMD="$SCRIPT_DIR/law_venv/bin/pip"
    elif [[ -d "$SCRIPT_DIR/venv" ]]; then
        info "Activating production virtual environment: venv"
        source "$SCRIPT_DIR/venv/bin/activate"
        export PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"
        export PIP_CMD="$SCRIPT_DIR/venv/bin/pip"
    else
        error "Virtual environment required for production. Create 'law_venv' or 'venv' directory."
        exit 1
    fi
    
    success "Python production environment ready"
}

install_production_dependencies() {
    if [[ "$SKIP_DEPS" == "true" ]]; then
        info "Skipping dependency installation (--skip-deps specified)"
        return 0
    fi
    
    info "Installing production dependencies..."
    
    # Install Node.js dependencies for React app
    if [[ -d "$VITE_APP_DIR" ]]; then
        info "Installing React app production dependencies..."
        cd "$VITE_APP_DIR"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            npm ci --only=production --silent
        else
            info "[DRY RUN] Would install: npm ci --only=production"
        fi
        success "React app production dependencies installed"
    else
        error "React app directory not found: $VITE_APP_DIR"
        exit 1
    fi
    
    # Install Python dependencies for backend
    if [[ -d "$BACKEND_DIR" ]] && [[ -f "$BACKEND_DIR/requirements.txt" ]]; then
        info "Installing backend production dependencies..."
        cd "$BACKEND_DIR"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            "$PIP_CMD" install -r requirements.txt --no-cache-dir --quiet
        else
            info "[DRY RUN] Would install: $PIP_CMD install -r requirements.txt"
        fi
        success "Backend production dependencies installed"
    fi
    
    # Install root dependencies if they exist
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        info "Installing root production dependencies..."
        cd "$SCRIPT_DIR"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            "$PIP_CMD" install -r requirements.txt --no-cache-dir --quiet
        else
            info "[DRY RUN] Would install: $PIP_CMD install -r requirements.txt"
        fi
        success "Root production dependencies installed"
    fi
}

setup_production_environment() {
    info "Setting up production environment variables..."
    
    # Create production environment configuration
    local env_prod_file="$SCRIPT_DIR/.env.production"
    
    # Production environment file
    if [[ ! -f "$env_prod_file" ]] || [[ "$SETUP_MODE" == "true" ]]; then
        info "Creating .env.production configuration..."
        cat > "$env_prod_file" << EOF
# LawyerFactory Production Environment Configuration
# Generated by launch-prod.sh v$SCRIPT_VERSION on $(date)

# Environment
NODE_ENV=production
ENVIRONMENT=production
DEBUG=false

# Server Configuration
FRONTEND_PORT=$FRONTEND_PORT
BACKEND_PORT=$BACKEND_PORT
VITE_API_URL=\${VITE_API_URL:-http://localhost:$BACKEND_PORT}
VITE_WS_URL=\${VITE_WS_URL:-ws://localhost:$BACKEND_PORT}

# CORS Configuration (restrict in production)
CORS_ORIGINS=\${CORS_ORIGINS:-http://localhost:$FRONTEND_PORT}

# AI Services (Production - REQUIRED)
OPENAI_API_KEY=\${OPENAI_API_KEY}
ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
GROQ_API_KEY=\${GROQ_API_KEY}

# Legal Research APIs
COURTLISTENER_API_KEY=\${COURTLISTENER_API_KEY}

# Storage Configuration
WORKFLOW_STORAGE_PATH=\${WORKFLOW_STORAGE_PATH:-./workflow_storage}
UPLOAD_DIR=\${UPLOAD_DIR:-./uploads}
OUTPUT_DIR=\${OUTPUT_DIR:-./output}
DATA_DIR=\${DATA_DIR:-./data}

# Vector Database
QDRANT_URL=\${QDRANT_URL:-http://localhost:6333}
QDRANT_API_KEY=\${QDRANT_API_KEY}

# Security (Production - CHANGE THESE)
JWT_SECRET_KEY=\${JWT_SECRET_KEY}
ENCRYPTION_KEY=\${ENCRYPTION_KEY}
SESSION_SECRET=\${SESSION_SECRET}

# Logging
LOG_LEVEL=\${LOG_LEVEL:-INFO}
PYTHONPATH=./src:\${PYTHONPATH:-}

# Production Features
HOT_RELOAD=false
WATCH_FILES=false
AUTO_RESTART=false

# Database
DATABASE_URL=\${DATABASE_URL}

# Redis
REDIS_URL=\${REDIS_URL}

# SSL/TLS
USE_SSL=\${USE_SSL:-false}
SSL_CERT_PATH=\${SSL_CERT_PATH}
SSL_KEY_PATH=\${SSL_KEY_PATH}

# Performance
MAX_WORKERS=\${MAX_WORKERS:-4}
WORKER_TIMEOUT=\${WORKER_TIMEOUT:-30}
MEMORY_LIMIT=\${MEMORY_LIMIT:-2G}
EOF
    fi
    
    # Load production environment file
    if [[ -f "$env_prod_file" ]]; then
        set -a  # Automatically export all variables
        source "$env_prod_file"
        set +a
        debug "Loaded production environment from $env_prod_file"
    fi
    
    # Set additional runtime variables
    export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR/src"
    export NODE_ENV="production"
    export ENVIRONMENT="production"
    
    success "Production environment variables configured"
}

build_frontend() {
    info "Building React frontend for production..."
    
    cd "$VITE_APP_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would build frontend: npm run build"
        return 0
    fi
    
    # Set Vite environment variables for build
    export VITE_API_URL="http://localhost:$BACKEND_PORT"
    export VITE_WS_URL="ws://localhost:$BACKEND_PORT"
    export VITE_ENVIRONMENT="production"
    
    # Build the frontend
    info "Running production build..."
    npm run build
    
    # Verify build output
    if [[ ! -f "dist/index.html" ]]; then
        error "Frontend build failed - dist/index.html not found"
        return 1
    fi
    
    success "Frontend built successfully"
}

start_backend_server() {
    info "Starting backend server in production mode on port $BACKEND_PORT..."
    
    cd "$BACKEND_DIR"
    
    local server_file
    if [[ -f "server.py" ]]; then
        server_file="server.py"
    elif [[ -f "simple_server.py" ]]; then
        server_file="simple_server.py"
    else
        error "No backend server file found (server.py or simple_server.py)"
        return 1
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would start backend: $PYTHON_CMD $server_file"
        return 0
    fi
    
    # Create backend log file
    local backend_log="$LOG_DIR/backend-prod-$(date '+%Y%m%d-%H%M%S').log"
    
    # Start backend server in production mode
    info "Starting production backend: $PYTHON_CMD $server_file"
    FLASK_ENV=production $PYTHON_CMD "$server_file" > "$backend_log" 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    local max_wait=45
    local wait_count=0
    
    info "Waiting for backend to start (PID: $BACKEND_PID)..."
    while [[ $wait_count -lt $max_wait ]]; do
        if ! check_port_available "$BACKEND_PORT"; then
            # Test if backend is responding
            if command_exists curl; then
                if curl -s --max-time 3 "http://localhost:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
                    success "Backend server started successfully (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
                    return 0
                fi
            else
                success "Backend server started successfully (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
                return 0
            fi
        fi
        
        # Check if process is still running
        if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            error "Backend process died unexpectedly"
            if [[ -f "$backend_log" ]]; then
                error "Backend log:"
                tail -10 "$backend_log" | sed 's/^/  /'
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
    info "Starting React frontend server in production mode on port $FRONTEND_PORT..."
    
    cd "$VITE_APP_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would start frontend: npm run preview with port $FRONTEND_PORT"
        return 0
    fi
    
    # Create frontend log file
    local frontend_log="$LOG_DIR/frontend-prod-$(date '+%Y%m%d-%H%M%S').log"
    
    # Start Vite preview server for production
    info "Starting Vite production server..."
    npm run preview -- --port "$FRONTEND_PORT" --host 0.0.0.0 > "$frontend_log" 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    local max_wait=30  # Production should start faster
    local wait_count=0
    
    info "Waiting for frontend to start (PID: $FRONTEND_PID)..."
    while [[ $wait_count -lt $max_wait ]]; do
        if ! check_port_available "$FRONTEND_PORT"; then
            # Test if frontend is responding
            if command_exists curl; then
                if curl -s --head --max-time 3 "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
                    success "Frontend server started successfully (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
                    return 0
                fi
            else
                success "Frontend server started successfully (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
                return 0
            fi
        fi
        
        # Check if process is still running
        if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            error "Frontend process died unexpectedly"
            if [[ -f "$frontend_log" ]]; then
                error "Frontend log:"
                tail -10 "$frontend_log" | sed 's/^/  /'
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

perform_health_checks() {
    info "Performing production health checks..."
    
    local backend_url="http://localhost:$BACKEND_PORT"
    local frontend_url="http://localhost:$FRONTEND_PORT"
    
    # Backend health check
    if command_exists curl; then
        info "Testing backend API endpoints..."
        
        # Health endpoint
        local health_url="$backend_url/api/health"
        if curl -s --max-time 10 "$health_url" | grep -q "healthy\|status"; then
            success "✓ Backend health endpoint responding"
        else
            error "✗ Backend health endpoint not responding properly"
            return 1
        fi
        
        # Frontend health check
        info "Testing frontend server..."
        if curl -s --head --max-time 10 "$frontend_url" >/dev/null 2>&1; then
            success "✓ Frontend server responding"
        else
            error "✗ Frontend server not responding"
            return 1
        fi
        
        # Socket.IO health check
        local socketio_url="$backend_url/socket.io/?EIO=4&transport=polling"
        if curl -s --max-time 5 "$socketio_url" >/dev/null 2>&1; then
            success "✓ Socket.IO endpoint responding"
        else
            warn "✗ Socket.IO endpoint may not be responding"
        fi
        
    else
        warn "curl not available, performing basic port checks only"
        
        # Basic port checks
        if ! check_port_available "$BACKEND_PORT"; then
            success "✓ Backend port $BACKEND_PORT is active"
        else
            error "✗ Backend port $BACKEND_PORT appears inactive"
            return 1
        fi
        
        if ! check_port_available "$FRONTEND_PORT"; then
            success "✓ Frontend port $FRONTEND_PORT is active"
        else
            error "✗ Frontend port $FRONTEND_PORT appears inactive"
            return 1
        fi
    fi
    
    success "Production health checks passed"
}

register_cleanup() {
    if [[ "$CLEANUP_REGISTERED" == "true" ]]; then
        return 0
    fi
    
    trap cleanup SIGINT SIGTERM EXIT
    CLEANUP_REGISTERED=true
}

cleanup() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    info "Shutting down LawyerFactory production environment..."
    
    # Kill frontend process
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        info "Stopping frontend server (PID: $FRONTEND_PID)"
        kill "$FRONTEND_PID" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local wait_count=0
        while kill -0 "$FRONTEND_PID" 2>/dev/null && [[ $wait_count -lt 15 ]]; do
            sleep 1
            wait_count=$((wait_count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            warn "Force killing frontend process"
            kill -9 "$FRONTEND_PID" 2>/dev/null || true
        fi
    fi
    
    # Kill backend process
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        info "Stopping backend server (PID: $BACKEND_PID)"
        kill "$BACKEND_PID" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local wait_count=0
        while kill -0 "$BACKEND_PID" 2>/dev/null && [[ $wait_count -lt 15 ]]; do
            sleep 1
            wait_count=$((wait_count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            warn "Force killing backend process"
            kill -9 "$BACKEND_PID" 2>/dev/null || true
        fi
    fi
    
    success "LawyerFactory production environment shutdown complete"
}

show_usage() {
    cat << EOF
LawyerFactory Production Environment Launcher v$SCRIPT_VERSION

USAGE:
    ./launch-prod.sh [options]

OPTIONS:
    --frontend-port PORT     React production port (default: 80)
    --backend-port PORT      Flask backend port (default: 5000)
    --skip-deps             Skip dependency installation
    --setup                 Full setup including environment files
    --verbose               Enable verbose logging
    --dry-run               Show what would be done without executing
    --ssl                   Enable SSL/HTTPS
    --ssl-cert PATH         Path to SSL certificate
    --ssl-key PATH          Path to SSL private key
    --log-level LEVEL       Set log level (INFO, WARN, ERROR)
    --help                  Show this help message

EXAMPLES:
    ./launch-prod.sh                         # Start production environment
    ./launch-prod.sh --setup                 # Full setup and start
    ./launch-prod.sh --frontend-port 443 --ssl  # HTTPS production
    ./launch-prod.sh --verbose --dry-run     # Test run with verbose output

REQUIRED ENVIRONMENT VARIABLES:
    OPENAI_API_KEY          OpenAI API key
    JWT_SECRET_KEY          JWT signing secret
    ENCRYPTION_KEY          Data encryption key
    SESSION_SECRET          Session secret key

SYSTEM URLS:
    Frontend (Briefcaser):  http://localhost:80
    Backend (Flask API):    http://localhost:5000
    API Health:             http://localhost:5000/api/health
    Socket.IO:              ws://localhost:5000

FEATURES:
    ✓ Production-optimized React build with Vite
    ✓ Flask + Socket.IO backend with security hardening
    ✓ Comprehensive health checks and monitoring
    ✓ SSL/TLS support for secure communications
    ✓ Environment variable validation
    ✓ Production logging and error handling

For more information, see: README.md
EOF
}

show_system_info() {
    header "LawyerFactory Production Environment v$SCRIPT_VERSION"
    info "  Mode: ${ENVIRONMENT:-production} (Node: ${NODE_ENV:-production})"
    info "  Frontend (Briefcaser): http://localhost:$FRONTEND_PORT"
    info "  Backend (Flask + Socket.IO): http://localhost:$BACKEND_PORT"
    info "  API Health Check: http://localhost:$BACKEND_PORT/api/health"
    info "  WebSocket: ws://localhost:$BACKEND_PORT"
    
    if command_exists node; then
        info "  Node.js: $(node --version)"
    fi
    if command_exists npm; then
        info "  npm: v$(npm --version)"
    fi
    if [[ -n "${PYTHON_CMD:-}" ]]; then
        info "  Python: $($PYTHON_CMD --version 2>&1)"
    fi
    
    info "  Log Directory: $LOG_DIR"
    info "  Environment: $ENVIRONMENT"
    info "  SSL Enabled: ${USE_SSL:-false}"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --frontend-port)
                FRONTEND_PORT="$2"
                shift 2
                ;;
            --backend-port)
                BACKEND_PORT="$2"
                shift 2
                ;;
            --skip-deps)
                SKIP_DEPS="true"
                shift
                ;;
            --setup)
                SETUP_MODE="true"
                shift
                ;;
            --verbose)
                VERBOSE="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --ssl)
                USE_SSL="true"
                shift
                ;;
            --ssl-cert)
                SSL_CERT_PATH="$2"
                USE_SSL="true"
                shift 2
                ;;
            --ssl-key)
                SSL_KEY_PATH="$2"
                USE_SSL="true"
                shift 2
                ;;
            --log-level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Main execution function
main() {
    # Parse arguments first
    parse_arguments "$@"
    
    # Register cleanup handler early
    register_cleanup
    
    # Initialize directories
    setup_directories
    
    # Show header
    if [[ "$DRY_RUN" == "true" ]]; then
        header "🧪 LawyerFactory Production Environment - DRY RUN MODE"
    else
        header "🚀 Starting LawyerFactory Production Environment"
    fi
    
    # Find available ports if needed
    FRONTEND_PORT=$(find_available_port "$FRONTEND_PORT")
    BACKEND_PORT=$(find_available_port "$BACKEND_PORT")
    
    # Setup environments
    setup_node_environment
    setup_python_environment
    
    # Show system info after detection is complete
    show_system_info
    
    # Continue setup
    setup_production_environment
    validate_production_requirements
    install_production_dependencies
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Build and start services
        build_frontend
        start_backend_server
        start_frontend_server
        perform_health_checks
        
        # Display success information
        header "🎉 LawyerFactory Production Environment Ready!"
        echo ""
        info "🌐 Application URLs:"
        info "  • Briefcaser UI: ${BOLD}http://localhost:$FRONTEND_PORT${NC}"
        info "  • Backend API: http://localhost:$BACKEND_PORT/api/health"
        info "  • Socket.IO: ws://localhost:$BACKEND_PORT"
        echo ""
        info "🔒 Production Features:"
        info "  • SSL/TLS: ${USE_SSL:-false}"
        info "  • Environment: $ENVIRONMENT"
        info "  • Node ENV: $NODE_ENV"
        info "  • Debug Mode: false"
        echo ""
        info "📝 Process Information:"
        info "  • Frontend PID: $FRONTEND_PID (React Production)"
        info "  • Backend PID: $BACKEND_PID (Flask Production)"
        info "  • Log Directory: $LOG_DIR"
        echo ""
        info "🛑 To stop: Press Ctrl+C or kill PIDs above"
        
        # Keep script running and monitor processes
        info "Production system is running. Monitoring processes..."
        
        while true; do
            # Check if both processes are still running
            if [[ -n "$FRONTEND_PID" ]] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
                error "Frontend process died unexpectedly"
                break
            fi
            if [[ -n "$BACKEND_PID" ]] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
                error "Backend process died unexpectedly"
                break
            fi
            
            sleep 10  # Longer monitoring interval for production
        done
        
    else
        success "🧪 PRODUCTION DRY RUN completed successfully - no services started"
        info "Would have started:"
        info "  • Frontend: React Production Build on port $FRONTEND_PORT"
        info "  • Backend: Flask Production Mode on port $BACKEND_PORT"
    fi
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi