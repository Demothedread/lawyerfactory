#!/usr/bin/env bash

# LawyerFactory Unified Launch Script
# Canonical wrapper that routes to development or production launchers
# Usage: ./launch.sh [--production] [options]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_MODE=false

# Parse for production flag
for arg in "$@"; do
    if [[ "$arg" == "--production" ]]; then
        PRODUCTION_MODE=true
        break
    fi
done

# Route to appropriate launcher
if [[ "$PRODUCTION_MODE" == "true" ]]; then
    echo "🚀 Starting LawyerFactory in PRODUCTION mode..."
    exec "$SCRIPT_DIR/launch-prod.sh" "$@"
else
    echo "🔧 Starting LawyerFactory in DEVELOPMENT mode..."
    exec "$SCRIPT_DIR/launch-dev.sh" "$@"
fi
