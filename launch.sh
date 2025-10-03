#!/bin/bash
# filepath: launch.sh
# Main launch script with automatic health checks and port detection

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default ports
FRONTEND_PORT=3000
BACKEND_PORT=5000
QDRANT_PORT=6333

# Log function
log() {
    echo -e "${GREEN}[LawyerFactory]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

# Find available port starting from given port
find_available_port() {
    local start_port=$1
    local port=$start_port
    while ! check_port $port; do
        port=$((port + 1))
        if [ $port -gt $((start_port + 100)) ]; then
            error "Could not find available port near $start_port"
            exit 1
        fi
    done
    echo $port
}

# Validate environment
validate_environment() {
    log "Validating environment..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Node.js version (if frontend exists)
    if [ -d "apps/ui" ]; then
        if ! command -v node &> /dev/null; then
            warn "Node.js not found - frontend may not work"
        fi
    fi
    
    # Check .env file
    if [ ! -f ".env" ]; then
        warn ".env file not found - copying from .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example .env
        else
            error "No .env or .env.example file found"
            exit 1
        fi
    fi
    
    # Validate required API keys
    source .env
    if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GROQ_API_KEY" ]; then
        error "At least one AI service API key is required (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GROQ_API_KEY)"
        exit 1
    fi
    
    log "Environment validation complete"
}

# Setup Python environment
setup_python() {
    log "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install/upgrade dependencies
    log "Installing Python dependencies..."
    pip install -q --upgrade pip
    
    # Check for multiple requirements files
    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt
    fi
    
    if [ -f "requirements-dev.txt" ]; then
        pip install -q -r requirements-dev.txt
    fi
    
    # Ensure the src directory is in Python path
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    log "Python environment ready"
}

# Start Qdrant vector store
start_qdrant() {
    log "Starting Qdrant vector store..."
    
    # Check if Qdrant is already running
    if check_port $QDRANT_PORT; then
        # Try to start with Docker
        if command -v docker &> /dev/null; then
            log "Starting Qdrant with Docker on port $QDRANT_PORT..."
            docker run -d \
                --name lawyerfactory-qdrant \
                -p $QDRANT_PORT:6333 \
                -v "$PROJECT_ROOT/qdrant_storage:/qdrant/storage" \
                qdrant/qdrant:latest >/dev/null 2>&1 || warn "Could not start Qdrant with Docker"
        else
            warn "Docker not found - Qdrant vector store may not be available"
        fi
    else
        log "Qdrant already running on port $QDRANT_PORT"
    fi
}

# Start backend server
start_backend() {
    log "Starting backend server..."
    
    # Find available port
    BACKEND_PORT=$(find_available_port $BACKEND_PORT)
    log "Backend will run on port $BACKEND_PORT"
    
    # Export environment variables
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    export FLASK_ENV=development
    export BACKEND_PORT=$BACKEND_PORT
    
    # Start backend in background
    cd "$PROJECT_ROOT/apps/api"
    python server.py --port $BACKEND_PORT > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_ROOT/.backend.pid"
    
    cd "$PROJECT_ROOT"
    
    # Wait for backend to be ready
    log "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:$BACKEND_PORT/api/health >/dev/null 2>&1; then
            log "Backend started successfully (PID: $BACKEND_PID)"
            return 0
        fi
        sleep 1
    done
    
    error "Backend failed to start within 30 seconds"
    if [ -f "$PROJECT_ROOT/logs/backend.log" ]; then
        error "Last 10 lines of backend log:"
        tail -n 10 "$PROJECT_ROOT/logs/backend.log"
    fi
    return 1
}

# Start frontend server
start_frontend() {
    if [ ! -d "apps/ui" ] && [ ! -d "apps" ]; then
        warn "Frontend directory not found - skipping frontend startup"
        return 0
    fi
    
    log "Starting frontend server..."
    
    # Find available port
    FRONTEND_PORT=$(find_available_port $FRONTEND_PORT)
    log "Frontend will run on port $FRONTEND_PORT"
    
    # Determine frontend location and type
    if [ -f "apps/package.json" ]; then
        # Vite app in apps folder
        cd apps
        
        # Check if npm dependencies are installed
        if [ ! -d "node_modules" ]; then
            log "Installing frontend dependencies..."
            npm install
        fi
        
        # Start Vite dev server
        VITE_BACKEND_URL="http://localhost:$BACKEND_PORT" npm run dev -- --port $FRONTEND_PORT --host > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend.pid"
        cd "$PROJECT_ROOT"
    elif [ -f "apps/ui/package.json" ]; then
        # Frontend in apps/ui folder
        cd apps/ui
        
        if [ ! -d "node_modules" ]; then
            log "Installing frontend dependencies..."
            npm install
        fi
        
        BACKEND_URL="http://localhost:$BACKEND_PORT" npm start -- --port $FRONTEND_PORT > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend.pid"
        cd "$PROJECT_ROOT"
    else
        warn "Could not determine frontend structure"
        return 0
    fi
    
    log "Frontend started (PID: $FRONTEND_PID)"
}

# Health check
health_check() {
    log "Running health checks..."
    
    # Backend health
    if curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then
        log "✓ Backend healthy"
    else
        error "✗ Backend unhealthy"
    fi
    
    # Qdrant health
    if curl -s http://localhost:$QDRANT_PORT/health >/dev/null 2>&1; then
        log "✓ Qdrant healthy"
    else
        warn "✗ Qdrant unhealthy"
    fi
    
    # Storage directories
    if [ -d "$WORKFLOW_STORAGE_PATH" ] && [ -d "$UPLOAD_DIR" ]; then
        log "✓ Storage directories exist"
    else
        warn "✗ Storage directories missing"
    fi
}

# Cleanup function
cleanup() {
    log "Shutting down services..."
    
    if [ -f .backend.pid ]; then
        kill $(cat .backend.pid) 2>/dev/null || true
        rm .backend.pid
    fi
    
    if [ -f .frontend.pid ]; then
        kill $(cat .frontend.pid) 2>/dev/null || true
        rm .frontend.pid
    fi
    
    log "Shutdown complete"
}

# Main execution
main() {
    log "LawyerFactory Launch System"
    log "============================"
    
    # Create logs directory
    mkdir -p logs
    
    # Setup trap for cleanup
    trap cleanup EXIT INT TERM
    
    # Run setup steps
    validate_environment
    setup_python
    start_qdrant
    start_backend || exit 1
    start_frontend
    
    # Run health checks
    sleep 2
    health_check
    
    # Display access information
    log ""
    log "============================"
    log "LawyerFactory is running!"
    log "============================"
    log "Backend:  http://localhost:$BACKEND_PORT"
    log "Frontend: http://localhost:$FRONTEND_PORT"
    log "Qdrant:   http://localhost:$QDRANT_PORT"
    log ""
    log "Press Ctrl+C to stop all services"
    log ""
    
    # Keep script running
    wait
}

main "$@"
