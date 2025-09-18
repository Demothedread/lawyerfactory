#!/usr/bin/env bash

# LawyerFactory Launch Script
# Wrapper script that calls the unified system launcher
# Usage: ./launch.sh [options]

# Redirect to the new unified launcher
exec "$(dirname "${BASH_SOURCE[0]}")/launch-system.sh" "$@"
