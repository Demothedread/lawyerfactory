#!/bin/bash
# LawyerFactory Unified Launch System
# Single canonical script supporting dev, production, and full-system modes
# Replaces: launch.sh, launch-dev.sh, launch-prod.sh, launch-full-system.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ============================================================================
# COLOR & LOGGING CONFIGURATION
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

log() {
    echo -e "${GREEN}[LawyerFactory]${NC} $1" | tee -a "$LOG_DIR/launch.log"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_DIR/launch.log"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_DIR/launch.log"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_DIR/launch.log"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_DIR/launch.log"
}

# ============================================================================
# CONFIGURATION & DEFAULTS
# ============================================================================

LAUNCH_MODE="dev"  # dev, prod, or full
FRONTEND_PORT=3000
BACKEND_PORT=5000
QDRANT_PORT=6333
SKIP_FRONTEND=false
SKIP_BACKEND=false
SKIP_QDRANT=false
AUTO_CLEANUP=true
HEALTH_CHECK=true
VERBOSE=false

# ============================================================================
# COMMAND LINE ARGUMENT PARSING
# ============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --production|--prod)
                LAUNCH_MODE="prod"
                shift
                ;;
            --full-system|--full)
                LAUNCH_MODE="full"
                shift
                ;;
            --dev)
                LAUNCH_MODE="dev"
                shift
                ;;
            --frontend-port)
                FRONTEND_PORT="$2"
                shift 2
                ;;
            --backend-port)
                BACKEND_PORT="$2"
                shift 2
                ;;
            --qdrant-port)
                QDRANT_PORT="$2"
                shift 2
                ;;
            --skip-frontend)
                SKIP_FRONTEND=true
                shift
                ;;
            --skip-backend)
                SKIP_BACKEND=true
                shift
                ;;
            --skip-qdrant)
                SKIP_QDRANT=true
                shift
                ;;
            --no-cleanup)
                AUTO_CLEANUP=false
                shift
                ;;
            --no-health-check)
                HEALTH_CHECK=false
                shift
                ;;
            --verbose|--debug)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                error "Unknown argument: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
${GREEN}LawyerFactory Unified Launch System${NC}

${CYAN}USAGE:${NC}
    ./launch.sh [MODE] [OPTIONS]

${CYAN}MODES:${NC}
    --dev                   Development mode (default)
    --production, --prod    Production mode (optimized)
    --full-system, --full   Full system launch (dev + all services)

${CYAN}OPTIONS:${NC}
    --frontend-port PORT    Frontend port (default: 3000)
    --backend-port PORT     Backend port (default: 5000)
    --qdrant-port PORT      Qdrant port (default: 6333)
    --skip-frontend         Skip frontend startup
    --skip-backend          Skip backend startup
    --skip-qdrant           Skip Qdrant startup
    --no-cleanup            Don't cleanup on exit
    --no-health-check       Skip health checks
    --verbose, --debug      Verbose output
    --help, -h              Show this help message

${CYAN}EXAMPLES:${NC}
    ./launch.sh                              # Launch development mode
    ./launch.sh --production                 # Launch production mode
    ./launch.sh --full-system                # Full system with all services
    ./launch.sh --dev --skip-frontend        # Backend only
    ./launch.sh --prod --frontend-port 8080 # Custom port

EOF
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
    else
        ! netstat -tuln 2>/dev/null | grep -q ":$port " || return 0
    fi
}

find_available_port() {
    local start_port=$1
    local port=$start_port
    while ! check_port $port; do
        port=$((port + 1))
        if [ $port -gt $((start_port + 100)) ]; then
            error "Could not find available port near $start_port"
            return 1
        fi
    done
    echo $port
}

verify_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# ============================================================================
# ENVIRONMENT VALIDATION
# ============================================================================

