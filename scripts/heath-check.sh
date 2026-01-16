#!/bin/bash
# filepath: scripts/health-check.sh
# Comprehensive health check for all LawyerFactory services

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment
source .env 2>/dev/null || true

# Default ports
BACKEND_PORT=${BACKEND_PORT:-5000}
QDRANT_PORT=${QDRANT_PORT:-6333}

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local name=$1
    local url=$2
    
    if curl -sf "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not responding"
        return 1
    fi
}

echo "LawyerFactory Health Check"
echo "=========================="

# Backend health
check_service "Backend API" "http://localhost:$BACKEND_PORT/health"

# Qdrant health
check_service "Qdrant Vector Store" "http://localhost:$QDRANT_PORT/health"

# Storage directories
if [ -d "$WORKFLOW_STORAGE_PATH" ] && [ -d "$UPLOAD_DIR" ]; then
    echo -e "${GREEN}✓${NC} Storage directories exist"
else
    echo -e "${YELLOW}!${NC} Storage directories missing"
fi

# Python environment
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo -e "${GREEN}✓${NC} Python virtual environment exists"
else
    echo -e "${RED}✗${NC} Python virtual environment missing"
fi

# API keys
if [ -n "$OPENAI_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$GROQ_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} AI service API keys configured"
else
    echo -e "${RED}✗${NC} No AI service API keys found"
fi

echo "=========================="