# README Update: Unified Launch System

## Integration with Main README.md

The `README.md` has been updated to reference the unified launch system. This document explains the integration and provides guidance for maintaining consistency.

## Current Status

✅ Main README already references both:
- `./launch.sh` - New unified script
- `./launch.sh --production` - Production mode

✅ README Quick Start section includes:
- Development launch
- Production launch
- Custom port configuration
- Alternative launch methods

## What the README Currently Shows

### Quick Start Section (Lines 26-84)

```markdown
## 🚀 Quick Start - Complete System Launch

### Canonical Launch Scripts (Recommended)

**Development Mode (Default):**
./launch.sh

**Production Mode:**
./launch.sh --production
```

## How the README References Old Scripts

### ⚠️ Areas Still Referencing Old Scripts

1. **Line 34**: `chmod +x launch.sh launch-dev.sh` 
   - Should be: `chmod +x launch.sh` (only needed if not already executable)

2. **Line 37**: `./launch-dev.sh` 
   - Should be: `./launch.sh` or `./launch.sh --dev`

3. **Line 45**: `./launch-prod.sh` 
   - Should be: `./launch.sh --production` or `./launch.sh --prod`

4. **Line 82**: `./launch-dev.sh --frontend-port 3000 --backend-port 5000`
   - Should be: `./launch.sh --frontend-port 3000 --backend-port 5000`

## Recommended README Updates

### Update 1: Quick Start Section (Lines 32-38)

**Current:**
```bash
chmod +x launch.sh launch-dev.sh
./launch.sh
# OR directly:
./launch-dev.sh
```

**Recommended:**
```bash
# Make executable (one-time)
chmod +x launch.sh

# Launch (development mode is default)
./launch.sh
```

### Update 2: Production Mode (Lines 42-47)

**Current:**
```bash
chmod +x launch-prod.sh
./launch.sh --production
# OR directly:
./launch-prod.sh
```

**Recommended:**
```bash
# Production mode (backend only)
./launch.sh --production
```

### Update 3: Custom Ports Section (Lines 78-86)

**Current:**
```bash
# Development with custom ports
./launch-dev.sh --frontend-port 3000 --backend-port 5000

# Production with custom ports
./launch-prod.sh --frontend-port 443 --backend-port 8000
```

**Recommended:**
```bash
# Development with custom ports
./launch.sh --frontend-port 3000 --backend-port 5000

# Production with custom ports
./launch.sh --prod --frontend-port 443 --backend-port 8000
```

### Update 4: Alternative Launch Methods (Lines 87-100)

**Current:**
```bash
# Frontend-Only (Development):
cd apps/ui/react-app && npm run dev

# Backend-Only (API Server):
cd apps/api && python simple_server.py

# Custom Ports:
./launch-dev.sh --frontend-port 3000 --backend-port 5000
```

**Recommended:**
```bash
# Frontend-Only (Development):
cd apps/ui/react-app && npm run dev

# Backend-Only (API Server):
cd apps/api && python server.py

# Backend + Qdrant (Full System):
./launch.sh --full-system

# Custom Ports:
./launch.sh --frontend-port 3000 --backend-port 5000
```

## Additional Sections to Add to README

### New Section: Launch System Overview

Add after Quick Start section:

```markdown
## 📚 Launch System Guide

LawyerFactory uses a unified launch system that supports multiple modes:

### Modes

- **Development** (default): Backend + Frontend, no Qdrant
- **Production**: Backend only, production environment
- **Full System**: Backend + Frontend + Qdrant (Docker)

### Usage

```bash
./launch.sh              # Development (default)
./launch.sh --prod       # Production
./launch.sh --full       # Full system with Qdrant
./launch.sh --help       # See all options
```

### Help & Documentation

For detailed launch information:
- Quick reference: `LAUNCH_QUICK_REFERENCE.md`
- Comprehensive guide: `LAUNCH_SYSTEM_CONSOLIDATION.md`
- Built-in help: `./launch.sh --help`

### Common Tasks

```bash
# Backend only
./launch.sh --skip-frontend

