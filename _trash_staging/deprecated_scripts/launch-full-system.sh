#!/bin/bash
# filepath: launch-system.sh
# Advanced launch script with configurable options and component selection

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Default configuration
FRONTEND_PORT=3000
BACKEND_PORT=5000
QDRANT_PORT=6333
START_FRONTEND=true
START_BACKEND=true
START_QDRANT=true
RUN_TESTS=false
FORMAT_CODE=false
VERBOSE=false

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

LawyerFactory System Launch Script

OPTIONS:
    --frontend-port PORT    Set frontend port (default: 3000)
    --backend-port PORT     Set backend port (default: 5000)
    --qdrant-port PORT      Set Qdrant port (default: 6333)
    --no-frontend          Skip frontend startup
    --no-backend           Skip backend startup
    --no-qdrant            Skip Qdrant startup
    --backend-only         Start only backend services
    --frontend-only        Start only frontend services
    --test                 Run integration tests after startup
    --format               Format code before startup
    --verbose              Enable verbose logging
    -h, --help             Show this help message

EXAMPLES:
    $0                                          # Start all services with defaults
    $0 --backend-only --backend-port 8000       # Start only backend on port 8000
    $0 --test --format                          # Format code, start services, run tests
    $0 --no-qdrant --frontend-port 3001         # Skip Qdrant, use custom frontend port

EOF
    exit 0
}

# Parse command line arguments
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
        --qdrant-port)
            QDRANT_PORT="$2"
            shift 2
            ;;
        --no-frontend)
            START_FRONTEND=false
            shift
            ;;
        --no-backend)
            START_BACKEND=false
            shift
            ;;
        --no-qdrant)
            START_QDRANT=false
            shift
            ;;
        --backend-only)
            START_FRONTEND=false
            START_BACKEND=true
            START_QDRANT=true
            shift
            ;;
        --frontend-only)
            START_FRONTEND=true
            START_BACKEND=false
            START_QDRANT=false
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --format)
            FORMAT_CODE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Logging functions
log() {
    echo -e "${GREEN}[LawyerFactory]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Format code using project standards
format_code() {
    log "Formatting Python code..."
    
    source venv/bin/activate
    
    debug "Running isort..."
    python -m isort . 2>&1 | grep -v "Skipped" || true
    
    debug "Running black..."
    python -m black . 2>&1 | grep -v "reformatted" | grep -v "left unchanged" || true
    
    debug "Running autopep8..."
    python -m autopep8 --in-place --aggressive --aggressive . 2>&1 || true
    
    log "Code formatting complete"
}

# Run integration tests
run_tests() {
    log "Running integration tests..."
    
    source venv/bin/activate
    
    # Run unit tests
    debug "Running unit tests..."
    python -m pytest tests/unit/ -v --tb=short || warn "Some unit tests failed"
    
    # Run integration tests
    debug "Running integration tests..."
    python -m pytest tests/integration/ -v --tb=short || warn "Some integration tests failed"
    
    # Run full integration flow
    debug "Running full integration flow..."
    python test_integration_flow.py || warn "Integration flow test failed"
    
    log "Tests complete"
}

# Check and create required directories
setup_directories() {
    debug "Setting up required directories..."
    
    mkdir -p logs
    mkdir -p workflow_storage
    mkdir -p uploads
    mkdir -p qdrant_storage
    
    # Set up storage paths in environment
    export WORKFLOW_STORAGE_PATH="$PROJECT_ROOT/workflow_storage"
    export UPLOAD_DIR="$PROJECT_ROOT/uploads"
    export QDRANT_URL="http://localhost:$QDRANT_PORT"
    
    debug "Directories ready"
}

# Start services based on configuration
start_services() {
    log "Starting services..."
    log "Configuration:"
    log "  Frontend: $START_FRONTEND (port: $FRONTEND_PORT)"
    log "  Backend:  $START_BACKEND (port: $BACKEND_PORT)"
    log "  Qdrant:   $START_QDRANT (port: $QDRANT_PORT)"
    
    # Start Qdrant if enabled
    if [ "$START_QDRANT" = true ]; then
        if command -v docker &> /dev/null; then
            debug "Starting Qdrant with Docker..."
            docker run -d \
                --name lawyerfactory-qdrant-$QDRANT_PORT \
                -p $QDRANT_PORT:6333 \
                -v "$PROJECT_ROOT/qdrant_storage:/qdrant/storage" \
                qdrant/qdrant:latest >/dev/null 2>&1 || warn "Qdrant may already be running"
        else
            warn "Docker not available - Qdrant will not start"
        fi
    fi
    
    # Start backend if enabled
    if [ "$START_BACKEND" = true ]; then
        source venv/bin/activate
        export BACKEND_PORT=$BACKEND_PORT
        debug "Starting backend on port $BACKEND_PORT..."
        python -m apps.api.server --port $BACKEND_PORT > logs/backend.log 2>&1 &
        echo $! > .backend.pid
        sleep 2
    fi
    
    # Start frontend if enabled
    if [ "$START_FRONTEND" = true ] && [ -d "apps/ui" ]; then
        debug "Starting frontend on port $FRONTEND_PORT..."
        cd apps/ui
        BACKEND_URL="http://localhost:$BACKEND_PORT" npm start -- --port $FRONTEND_PORT > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
        echo $! > "$PROJECT_ROOT/.frontend.pid"
        cd "$PROJECT_ROOT"
    fi
}

# Main execution
main() {
    log "LawyerFactory Advanced Launch System"
    log "====================================="
    
    # Format code if requested
    if [ "$FORMAT_CODE" = true ]; then
        format_code
    fi
    
    # Setup environment
    setup_directories
    
    # Start services
    start_services
    
    # Run tests if requested
    if [ "$RUN_TESTS" = true ]; then
        sleep 5  # Wait for services to fully start
        run_tests
    fi
    
    # Display status
    log ""
    log "====================================="
    log "Services started successfully!"
    log "====================================="
    
    if [ "$START_BACKEND" = true ]; then
        log "Backend:  http://localhost:$BACKEND_PORT"
    fi
    
    if [ "$START_FRONTEND" = true ]; then
        log "Frontend: http://localhost:$FRONTEND_PORT"
    fi
    
    if [ "$START_QDRANT" = true ]; then
        log "Qdrant:   http://localhost:$QDRANT_PORT"
    fi
    
    log ""
    log "Check logs/ directory for service logs"
    log "Press Ctrl+C to stop services"
}

main "$@"