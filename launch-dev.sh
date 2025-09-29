#!/usr/bin/env bash

# LawyerFactory Development Environment Launcher v4.0.0
# Canonical development launch script for Briefcaser + LawyerFactory backend integration
# Consolidated from multiple launch scripts with unified functionality
# Usage: ./launch-dev.sh [options]

set -euo pipefail

# Script metadata
readonly SCRIPT_VERSION="4.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="$SCRIPT_DIR/logs"
readonly CONFIG_DIR="$SCRIPT_DIR/configs"
readonly VITE_APP_DIR="$SCRIPT_DIR/apps/ui/react-app/"
readonly BACKEND_DIR="$SCRIPT_DIR/apps/api"

# Environment detection
ENVIRONMENT="${ENVIRONMENT:-development}"
NODE_ENV="${NODE_ENV:-development}"

# Default configuration - Force real data mode, no dry-run
FRONTEND_PORT="${FRONTEND_PORT:-3000}"  # Standard development port
BACKEND_PORT="${BACKEND_PORT:-5000}"
SKIP_DEPS="${SKIP_DEPS:-false}"
VERBOSE="${VERBOSE:-false}"
DRY_RUN="false"  # Force disable dry-run mode
LOG_LEVEL="${LOG_LEVEL:-INFO}"
SETUP_MODE="${SETUP_MODE:-false}"
OPEN_BROWSER="${OPEN_BROWSER:-true}"
PRODUCTION_MODE="${PRODUCTION_MODE:-false}"
USE_HTTPS="${USE_HTTPS:-false}"
WATCH_MODE="${WATCH_MODE:-true}"
USE_REAL_DATA="true"  # Force real data usage

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
    echo "${timestamp} - $message" >> "$LOG_DIR/launch-dev-$(date '+%Y%m%d').log"
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
    
    # Set up logs with rotation
    if [[ -f "$LOG_DIR/launch-dev-$(date '+%Y%m%d').log" ]]; then
        # Rotate if file is too large (>10MB)
        if [[ $(stat -f%z "$LOG_DIR/launch-dev-$(date '+%Y%m%d').log" 2>/dev/null || echo 0) -gt 10485760 ]]; then
            mv "$LOG_DIR/launch-dev-$(date '+%Y%m%d').log" "$LOG_DIR/launch-dev-$(date '+%Y%m%d')-$(date '+%H%M%S').log"
        fi
    fi
    
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

install_dependencies() {
    if [[ "$SKIP_DEPS" == "true" ]]; then
        info "Skipping dependency installation (--skip-deps specified)"
        return 0
    fi
    
    info "Installing/updating dependencies..."
    
    # Install Node.js dependencies for React app
    if [[ -d "$VITE_APP_DIR" ]]; then
        info "Installing React app dependencies..."
        cd "$VITE_APP_DIR"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            if [[ ! -d "node_modules" ]] || [[ "$SETUP_MODE" == "true" ]]; then
                npm install
            else
                # Quick check for missing dependencies
                npm ci --only=production --silent 2>/dev/null || npm install
            fi
        else
            info "[DRY RUN] Would install: npm install"
        fi
        success "React app dependencies installed"
    else
        error "React app directory not found: $VITE_APP_DIR"
        exit 1
    fi
    
    # Install Python dependencies for backend
    if [[ -d "$BACKEND_DIR" ]] && [[ -f "$BACKEND_DIR/requirements.txt" ]]; then
        info "Installing backend dependencies..."
        cd "$BACKEND_DIR"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            "$PIP_CMD" install -r requirements.txt --quiet
        else
            info "[DRY RUN] Would install: $PIP_CMD install -r requirements.txt"
        fi
        success "Backend dependencies installed"
    fi
    
    # Install root dependencies if they exist
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        info "Installing root dependencies..."
        cd "$SCRIPT_DIR"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            "$PIP_CMD" install -r requirements.txt --quiet
        else
            info "[DRY RUN] Would install: $PIP_CMD install -r requirements.txt"
        fi
        success "Root dependencies installed"
    fi
    
    # Install development dependencies if in setup mode
    if [[ "$SETUP_MODE" == "true" ]] && [[ -f "$SCRIPT_DIR/requirements-dev.txt" ]]; then
        info "Installing development dependencies..."
        cd "$SCRIPT_DIR"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            "$PIP_CMD" install -r requirements-dev.txt --quiet
        else
            info "[DRY RUN] Would install: $PIP_CMD install -r requirements-dev.txt"
        fi
        success "Development dependencies installed"
    fi
}