validate_environment() {
    log "Validating environment..."

    # Check Python
    if ! verify_command python3; then
        error "Python 3 is not installed"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    success "Python 3 found: $PYTHON_VERSION"

    # Check Node.js for frontend
    if [ "$SKIP_FRONTEND" = false ]; then
        if ! verify_command node; then
            warn "Node.js not found - frontend will not work"
        else
            NODE_VERSION=$(node --version)
            success "Node.js found: $NODE_VERSION"
        fi
    fi

    # Check .env file
    if [ ! -f ".env" ]; then
        warn ".env file not found - attempting to create from .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            success "Created .env from .env.example"
        else
            warn "No .env or .env.example file found"
        fi
    fi

    # Source .env for API key validation
    if [ -f ".env" ]; then
        source .env
        if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GROQ_API_KEY" ]; then
            warn "No AI service API keys configured (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GROQ_API_KEY)"
            warn "Some features may not work without API keys"
        fi
    fi

    log "Environment validation complete"
}

# ============================================================================
# PYTHON ENVIRONMENT SETUP
# ============================================================================

setup_python() {
    log "Setting up Python environment..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log "Creating virtual environment..."
        python3 -m venv venv
        success "Virtual environment created"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    log "Upgrading pip..."
    pip install -q --upgrade pip

    # Install dependencies
    if [ -f "requirements.txt" ]; then
        log "Installing dependencies from requirements.txt..."
        pip install -q -r requirements.txt
        success "Dependencies installed"
    fi

    # Export Python path
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

    success "Python environment ready"
}

# ============================================================================
# SERVICE STARTUP FUNCTIONS
# ============================================================================

start_qdrant() {
    if [ "$SKIP_QDRANT" = true ]; then
        log "Skipping Qdrant startup"
        return 0
    fi

    log "Starting Qdrant vector store..."

    # Check if Qdrant is already running
    if check_port $QDRANT_PORT; then
        if verify_command docker; then
            log "Starting Qdrant with Docker on port $QDRANT_PORT..."
            docker run -d \
                --name lawyerfactory-qdrant \
                -p $QDRANT_PORT:6333 \
                -v "$PROJECT_ROOT/qdrant_storage:/qdrant/storage" \
                qdrant/qdrant:latest >/dev/null 2>&1
            success "Qdrant started"
            return 0
        else
            warn "Docker not found - Qdrant vector store will not be available"
            return 0
        fi
    else
        success "Qdrant already running on port $QDRANT_PORT"
        return 0
    fi
}

start_backend() {
    if [ "$SKIP_BACKEND" = true ]; then
        log "Skipping backend startup"
        return 0
    fi

    log "Starting backend server..."

    # Find available port
    BACKEND_PORT=$(find_available_port $BACKEND_PORT)
    log "Backend will run on port $BACKEND_PORT"

    # Export environment
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    export FLASK_ENV=${LAUNCH_MODE:-development}
    export BACKEND_PORT=$BACKEND_PORT

    # Create backend logs
    mkdir -p "$LOG_DIR"

    # Start backend
    cd "$PROJECT_ROOT/apps/api"
    python server.py --port $BACKEND_PORT > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_ROOT/.backend.pid"
    cd "$PROJECT_ROOT"

    success "Backend started (PID: $BACKEND_PID)"

    # Wait for backend to be ready
    log "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:$BACKEND_PORT/api/health >/dev/null 2>&1; then
            success "Backend is healthy"
            return 0
        fi
        if [ $i -eq 15 ] || [ $i -eq 30 ]; then
            info "Still waiting for backend... ($i/30)"
        fi
        sleep 1
    done

    error "Backend failed to start within 30 seconds"
    if [ -f "$LOG_DIR/backend.log" ]; then
        warn "Last 10 lines of backend log:"
        tail -n 10 "$LOG_DIR/backend.log" | sed 's/^/  /'
    fi
    return 1
}