# Custom ports
./launch.sh --frontend-port 8080 --backend-port 8000

# With detailed output
./launch.sh --verbose

# Skip health checks
./launch.sh --no-health-check
```
```

### New Section: Troubleshooting Launch Issues

Add in troubleshooting section:

```markdown
## 🔧 Launch Troubleshooting

### Port Already in Use

The launch script automatically detects available ports:

```bash
./launch.sh
# If port 5000 is in use, uses 5001, 5002, etc.
```

### Backend Won't Start

Check the backend logs:

```bash
tail -f logs/backend.log
```

Or run with verbose output:

```bash
./launch.sh --verbose
```

### Frontend Not Connecting

1. Ensure backend started: `./launch.sh --skip-frontend`
2. Note the backend port from output
3. Start frontend: `./launch.sh --skip-backend --frontend-port [same-port-from-above]`

### Services Don't Stop on Ctrl+C

Kill processes manually:

```bash
kill $(cat .backend.pid)
kill $(cat .frontend.pid)
```
```

## Migration Instructions for README

### Step 1: Update Quick Start Section
Replace old launch commands with new unified syntax

### Step 2: Add Launch System Guide Section
Insert comprehensive launch guide after Quick Start

### Step 3: Update Troubleshooting
Add new launch-specific troubleshooting section

### Step 4: Update References
Replace all `./launch-dev.sh` with `./launch.sh`
Replace all `./launch-prod.sh` with `./launch.sh --prod`
Replace all `./launch-full-system.sh` with `./launch.sh --full`

### Step 5: Add Links
Reference new documentation files:
- LAUNCH_QUICK_REFERENCE.md
- LAUNCH_SYSTEM_CONSOLIDATION.md

## Impact Assessment

### For Users
- ✅ Simpler commands (single script)
- ✅ Consistent behavior
- ✅ Better error messages
- ✅ More documentation

### For Maintainers
- ✅ Less code to maintain
- ✅ Easier to update
- ✅ Consistent patterns
- ✅ Better testing

## Backward Compatibility

- ✅ All existing launch methods still work
- ✅ Default behavior unchanged
- ✅ Environment variables respected
- ✅ Can revert to old scripts if needed

## Documentation Structure

After updates, documentation will be:

```
README.md
├── Quick Start (updated)
├── Launch System Guide (new)
├── Configuration (existing)
├── Development (existing)
└── Troubleshooting (updated)
        └── Launch Troubleshooting (new)

Supporting Documents:
├── LAUNCH_QUICK_REFERENCE.md
├── LAUNCH_SYSTEM_CONSOLIDATION.md
├── LAUNCH_SYSTEM_CONSOLIDATION_COMPLETE.md
└── launch.sh --help
```

## Recommended Timeline

1. **Immediate**: Share `LAUNCH_QUICK_REFERENCE.md` with team
2. **This Week**: Review and merge README updates
3. **This Month**: Monitor usage and gather feedback
4. **Next Month**: Remove old scripts from documentation
5. **After 30 days**: Archive old scripts in `_trash_staging/`

## Quality Assurance

Before finalizing README updates:

- [ ] Test all launch commands
- [ ] Verify port detection works
- [ ] Check error messages
- [ ] Validate examples in README
- [ ] Ensure links work
- [ ] Cross-reference with other docs

## Questions for Code Review

1. Should we keep references to old scripts for backward compatibility?
   - **Recommendation**: Keep in migration period, remove after 30 days

2. Should launch system docs be in separate files or README?
   - **Recommendation**: README for quick ref, separate files for details

3. How long should we support old scripts?
   - **Recommendation**: 30-day transition period, then archive

4. Should we add launch system to contribution guidelines?
   - **Recommendation**: Yes, for consistency

## Next Steps

1. Review this document
2. Propose README updates to team
3. Get approval for changes
4. Update README accordingly
5. Link to new documentation
6. Communicate changes to team
7. Monitor adoption and gather feedback

---

**Document Type**: Integration Guide  
**Version**: 1.0  
**Status**: Ready for Implementation  
**Date**: 2024
