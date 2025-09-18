#!/usr/bin/env bash

# LawyerFactory Unified System Launcher
# Comprehensive launch script that consolidates launch.sh, launch-full-system.sh, and launch-website.sh
# Sets up and launches the complete LawyerFactory system with integrated UI
# Usage: ./launch-system.sh [options]

set -euo pipefail

# Script metadata
readonly SCRIPT_VERSION="2.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="$SCRIPT_DIR/logs"
readonly CONFIG_DIR="$SCRIPT_DIR/configs"

# Default configuration
FRONTEND_PORT="${FRONTEND_PORT:-8000}"
BACKEND_PORT="${BACKEND_PORT:-5000}"
SKIP_DEPS="${SKIP_DEPS:-false}"
VERBOSE="${VERBOSE:-false}"
DRY_RUN="${DRY_RUN:-false}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
SETUP_MODE="${SETUP_MODE:-false}"
OPEN_BROWSER="${OPEN_BROWSER:-true}"

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_DIR/launch-system.log"
}

info() { echo -e "${GREEN}[INFO]${NC} $*"; log "INFO" "$*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; log "WARN" "$*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; log "ERROR" "$*"; }
debug() { [[ "$VERBOSE" == "true" ]] && echo -e "${BLUE}[DEBUG]${NC} $*"; log "DEBUG" "$*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; log "SUCCESS" "$*"; }

# Utility functions
command_exists() { command -v "$1" >/dev/null 2>&1; }

check_port_available() {
    local port="$1"
    if command_exists nc; then
        ! nc -z 127.0.0.1 "$port" 2>/dev/null
    elif command_exists lsof; then
        ! lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        warn "No port checking tool available. Assuming port $port is available."
        return 0
    fi
}

find_available_port() {
    local port="$1"
    while ! check_port_available "$port"; do
        port=$((port + 1))
    done
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
        "$SCRIPT_DIR/uploads"
        "$SCRIPT_DIR/output"
        "$SCRIPT_DIR/workflow_storage"
        "$SCRIPT_DIR/data/vectors"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            debug "Created directory: $dir"
        fi
    done
    
    success "Directory structure ready"
}

setup_python_environment() {
    info "Setting up Python environment..."
    
    # Check Python version
    if command_exists python3; then
        PYTHON_CMD=python3
        PIP_CMD=pip3
    elif command_exists python; then
        PYTHON_CMD=python
        PIP_CMD=pip
    else
        error "Python is required but not found. Install Python 3.9+."
        exit 1
    fi
    
    local python_version
    python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
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
    elif [[ -d "$SCRIPT_DIR/venv" ]]; then
        info "Activating virtual environment: venv"
        source "$SCRIPT_DIR/venv/bin/activate"
    else
        warn "No virtual environment found. Consider creating one with: python -m venv venv"
    fi
    
    success "Python environment ready"
}

install_dependencies() {
    if [[ "$SKIP_DEPS" == "true" ]]; then
        info "Skipping dependency installation (--skip-deps specified)"
        return 0
    fi
    
    info "Installing/updating dependencies..."
    
    # Check if pip is available
    if ! command_exists "$PIP_CMD"; then
        error "pip is required but not found"
        exit 1
    fi
    
    # Install backend dependencies
    if [[ -f "$SCRIPT_DIR/apps/api/requirements.txt" ]]; then
        info "Installing backend dependencies..."
        cd "$SCRIPT_DIR/apps/api"
        if [[ "$DRY_RUN" == "false" ]]; then
            "$PIP_CMD" install -r requirements.txt --quiet
        else
            info "[DRY RUN] Would install: $PIP_CMD install -r requirements.txt"
        fi
        success "Backend dependencies installed"
    else
        warn "Backend requirements.txt not found at apps/api/requirements.txt"
    fi
    
    # Check for additional Python dependencies
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
    
    # Create .env.production file in law_venv if it doesn't exist
    local env_file="$SCRIPT_DIR/law_venv/.env.production"
    if [[ ! -f "$env_file" ]]; then
        info "Creating .env.production configuration file..."
        mkdir -p "$(dirname "$env_file")"
        cat > "$env_file" << EOF
# LawyerFactory Environment Configuration
# Generated by launch-system.sh on $(date)

# Server Configuration
FRONTEND_PORT=$FRONTEND_PORT
BACKEND_PORT=$BACKEND_PORT

# AI Services (Configure with your API keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GROQ_API_KEY=your_groq_key_here

# Legal Research
COURTLISTENER_API_KEY=your_courtlistener_key_here

# Storage Configuration
WORKFLOW_STORAGE_PATH=./data/storage
UPLOAD_DIR=./uploads
OUTPUT_DIR=./output

# Vector Database (Configure if using external vector DB)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_qdrant_key

# System Configuration
LOG_LEVEL=$LOG_LEVEL
LAWYERFACTORY_ENV=development
DEBUG=true

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000

# Security Settings
JWT_SECRET_KEY=your_jwt_secret_key_32_chars_long
ENCRYPTION_KEY=your_encryption_key_32_chars_long
EOF
        warn "Created basic .env.production file. Please configure API keys before production use."
    fi
    
    # Load environment variables from .env.production
    if [[ -f "$env_file" ]]; then
        set -a  # Automatically export all variables
        source "$env_file"
        set +a
        debug "Loaded environment variables from $env_file"
    fi
    
    # Set PYTHONPATH
    export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR/src"
    
    success "Environment variables configured"
}

validate_system_requirements() {
    info "Validating system requirements..."
    
    local requirements_met=true
    
    # Check required commands
    local required_commands=("curl" "grep" "awk" "sort")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            warn "Recommended command '$cmd' not found"
        fi
    done
    
    # Check Python modules availability (if not in dry run)
    if [[ "$DRY_RUN" == "false" ]]; then
        local required_modules=("flask" "socketio" "requests")
        for module in "${required_modules[@]}"; do
            if ! $PYTHON_CMD -c "import $module" 2>/dev/null; then
                warn "Python module '$module' not available. Will be installed with dependencies."
            fi
        done
    fi
    
    # Check file structure
    local required_files=(
        "apps/api/server.py"
        "apps/ui/templates/consolidated_factory.html"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
            error "Required file not found: $file"
            requirements_met=false
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
    
    if [[ ! -f "$SCRIPT_DIR/apps/api/server.py" ]]; then
        error "Backend server.py not found at apps/api/server.py"
        return 1
    fi
    
    cd "$SCRIPT_DIR/apps/api"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would start backend: $PYTHON_CMD server.py --host 127.0.0.1 --port $BACKEND_PORT"
        return 0
    fi
    
    # Start backend server in background
    $PYTHON_CMD server.py --host 127.0.0.1 --port "$BACKEND_PORT" > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    local max_wait=30
    local wait_count=0
    
    while [[ $wait_count -lt $max_wait ]]; do
        if ! check_port_available "$BACKEND_PORT"; then
            success "Backend server started (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
            return 0
        fi
        sleep 1
        wait_count=$((wait_count + 1))
    done
    
    error "Backend server failed to start within $max_wait seconds"
    return 1
}

start_frontend_server() {
    info "Starting frontend server on port $FRONTEND_PORT..."
    
    cd "$SCRIPT_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would start frontend: $PYTHON_CMD -m http.server $FRONTEND_PORT"
        return 0
    fi
    
    # Start simple HTTP server for static files
    $PYTHON_CMD -m http.server "$FRONTEND_PORT" --bind 127.0.0.1 > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    
    sleep 2
    
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        success "Frontend server started (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
    else
        error "Frontend server failed to start"
        return 1
    fi
}

perform_health_checks() {
    info "Performing health checks..."
    
    local backend_url="http://127.0.0.1:$BACKEND_PORT/api/health"
    local frontend_url="http://127.0.0.1:$FRONTEND_PORT/apps/ui/templates/consolidated_factory.html"
    
    # Backend health check
    if command_exists curl; then
        local max_tries=10
        local tries=0
        
        info "Checking backend health at $backend_url..."
        while [[ $tries -lt $max_tries ]]; do
            if curl -s --head "$backend_url" >/dev/null 2>&1; then
                success "Backend is healthy"
                break
            fi
            tries=$((tries + 1))
            sleep 1
        done
        
        if [[ $tries -eq $max_tries ]]; then
            warn "Backend health check failed, but server may still be functional"
        fi
        
        # Frontend health check
        info "Checking frontend health at $frontend_url..."
        tries=0
        while [[ $tries -lt $max_tries ]]; do
            if curl -s --head "$frontend_url" >/dev/null 2>&1; then
                success "Frontend is healthy"
                break
            fi
            tries=$((tries + 1))
            sleep 1
        done
        
        if [[ $tries -eq $max_tries ]]; then
            warn "Frontend health check failed, but server may still be functional"
        fi
    else
        warn "curl not available, skipping detailed health checks"
        # Basic port checks
        if ! check_port_available "$BACKEND_PORT"; then
            success "Backend port $BACKEND_PORT is active"
        else
            warn "Backend port $BACKEND_PORT appears inactive"
        fi
        
        if ! check_port_available "$FRONTEND_PORT"; then
            success "Frontend port $FRONTEND_PORT is active"
        else
            warn "Frontend port $FRONTEND_PORT appears inactive"
        fi
    fi
}

open_browser() {
    if [[ "$OPEN_BROWSER" == "false" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    local url="http://127.0.0.1:$FRONTEND_PORT/apps/ui/templates/consolidated_factory.html"
    
    info "Opening browser to $url..."
    
    if command_exists open; then
        # macOS
        open "$url"
    elif command_exists xdg-open; then
        # Linux
        xdg-open "$url"
    elif command_exists start; then
        # Windows
        start "$url"
    else
        info "Please open this URL in your browser: $url"
    fi
}

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
    
    success "LawyerFactory system shutdown complete"
    exit 0
}

show_usage() {
    cat << EOF
LawyerFactory Unified System Launcher v$SCRIPT_VERSION

USAGE:
    ./launch-system.sh [options]

OPTIONS:
    --frontend-port PORT     Frontend server port (default: 8000)
    --backend-port PORT      Backend server port (default: 5000)
    --skip-deps             Skip dependency installation
    --verbose               Enable verbose logging
    --dry-run               Show what would be done without executing
    --setup                 Run full setup including dev dependencies
    --no-browser            Don't open browser automatically
    --log-level LEVEL       Set log level (DEBUG, INFO, WARN, ERROR)
    --help                  Show this help message

EXAMPLES:
    ./launch-system.sh                          # Start with defaults
    ./launch-system.sh --setup                  # Full setup and start
    ./launch-system.sh --frontend-port 9000     # Custom frontend port
    ./launch-system.sh --verbose --dry-run      # Test run with verbose output
    ./launch-system.sh --no-browser             # Start without opening browser

ENVIRONMENT VARIABLES:
    FRONTEND_PORT       Frontend server port
    BACKEND_PORT        Backend server port
    SKIP_DEPS          Skip dependency installation
    VERBOSE            Enable verbose logging
    DRY_RUN            Test mode
    LOG_LEVEL          Logging level

The system will launch the comprehensive LawyerFactory UI at:
http://127.0.0.1:\$FRONTEND_PORT/apps/ui/templates/consolidated_factory.html

For more information, see: README.md and SYSTEM_DOCUMENTATION.md
EOF
}

show_system_info() {
    info "LawyerFactory System Information:"
    info "  Version: $SCRIPT_VERSION"
    if [[ -n "${PYTHON_CMD:-}" ]]; then
        info "  Python: $($PYTHON_CMD --version 2>&1)"
    else
        info "  Python: (detecting...)"
    fi
    info "  Frontend Port: $FRONTEND_PORT"
    info "  Backend Port: $BACKEND_PORT"
    info "  Main UI: consolidated_factory.html"
    info "  Log Directory: $LOG_DIR"
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
            --verbose)
                VERBOSE="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --setup)
                SETUP_MODE="true"
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
    # Parse arguments
    parse_arguments "$@"
    
    # Setup signal handlers
    trap cleanup SIGINT SIGTERM EXIT
    
    # Initialize
    info "🚀 Starting LawyerFactory System v$SCRIPT_VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        warn "Running in DRY RUN mode - no actual changes will be made"
    fi
    
    # Find available ports
    FRONTEND_PORT=$(find_available_port "$FRONTEND_PORT")
    BACKEND_PORT=$(find_available_port "$BACKEND_PORT")
    
    if [[ "$FRONTEND_PORT" != "${1:-8000}" ]] || [[ "$BACKEND_PORT" != "${2:-5000}" ]]; then
        info "Adjusted ports - Frontend: $FRONTEND_PORT, Backend: $BACKEND_PORT"
    fi
    
    # Setup system
    setup_directories
    setup_python_environment
    
    # Show system info after Python is detected
    show_system_info
    setup_environment_variables
    install_dependencies
    validate_system_requirements
    
    # Start services
    if [[ "$DRY_RUN" == "false" ]]; then
        start_backend_server
        start_frontend_server
        perform_health_checks
        
        # Display success information
        success "🎉 LawyerFactory system is ready!"
        info ""
        info "📊 System URLs:"
        info "  • Main UI: http://127.0.0.1:$FRONTEND_PORT/apps/ui/templates/consolidated_factory.html"
        info "  • Backend API: http://127.0.0.1:$BACKEND_PORT/api/health"
        info "  • Frontend Server: http://127.0.0.1:$FRONTEND_PORT"
        info ""
        info "📝 Process Information:"
        info "  • Frontend PID: ${FRONTEND_PID:-N/A}"
        info "  • Backend PID: ${BACKEND_PID:-N/A}"
        info "  • Logs: $LOG_DIR/"
        info ""
        info "🛑 To stop the system: Press Ctrl+C or kill the processes above"
        
        # Open browser
        open_browser
        
        # Keep script running
        info "System is running. Press Ctrl+C to stop..."
        wait "${FRONTEND_PID:-1}" "${BACKEND_PID:-1}"
    else
        success "DRY RUN completed successfully"
    fi
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi