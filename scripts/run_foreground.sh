#!/usr/bin/env bash
set -euo pipefail

# Change to repository root (script located in scripts/)
cd "$(dirname "$0")/.."
# Ensure PYTHONPATH includes project root and src so imports resolve consistently
export PYTHONPATH="$(pwd):$(pwd)/src:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1

# Activate project's venv if present
if [ -f "./law_venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source ./law_venv/bin/activate
fi

# Disable Flask/Werkzeug reloader and debug to avoid termios errors in some terminals
export FLASK_ENV=production
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

echo "Starting app in foreground (python app.py). Press Ctrl-C to stop."
# Run without the werkzeug reloader by passing debug=False inside app or relying on FLASK_ENV=production
python -u app.py