start_frontend() {
    if [ "$SKIP_FRONTEND" = true ]; then
        log "Skipping frontend startup"
        return 0
    fi

    if [ ! -f "apps/ui/react-app/package.json" ]; then
        warn "React app not found - skipping frontend startup"
        return 0
    fi

    log "Starting React frontend server..."

    # Find available port
    FRONTEND_PORT=$(find_available_port $FRONTEND_PORT)
    log "Frontend will run on port $FRONTEND_PORT"

    cd apps/ui/react-app

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log "Installing frontend dependencies..."
        npm install
    fi

    # Start frontend
    VITE_BACKEND_URL="http://localhost:$BACKEND_PORT" npm run dev -- --port $FRONTEND_PORT --host > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend.pid"
    cd "$PROJECT_ROOT"

    success "Frontend started (PID: $FRONTEND_PID)"
    return 0
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

health_check() {
    if [ "$HEALTH_CHECK" = false ]; then
        return 0
    fi

    log "Running health checks..."

    # Backend health
    if [ "$SKIP_BACKEND" = false ]; then
        if curl -s http://localhost:$BACKEND_PORT/api/health >/dev/null 2>&1; then
            success "✓ Backend healthy"
        else
            warn "✗ Backend unhealthy"
        fi
    fi

    # Qdrant health
    if [ "$SKIP_QDRANT" = false ]; then
        if curl -s http://localhost:$QDRANT_PORT/health >/dev/null 2>&1; then
            success "✓ Qdrant healthy"
        else
            warn "✗ Qdrant unhealthy"
        fi
    fi

    # Storage directories
    if [ -d "$PROJECT_ROOT/workflow_storage" ] && [ -d "$PROJECT_ROOT/uploads" ]; then
        success "✓ Storage directories exist"
    else
        warn "✗ Storage directories missing"
    fi
}

# ============================================================================
# CLEANUP
# ============================================================================

cleanup() {
    if [ "$AUTO_CLEANUP" = false ]; then
        return 0
    fi

    log "Cleaning up processes..."

    # Kill backend
    if [ -f "$PROJECT_ROOT/.backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/.backend.pid")
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID 2>/dev/null || true
        fi
        rm "$PROJECT_ROOT/.backend.pid"
    fi

    # Kill frontend
    if [ -f "$PROJECT_ROOT/.frontend.pid" ]; then
        FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend.pid")
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID 2>/dev/null || true
        fi
        rm "$PROJECT_ROOT/.frontend.pid"
    fi

    # Stop Qdrant container if running
    if verify_command docker; then
        docker stop lawyerfactory-qdrant 2>/dev/null || true
        docker rm lawyerfactory-qdrant 2>/dev/null || true
    fi

    success "Cleanup complete"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    # Parse arguments
    parse_arguments "$@"

    # Display header
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "LawyerFactory Unified Launch System"
    log "Mode: $(echo $LAUNCH_MODE | tr '[:lower:]' '[:upper:]')"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Setup trap for cleanup
    trap cleanup EXIT INT TERM

    # Create required directories
    mkdir -p logs
    
    # Run setup
    validate_environment
    setup_python

    # Start services based on mode
    case $LAUNCH_MODE in
        dev)
            start_backend || exit 1
            start_frontend
            ;;
        prod)
            export FLASK_ENV=production
            start_backend || exit 1
            ;;
        full)
            start_qdrant
            start_backend || exit 1
            start_frontend
            ;;
    esac

    # Run health checks
    sleep 2
    health_check

    # Display access information
    log ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "LawyerFactory is running!"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ "$SKIP_BACKEND" = false ]; then
        success "Backend:  http://localhost:$BACKEND_PORT"
        success "API Docs: http://localhost:$BACKEND_PORT/api/health"
    fi

    if [ "$SKIP_FRONTEND" = false ]; then
        success "Frontend: http://localhost:$FRONTEND_PORT"
    fi

    if [ "$LAUNCH_MODE" = "full" ] && [ "$SKIP_QDRANT" = false ]; then
        success "Qdrant:   http://localhost:$QDRANT_PORT"
    fi

    log ""
    log "Press ${CYAN}Ctrl+C${NC} to stop all services"
    log "Logs saved to: $LOG_DIR"
    log ""

    # Keep running
    wait
}

# ============================================================================
# ENTRY POINT
# ============================================================================

if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