setup_environment_variables() {
    info "Setting up environment variables..."
    
    # Create comprehensive environment configuration
    local env_file="$SCRIPT_DIR/.env"
    local env_prod_file="$SCRIPT_DIR/.env.production"
    local env_dev_file="$SCRIPT_DIR/.env.development"
    
    # Development environment file
    if [[ ! -f "$env_dev_file" ]] || [[ "$SETUP_MODE" == "true" ]]; then
        info "Creating .env.development configuration..."
        cat > "$env_dev_file" << EOF
# LawyerFactory Development Environment Configuration
# Generated by launch-dev.sh on $(date)

# Environment
NODE_ENV=development
ENVIRONMENT=development
DEBUG=true

# Server Configuration
FRONTEND_PORT=$FRONTEND_PORT
BACKEND_PORT=$BACKEND_PORT
VITE_API_URL=http://localhost:$BACKEND_PORT
VITE_WS_URL=ws://localhost:$BACKEND_PORT

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000,http://127.0.0.1:5173

# AI Services (Development - use your API keys - REAL APIS, NO MOCKS)
OPENAI_API_KEY=\${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY:-}
GROQ_API_KEY=\${GROQ_API_KEY:-}

# Legal Research APIs (REAL APIS, NO MOCKS)
COURTLISTENER_API_KEY=\${COURTLISTENER_API_KEY:-}

# Storage Configuration
WORKFLOW_STORAGE_PATH=./workflow_storage
UPLOAD_DIR=./uploads
OUTPUT_DIR=./output
DATA_DIR=./data

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=\${QDRANT_API_KEY:-}

# Security (Development)
JWT_SECRET_KEY=dev_jwt_secret_key_32_chars_long_12345
ENCRYPTION_KEY=dev_encryption_key_32_chars_long_67890
SESSION_SECRET=dev_session_secret

# Logging
LOG_LEVEL=DEBUG
PYTHONPATH=./src:\${PYTHONPATH:-}

# Development Features - Real Data Mode
HOT_RELOAD=true
WATCH_FILES=true
AUTO_RESTART=true
USE_REAL_DATA=true
USE_MOCK_DATA=false
ENABLE_UNIFIED_STORAGE=true

# Database (if using)
DATABASE_URL=sqlite:///./data/lawyerfactory_dev.db

# Redis (if using)
REDIS_URL=redis://localhost:6379/0
EOF
    fi
    
    # Production environment file
    if [[ ! -f "$env_prod_file" ]] || [[ "$SETUP_MODE" == "true" ]]; then
        info "Creating .env.production configuration..."
        cat > "$env_prod_file" << EOF
# LawyerFactory Production Environment Configuration
# Generated by launch-dev.sh on $(date)

# Environment
NODE_ENV=production
ENVIRONMENT=production
DEBUG=false

# Server Configuration
FRONTEND_PORT=\${FRONTEND_PORT:-3000}
BACKEND_PORT=\${BACKEND_PORT:-5000}
VITE_API_URL=\${VITE_API_URL:-http://localhost:5000}
VITE_WS_URL=\${VITE_WS_URL:-ws://localhost:5000}

# CORS Configuration (restrict in production)
CORS_ORIGINS=\${CORS_ORIGINS:-http://localhost:3000}

# AI Services (Production - REQUIRED)
OPENAI_API_KEY=\${OPENAI_API_KEY}
ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
GROQ_API_KEY=\${GROQ_API_KEY}

# Legal Research APIs
COURTLISTENER_API_KEY=\${COURTLISTENER_API_KEY}

# Storage Configuration
WORKFLOW_STORAGE_PATH=\${WORKFLOW_STORAGE_PATH:-/app/data/storage}
UPLOAD_DIR=\${UPLOAD_DIR:-/app/uploads}
OUTPUT_DIR=\${OUTPUT_DIR:-/app/output}
DATA_DIR=\${DATA_DIR:-/app/data}

# Vector Database
QDRANT_URL=\${QDRANT_URL:-http://localhost:6333}
QDRANT_API_KEY=\${QDRANT_API_KEY}

# Security (Production - CHANGE THESE)
JWT_SECRET_KEY=\${JWT_SECRET_KEY}
ENCRYPTION_KEY=\${ENCRYPTION_KEY}
SESSION_SECRET=\${SESSION_SECRET}

# Logging
LOG_LEVEL=\${LOG_LEVEL:-INFO}
PYTHONPATH=/app/src:\${PYTHONPATH:-}

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
EOF
    fi
    
    # Load appropriate environment file
    local current_env_file
    if [[ "$PRODUCTION_MODE" == "true" ]]; then
        current_env_file="$env_prod_file"
        info "Loading production environment variables"
    else
        current_env_file="$env_dev_file"
        info "Loading development environment variables"
    fi
    
    if [[ -f "$current_env_file" ]]; then
        set -a  # Automatically export all variables
        source "$current_env_file"
        set +a
        debug "Loaded environment from $current_env_file"
    fi
    
    # Set additional runtime variables
    export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR/src"
    export NODE_ENV="$NODE_ENV"
    export ENVIRONMENT="$ENVIRONMENT"
    
    # Log full system launch info
    echo "$(date '+%Y-%m-%d %H:%M:%S') - === LawyerFactory Full System Launch ===" >> "$LOG_DIR/full-system-launch.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Frontend Port: $FRONTEND_PORT" >> "$LOG_DIR/full-system-launch.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Backend Port: $BACKEND_PORT" >> "$LOG_DIR/full-system-launch.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Environment: $ENVIRONMENT" >> "$LOG_DIR/full-system-launch.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Node ENV: $NODE_ENV" >> "$LOG_DIR/full-system-launch.log"
    
    success "Environment variables configured"
}

validate_system_requirements() {
    info "Validating system requirements..."
    
    local requirements_met=true
    
    # Check required commands
    local required_commands=("node" "npm" "curl" "grep" "awk")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            error "Required command '$cmd' not found"
            requirements_met=false
        fi
    done
    
    # Check recommended commands
    local recommended_commands=("git" "lsof" "netstat" "jq")
    for cmd in "${recommended_commands[@]}"; do
        if ! command_exists "$cmd"; then
            warn "Recommended command '$cmd' not found"
        fi
    done
    
    # Check file structure
    local required_files=(
        "$VITE_APP_DIR/package.json"
        "$VITE_APP_DIR/src/App.jsx"
        "$BACKEND_DIR/server.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file not found: $file"
            requirements_met=false
        fi
    done
    
    # Check for optional but important files
    local important_files=(
        "$VITE_APP_DIR/vite.config.js"
        "$BACKEND_DIR/Server.py"
    )
    
    for file in "${important_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            warn "Important file not found: $file"
        fi
    done
    
    if [[ "$requirements_met" == "false" ]]; then
        error "System requirements not met. Please check the installation."
        exit 1
    fi
    
    success "System requirements validated"
}

start_backend_server() {
    info "Starting backend server on port $BACKEND_PORT..."
    
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
    local backend_log="$LOG_DIR/backend-$(date '+%Y%m%d-%H%M%S').log"
    
    # Set environment variables for real data usage
    export USE_REAL_DATA="true"
    export USE_MOCK_DATA="false"
    export ENABLE_UNIFIED_STORAGE="true"
    export DRY_RUN="false"
    
    # Start backend server in background with real data configuration
    info "Starting backend with real data: $PYTHON_CMD $server_file"
    $PYTHON_CMD "$server_file" --port="$BACKEND_PORT" > "$backend_log" 2>&1 &
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
                    success "Backend server started successfully (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
                    debug "Backend log: $backend_log"
                    return 0
                fi
            else
                success "Backend server started (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
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
    info "Starting React frontend server on port $FRONTEND_PORT..."
    
    cd "$VITE_APP_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would start frontend: VITE_PORT=$FRONTEND_PORT npm run dev -- --port $FRONTEND_PORT --host"
        return 0
    fi
    
    # Create frontend log file
    local frontend_log="$LOG_DIR/frontend-$(date '+%Y%m%d-%H%M%S').log"
    
    # Set Vite environment variables
    export VITE_API_URL="http://localhost:$BACKEND_PORT"
    export VITE_WS_URL="ws://localhost:$BACKEND_PORT"
    export VITE_ENVIRONMENT="$ENVIRONMENT"
    
    # Start Vite development server using npm with proper port configuration
    info "Starting Vite development server..."
    # Use environment variable to set port, which is more reliable than CLI args
    VITE_PORT="$FRONTEND_PORT" npm run dev -- --port "$FRONTEND_PORT" --host 0.0.0.0 > "$frontend_log" 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    local max_wait=60  # Vite can take longer to start
    local wait_count=0
    
    info "Waiting for frontend to start (PID: $FRONTEND_PID)..."
    while [[ $wait_count -lt $max_wait ]]; do
        if ! check_port_available "$FRONTEND_PORT"; then
            # Test if frontend is responding
            if command_exists curl; then
                local frontend_url="http://localhost:$FRONTEND_PORT"
                if curl -s --max-time 2 "$frontend_url" >/dev/null 2>&1; then
                    success "Frontend server started successfully (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
                    debug "Frontend log: $frontend_log"
                    return 0
                fi
            else
                success "Frontend server started (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
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

perform_health_checks() {
    info "Performing comprehensive health checks..."
    
    local backend_url="http://localhost:$BACKEND_PORT"
    local frontend_url="http://localhost:$FRONTEND_PORT"
    
    # Backend health check
    if command_exists curl; then
        info "Testing backend API endpoints..."
        
        # Health endpoint
        local health_url="$backend_url/api/health"
        if curl -s --max-time 5 "$health_url" | grep -q "healthy\|status"; then
            success "✓ Backend health endpoint responding"
        else
            warn "✗ Backend health endpoint not responding properly"
        fi
        
        # Test CORS headers for frontend integration
        local cors_test=$(curl -s -I -H "Origin: http://localhost:$FRONTEND_PORT" "$health_url" 2>/dev/null)
        if echo "$cors_test" | grep -qi "access-control-allow-origin"; then
            success "✓ CORS headers configured for frontend integration"
        else
            warn "✗ CORS headers may not be configured properly"
        fi
        
        # Frontend health check
        info "Testing frontend server..."
        if curl -s --head --max-time 5 "$frontend_url" >/dev/null 2>&1; then
            success "✓ Frontend server responding"
        else
            warn "✗ Frontend server not responding"
        fi
        
    else
        warn "curl not available, performing basic port checks only"
        
        # Basic port checks
        if ! check_port_available "$BACKEND_PORT"; then
            success "✓ Backend port $BACKEND_PORT is active"
        else
            warn "✗ Backend port $BACKEND_PORT appears inactive"
        fi
        
        if ! check_port_available "$FRONTEND_PORT"; then
            success "✓ Frontend port $FRONTEND_PORT is active"
        else
            warn "✗ Frontend port $FRONTEND_PORT appears inactive"
        fi
    fi
    
    # Socket.IO health check
    if command_exists curl; then
        local socketio_url="$backend_url/socket.io/?EIO=4&transport=polling"
        if curl -s --max-time 3 "$socketio_url" >/dev/null 2>&1; then
            success "✓ Socket.IO endpoint responding"
        else
            warn "✗ Socket.IO endpoint may not be responding"
        fi
    fi
}

open_browser() {
    if [[ "$OPEN_BROWSER" == "false" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    local url="http://localhost:$FRONTEND_PORT"
    
    info "Opening browser to $url..."
    
    # Wait a moment for servers to fully initialize
    sleep 2
    
    if command_exists open; then
        # macOS
        open "$url" 2>/dev/null || warn "Failed to open browser automatically"
    elif command_exists xdg-open; then
        # Linux
        xdg-open "$url" 2>/dev/null || warn "Failed to open browser automatically"
    elif command_exists start; then
        # Windows (WSL/Git Bash)
        start "$url" 2>/dev/null || warn "Failed to open browser automatically"
    else
        info "Manual browser open required: $url"
    fi
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
    
    info "Shutting down LawyerFactory development environment..."
    
    # Kill frontend process
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        info "Stopping frontend server (PID: $FRONTEND_PID)"
        kill "$FRONTEND_PID" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local wait_count=0
        while kill -0 "$FRONTEND_PID" 2>/dev/null && [[ $wait_count -lt 10 ]]; do
            sleep 0.5
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
        while kill -0 "$BACKEND_PID" 2>/dev/null && [[ $wait_count -lt 10 ]]; do
            sleep 0.5
            wait_count=$((wait_count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            warn "Force killing backend process"
            kill -9 "$BACKEND_PID" 2>/dev/null || true
        fi
    fi
    
    # Kill any lingering processes on our ports
    if command_exists lsof; then
        for port in "$FRONTEND_PORT" "$BACKEND_PORT"; do
            local port_pids=$(lsof -ti :"$port" 2>/dev/null || true)
            if [[ -n "$port_pids" ]]; then
                warn "Killing remaining processes on port $port: $port_pids"
                echo "$port_pids" | xargs kill -9 2>/dev/null || true
            fi
        done
    fi
    
    success "LawyerFactory development environment shutdown complete"
}

show_usage() {
    cat << EOF
LawyerFactory Development Environment Launcher v$SCRIPT_VERSION

USAGE:
    ./launch-dev.sh [options]

OPTIONS:
    --frontend-port PORT     React Vite frontend port (default: 3000)
    --backend-port PORT      Flask backend port (default: 5000)
    --skip-deps             Skip dependency installation
    --setup                 Full setup including dev dependencies
    --verbose               Enable verbose logging
    --dry-run               Show what would be done without executing
    --no-browser            Don't open browser automatically
    --log-level LEVEL       Set log level (DEBUG, INFO, WARN, ERROR)
    --help                  Show this help message

ENVIRONMENT MODES:
    Development (default):   Hot reload, debug mode, development APIs
    Production:             Optimized builds, production configuration

EXAMPLES:
    ./launch-dev.sh                          # Start development environment
    ./launch-dev.sh --setup                  # Full setup and start
    ./launch-dev.sh --production             # Production mode
    ./launch-dev.sh --frontend-port 3000     # Custom frontend port
    ./launch-dev.sh --verbose --dry-run      # Test run with verbose output
    ./launch-dev.sh --no-browser             # Start without opening browser

ENVIRONMENT VARIABLES:
    FRONTEND_PORT       React app port (default: 5173)
    BACKEND_PORT        Flask API port (default: 5000)
    NODE_ENV           Node environment (development/production)
    ENVIRONMENT        App environment (development/production)
    SKIP_DEPS          Skip dependency installation
    VERBOSE            Enable verbose logging
    DRY_RUN            Test mode
    PRODUCTION_MODE    Run in production mode
    OPEN_BROWSER       Auto-open browser

SYSTEM URLS:
    Frontend (Briefcaser):  http://localhost:3000
    Backend (Flask API):    http://localhost:5000
    API Health:             http://localhost:5000/api/health
    Socket.IO:              ws://localhost:5000

FEATURES:
    ✓ React 19.1.1 + Vite development server with proper PATH handling
    ✓ Flask + Socket.IO backend with unified storage integration
    ✓ Hot reload for both frontend and backend
    ✓ Comprehensive environment variable management
    ✓ Health checks and automatic port detection
    ✓ Graceful shutdown handling
    ✓ Development and production modes
    ✓ Complete logging with rotation

For more information, see: README.md and SYSTEM_DOCUMENTATION.md
EOF
}

show_system_info() {
    header "LawyerFactory Development Environment v$SCRIPT_VERSION"
    info "  Mode: ${ENVIRONMENT:-development} (Node: ${NODE_ENV:-development})"
    info "  Frontend (React + Vite): http://localhost:$FRONTEND_PORT"
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
            --production)
                PRODUCTION_MODE="true"
                NODE_ENV="production"
                ENVIRONMENT="production"
                WATCH_MODE="false"
                shift
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
                warn "Dry-run mode is disabled - script will always run in real mode"
                # DRY_RUN remains "false" - force real execution
                shift
                ;;
            --no-browser)
                OPEN_BROWSER="false"
                shift
                ;;
            --log-level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            --help|-h)
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
    
    # Initialize logging and directories
    setup_directories
    
    # Show header
    if [[ "$DRY_RUN" == "true" ]]; then
        header "🧪 LawyerFactory Development Environment - DRY RUN MODE"
    else
        header "🚀 Starting LawyerFactory Development Environment"
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
    setup_environment_variables
    install_dependencies
    validate_system_requirements
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Start services
        start_backend_server
        start_frontend_server
        perform_health_checks
        
        # Display success information
        header "🎉 LawyerFactory Development Environment Ready!"
        echo ""
        info "📊 Application URLs:"
        info "  • Briefcaser UI: ${BOLD}http://localhost:$FRONTEND_PORT${NC}"
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
        
        # Open browser
        open_browser
        
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

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi