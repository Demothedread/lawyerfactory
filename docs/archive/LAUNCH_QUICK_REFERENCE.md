# 🚀 LawyerFactory Launch Quick Reference

## One Command to Rule Them All

```bash
./launch.sh  # That's it! Starts dev environment
```

## Three Main Modes

```bash
./launch.sh              # 👈 Development (default)
./launch.sh --prod       # 👈 Production
./launch.sh --full       # 👈 Full system with Qdrant
```

## Common Commands

```bash
# Development
./launch.sh                              # Standard dev

# Production  
./launch.sh --prod                       # Backend only

# Full system (with vector store)
./launch.sh --full-system                # All services + Qdrant

# Custom ports
./launch.sh --frontend-port 8080         # Custom frontend port
./launch.sh --backend-port 8000          # Custom backend port

# Backend only
./launch.sh --skip-frontend              # No frontend

# Debugging
./launch.sh --verbose                    # Detailed output
./launch.sh --help                       # See all options

# Advanced
./launch.sh --no-health-check            # Skip health checks
./launch.sh --no-cleanup                 # Keep processes on exit
```

## What Gets Started

### Development Mode (default)
- ✅ Backend (http://localhost:5000)
- ✅ Frontend (http://localhost:3000)
- ❌ Qdrant

### Production Mode (--prod)
- ✅ Backend (http://localhost:5000)
- ❌ Frontend
- ❌ Qdrant

### Full System (--full-system)
- ✅ Backend (http://localhost:5000)
- ✅ Frontend (http://localhost:3000)
- ✅ Qdrant (http://localhost:6333)

## Logs

```bash
tail -f logs/launch.log     # Watch startup events
tail -f logs/backend.log    # Watch backend
tail -f logs/frontend.log   # Watch frontend
```

## Stop Services

```bash
# Press Ctrl+C in the terminal running launch.sh
# Or in a new terminal:
kill $(cat .backend.pid)
kill $(cat .frontend.pid)
```

## Troubleshooting

```bash
# Port in use? Script finds next available automatically
./launch.sh

# Backend won't start?
tail -f logs/backend.log

# Need more details?
./launch.sh --verbose

# See all options
./launch.sh --help
```

## Default Access Points

```
Frontend:  http://localhost:3000
Backend:   http://localhost:5000
API Docs:  http://localhost:5000/api/health
Qdrant:    http://localhost:6333 (only in --full-system)
```

## Environment Files

```
.env              # Configuration (created from .env.example if missing)
.backend.pid      # Backend process ID
.frontend.pid     # Frontend process ID
logs/             # All startup and service logs
```

---

**Need more details?** Run `./launch.sh --help` or see `LAUNCH_SYSTEM_CONSOLIDATION.md`
