# Launch System Consolidation

## Overview

All launch scripts have been consolidated into a single canonical `launch.sh` script that supports multiple modes and configurations.

**Status**: ✅ Complete - Use only `launch.sh` going forward

## Before (Fragmented)

```bash
./launch.sh              # Basic launch (unclear mode)
./launch-dev.sh          # Development mode
./launch-prod.sh         # Production mode  
./launch-full-system.sh  # Full system with all services
```

**Problems**:
- Multiple scripts to maintain
- Inconsistent behavior across scripts
- Difficult to track which version is current
- No unified argument parsing
- Duplicate logic across files

## After (Unified)

```bash
./launch.sh              # Development mode (default)
./launch.sh --prod       # Production mode
./launch.sh --full       # Full system with Qdrant
```

## Usage Guide

### Development Mode (Default)

```bash
./launch.sh
```

Starts:
- ✅ Backend server (Flask + Socket.IO)
- ✅ Frontend server (React + Vite)
- ❌ Qdrant (not needed in development)

### Production Mode

```bash
./launch.sh --prod
```

Starts:
- ✅ Backend server (optimized, production environment)
- ❌ Frontend (assumes pre-built)
- ❌ Qdrant

### Full System Mode

```bash
./launch.sh --full-system
```

Starts:
- ✅ Backend server
- ✅ Frontend server
- ✅ Qdrant vector store (Docker)

## Advanced Options

### Custom Ports

```bash
./launch.sh --dev --frontend-port 8080 --backend-port 8000
```

### Skip Specific Services

```bash
./launch.sh --backend-only         # Backend only
./launch.sh --skip-frontend        # Backend + Qdrant
./launch.sh --skip-qdrant          # Dev mode without Qdrant
```

### Health Checks & Cleanup

```bash
./launch.sh --no-health-check      # Skip health checks
./launch.sh --no-cleanup           # Keep processes on exit
```

### Debugging

```bash
./launch.sh --verbose              # Detailed output
./launch.sh --debug                # Same as --verbose
./launch.sh --help                 # Show all options
```

## Features

### ✅ Automatic Port Detection

If default ports are in use, finds next available port:

```bash
$ ./launch.sh
[LawyerFactory] Backend will run on port 5001  # 5000 was in use
```

### ✅ Health Checks

Validates all running services:

```bash
[SUCCESS] ✓ Backend healthy
[SUCCESS] ✓ Qdrant healthy
[SUCCESS] ✓ Storage directories exist
```

### ✅ Process Tracking

Stores PIDs for easy cleanup:

```bash
cat .backend.pid    # Backend process ID
cat .frontend.pid   # Frontend process ID
```

### ✅ Unified Logging

All output goes to both console and `logs/launch.log`:

```bash
tail -f logs/launch.log  # Watch launch logs
tail -f logs/backend.log # Watch backend logs
tail -f logs/frontend.log # Watch frontend logs
```

### ✅ Graceful Shutdown

Press `Ctrl+C` to cleanly shutdown all services and cleanup.

## Deprecated Scripts

The following scripts are **deprecated** and should not be used:

- ❌ `launch-dev.sh` → Use `./launch.sh` (or `./launch.sh --dev`)
- ❌ `launch-prod.sh` → Use `./launch.sh --prod`
- ❌ `launch-full-system.sh` → Use `./launch.sh --full-system`

### Migration Guide

| Old Script | New Command |
|-----------|------------|
| `./launch-dev.sh` | `./launch.sh` |
| `./launch-dev.sh --frontend-port 8080` | `./launch.sh --frontend-port 8080` |
| `./launch-prod.sh` | `./launch.sh --prod` |
| `./launch-prod.sh --backend-port 8000` | `./launch.sh --prod --backend-port 8000` |
| `./launch-full-system.sh` | `./launch.sh --full-system` |

## Environment Variables

The new launch script respects:

```bash
FLASK_ENV              # Set to 'production' in prod mode
PYTHONPATH             # Automatically set to include src/
VITE_BACKEND_URL       # Automatically set for frontend
BACKEND_PORT           # Custom backend port
FRONTEND_PORT          # Custom frontend port
QDRANT_PORT            # Custom Qdrant port
```

## VS Code Integration

The unified script works with existing VS Code tasks:

```bash
# Run via VS Code task runner
Ctrl+Shift+P → "Tasks: Run Task" → "launch dev script"
```

## Architecture Benefits

1. **Single Source of Truth**: One script to maintain
2. **Consistent Behavior**: Same validation, logging, cleanup
3. **Flexible Configuration**: Multiple modes via arguments
4. **Better Error Handling**: Unified error messages and recovery
5. **Easier Debugging**: Centralized logging
6. **Clear Documentation**: Built-in help system

## Troubleshooting

### Port Already in Use

```bash
# Script automatically finds next available port
./launch.sh
```

Or explicitly specify:

```bash
./launch.sh --backend-port 5001 --frontend-port 3001
```

### Backend Not Starting

```bash
# Check backend logs
tail -f logs/backend.log

# Or run with verbose output
./launch.sh --verbose
```

### Frontend Not Connecting

```bash
# Ensure backend is running first
./launch.sh --skip-frontend  # Start backend

# Then in another terminal
./launch.sh --skip-backend   # Start frontend (uses running backend)
```

### Services Don't Stop on Ctrl+C

```bash
# Kill manually by PID
kill $(cat .backend.pid)
kill $(cat .frontend.pid)

# Or use cleanup option
./launch.sh --no-cleanup  # Then manually: pkill -f "python server.py"
```

## Implementation Details

- **Language**: Bash (POSIX-compliant)
- **Shell Compatibility**: bash, zsh, sh
- **Logging**: `logs/launch.log`
- **Process Tracking**: `.backend.pid`, `.frontend.pid`
- **Environment Setup**: Virtual environment auto-creation
- **Health Checks**: HTTP endpoint validation with retry logic

## Future Improvements

Potential enhancements:

1. Docker-based deployment option
2. Load balancing for multiple backends
3. Database migration runner
4. Automated backup scheduler
5. Performance monitoring integration

## References

- See `./launch.sh` for implementation
- See copilot-instructions.md for system architecture
- See README.md for general setup
