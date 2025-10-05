# Phase Button Functionality Fix - Frontend/Backend Mismatch 🔧

## Problem Identified

**The phase workflow buttons in the UI don't work because of a critical frontend-backend API endpoint mismatch.**

### Root Cause Analysis

#### Frontend Expectation (PhasePipeline.jsx)
```javascript
// Line 348 in PhasePipeline.jsx
const response = await fetch(`${apiEndpoint}/${phaseId}/start`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ case_id: caseId }),
});
```

**Frontend tries to call:**
- `/api/phases/phaseA01_intake/start` ❌
- `/api/phases/phaseA02_research/start` ❌  
- `/api/phases/phaseA03_outline/start` ❌
- `/api/phases/phaseB01_review/start` ❌
- `/api/phases/phaseB02_drafting/start` ❌
- `/api/phases/phaseC01_editing/start` ❌
- `/api/phases/phaseC02_orchestration/start` ❌

#### Backend Reality (server.py)
```python
# Only these endpoints exist:
@app.route("/api/intake", methods=["POST"])                    # ✓
@app.route("/api/research/start", methods=["POST"])            # ✓
@app.route("/api/outline/generate", methods=["POST"])          # ✓
# NO /api/phases/* routes!                                     # ❌
```

**Backend has:**
- `/api/intake` (Phase A01 - Intake)
- `/api/research/start` (Phase A02 - Research)
- `/api/outline/generate` (Phase A03 - Outline)
- **MISSING**: Phase B01, B02, C01, C02 endpoints

### Why This Happens

1. **Incorrect API Endpoint Configuration**: `PhasePipeline` uses `apiEndpoint="/api/phases"` but server has scattered endpoints
2. **Incomplete Backend Implementation**: Only 3 of 7 phases have backend routes
3. **No Phase Orchestration Route**: Backend lacks unified phase orchestration system
4. **Launch Script Mismatch**: `launch-dev.sh` starts services but doesn't validate API contract

## Impact Assessment

### User Experience Impact
- ✅ **Upload Evidence** - Works (uses `/api/storage/documents`)
- ✅ **Evidence Table Display** - Works (uses `/api/evidence`)
- ❌ **Start Phase Pipeline Button** - **BROKEN** (calls non-existent `/api/phases/phaseA01_intake/start`)
- ❌ **Individual Phase Buttons** - **BROKEN** (call non-existent routes)
- ❌ **Phase Progress Updates** - **BROKEN** (Socket.IO events never fire)
- ❌ **Automated Workflow** - **BROKEN** (phases don't execute)

### What Users See
```
Browser Console Errors:
❌ POST http://localhost:5000/api/phases/phaseA01_intake/start 404 (Not Found)
❌ Failed to start phase: Not Found
⚠️ Max retries (3) exceeded for phaseA01_intake
```

## Solution Options

### Option 1: Quick Fix - Update Frontend to Use Existing Endpoints ⚡

**Pros**: Immediate fix, no backend changes needed  
**Cons**: Still missing 4 phases (B01, B02, C01, C02)

**Implementation**:

```javascript
// File: apps/ui/react-app/src/components/ui/PhasePipeline.jsx
// Replace startPhase function (line 330) with:

const startPhase = async (phaseId) => {
  if (!caseId) {
    addToast("Case ID required to start phase", { severity: "warning" });
    return;
  }

  setLoading(true);

  try {
    // Map phase IDs to actual backend endpoints
    const endpointMap = {
      'phaseA01_intake': { 
        url: '/api/intake', 
        method: 'POST',
        payload: { case_id: caseId, files: [] }
      },
      'phaseA02_research': { 
        url: '/api/research/start', 
        method: 'POST',
        payload: { case_id: caseId, research_query: 'Legal research query' }
      },
      'phaseA03_outline': { 
        url: '/api/outline/generate', 
        method: 'POST',
        payload: { case_id: caseId }
      },
      // TODO: Add B01, B02, C01, C02 when backend implements them
    };

    const endpoint = endpointMap[phaseId];
    if (!endpoint) {
      throw new Error(`Phase ${phaseId} not yet implemented on backend`);
    }

    const response = await fetch(endpoint.url, {
      method: endpoint.method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(endpoint.payload),
    });

    if (!response.ok) {
      throw new Error(`Failed to start phase: ${response.statusText}`);
    }

    const result = await response.json();
    setPipelineStatus("running");
    
    addToast(`✅ Started ${phaseId}`, {
      severity: "success",
      title: "Phase Started",
    });

  } catch (error) {
    console.error("Failed to start phase:", error);
    addToast(`❌ ${error.message}`, {
      severity: "error",
      title: "Phase Start Failed",
    });
  } finally {
    setLoading(false);
  }
};
```

### Option 2: Comprehensive Fix - Implement Backend Phase Orchestrator 🏭

**Pros**: Proper architecture, supports all 7 phases, scalable  
**Cons**: Requires backend development, more time

**Implementation**:

```python
# File: apps/api/server.py
# Add unified phase orchestration endpoint

@app.route("/api/phases/<phase_id>/start", methods=["POST"])
def start_phase(phase_id):
    """
    Unified phase orchestration endpoint
    Maps phase IDs to their respective handlers
    """
    data = request.get_json()
    case_id = data.get("case_id")
    
    if not case_id:
        return jsonify({"error": "case_id required"}), 400
    
    # Phase routing map
    phase_handlers = {
        "phaseA01_intake": handle_intake_phase,
        "phaseA02_research": handle_research_phase,
        "phaseA03_outline": handle_outline_phase,
        "phaseB01_review": handle_review_phase,      # NEW
        "phaseB02_drafting": handle_drafting_phase,  # NEW
        "phaseC01_editing": handle_editing_phase,    # NEW
        "phaseC02_orchestration": handle_orchestration_phase,  # NEW
    }
    
    handler = phase_handlers.get(phase_id)
    if not handler:
        return jsonify({"error": f"Unknown phase: {phase_id}"}), 404
    
    try:
        # Execute phase handler with Socket.IO updates
        result = handler(case_id, data)
        
        # Emit phase started event
        socketio.emit("phase_started", {
            "phase": phase_id,
            "case_id": case_id,
            "timestamp": time.time()
        })
        
        return jsonify({
            "success": True,
            "phase": phase_id,
            "case_id": case_id,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Phase {phase_id} failed: {e}")
        
        # Emit phase error event
        socketio.emit("phase_error", {
            "phase": phase_id,
            "case_id": case_id,
            "error": str(e),
            "timestamp": time.time()
        })
        
        return jsonify({"error": str(e)}), 500


def handle_intake_phase(case_id, data):
    """Phase A01: Document Intake"""
    if not intake_processor:
        return {"status": "mock", "message": "Intake processor not available"}
    
    # Emit progress updates
    socketio.emit("phase_progress_update", {
        "phase": "A01_Intake",
        "progress": 50,
        "message": "Processing documents..."
    })
    
    result = intake_processor.process(case_id, data)
    
    socketio.emit("phase_progress_update", {
        "phase": "A01_Intake",
        "progress": 100,
        "message": "Intake complete"
    })
    
    return result


def handle_research_phase(case_id, data):
    """Phase A02: Legal Research"""
    if not research_bot:
        return {"status": "mock", "message": "Research bot not available"}
    
    research_query = data.get("research_query", "")
    
    socketio.emit("phase_progress_update", {
        "phase": "A02_Research",
        "progress": 30,
        "message": "Searching legal databases..."
    })
    
    result = research_bot.research(research_query)
    
    socketio.emit("phase_progress_update", {
        "phase": "A02_Research",
        "progress": 100,
        "message": "Research complete"
    })
    
    return result


def handle_outline_phase(case_id, data):
    """Phase A03: Case Outline"""
    if not outline_generator:
        return {"status": "mock", "message": "Outline generator not available"}
    
    socketio.emit("phase_progress_update", {
        "phase": "A03_Outline",
        "progress": 40,
        "message": "Generating case structure..."
    })
    
    result = outline_generator.generate(case_id)
    
    socketio.emit("phase_progress_update", {
        "phase": "A03_Outline",
        "progress": 100,
        "message": "Outline complete"
    })
    
    return result


def handle_review_phase(case_id, data):
    """Phase B01: Quality Review (STUB - TO BE IMPLEMENTED)"""
    socketio.emit("phase_progress_update", {
        "phase": "B01_Review",
        "progress": 100,
        "message": "Review phase (mock) complete"
    })
    return {"status": "mock", "message": "Review phase not yet implemented"}


def handle_drafting_phase(case_id, data):
    """Phase B02: Document Drafting (STUB - TO BE IMPLEMENTED)"""
    socketio.emit("phase_progress_update", {
        "phase": "B02_Drafting",
        "progress": 100,
        "message": "Drafting phase (mock) complete"
    })
    return {"status": "mock", "message": "Drafting phase not yet implemented"}


def handle_editing_phase(case_id, data):
    """Phase C01: Final Editing (STUB - TO BE IMPLEMENTED)"""
    socketio.emit("phase_progress_update", {
        "phase": "C01_Editing",
        "progress": 100,
        "message": "Editing phase (mock) complete"
    })
    return {"status": "mock", "message": "Editing phase not yet implemented"}


def handle_orchestration_phase(case_id, data):
    """Phase C02: Final Orchestration (STUB - TO BE IMPLEMENTED)"""
    socketio.emit("phase_progress_update", {
        "phase": "C02_Orchestration",
        "progress": 100,
        "message": "Orchestration phase (mock) complete"
    })
    return {"status": "mock", "message": "Orchestration phase not yet implemented"}
```

### Option 3: Hybrid Approach - Mock Missing Phases 🎭

**Pros**: Quick fix with proper architecture setup  
**Cons**: Phases B01-C02 won't actually process, just simulate

**Implementation**: Combine Option 2 backend route with mock handlers for missing phases

## Recommended Solution

**Go with Option 2 (Comprehensive Fix)** for these reasons:

1. ✅ **Proper Architecture**: Aligns with project design in `.github/copilot-instructions.md`
2. ✅ **Scalable**: Easy to add real implementations for B01-C02 later
3. ✅ **Consistent API**: Single `/api/phases/<phase_id>/start` endpoint pattern
4. ✅ **Socket.IO Integration**: Properly emits phase progress events
5. ✅ **Launch Script Compatible**: Works with existing `launch-dev.sh`

## Implementation Steps

### Step 1: Add Backend Phase Orchestrator
1. Add unified phase route to `apps/api/server.py`
2. Implement handlers for A01, A02, A03 (map to existing logic)
3. Add stub handlers for B01, B02, C01, C02 (mock responses)
4. Ensure Socket.IO events fire correctly

### Step 2: Verify Frontend Configuration
1. Check `PhasePipeline.jsx` uses `apiEndpoint="/api/phases"`
2. Verify Socket.IO event listeners match backend emissions
3. Test retry logic with mock failures

### Step 3: Test End-to-End Workflow
1. Upload evidence (Phase A01 trigger)
2. Click "Start Phase Pipeline"
3. Verify each phase button works
4. Check Socket.IO events in browser console
5. Confirm phase progression A01→A02→A03

### Step 4: Implement Missing Phases (Future Work)
1. Phase B01: Quality review agent integration
2. Phase B02: Document drafting with templates
3. Phase C01: Legal formatting and citation
4. Phase C02: Final orchestration and delivery

## Testing Checklist

```bash
# Terminal 1: Start backend
cd /Users/jreback/Projects/lawyerfactory
./launch-dev.sh

# Terminal 2: Test phase endpoints
curl -X POST http://localhost:5000/api/phases/phaseA01_intake/start \
  -H "Content-Type: application/json" \
  -d '{"case_id": "test_case_001"}'

curl -X POST http://localhost:5000/api/phases/phaseA02_research/start \
  -H "Content-Type: application/json" \
  -d '{"case_id": "test_case_001", "research_query": "contract law"}'

curl -X POST http://localhost:5000/api/phases/phaseA03_outline/start \
  -H "Content-Type: application/json" \
  -d '{"case_id": "test_case_001"}'

# Check Socket.IO events in browser DevTools:
# 1. Open http://localhost:3000
# 2. DevTools → Network → WS (WebSocket)
# 3. Click on Socket.IO connection
# 4. Monitor Messages tab for phase_progress_update events
```

## Files to Modify

### Backend (Required)
1. ✅ `/apps/api/server.py` - Add `/api/phases/<phase_id>/start` route
2. ✅ `/apps/api/server.py` - Add phase handler functions
3. ✅ `/apps/api/server.py` - Add Socket.IO event emissions

### Frontend (Optional - already correct)
1. ⚠️ `/apps/ui/react-app/src/components/ui/PhasePipeline.jsx` - Already uses correct endpoint pattern
2. ✅ `/apps/ui/react-app/src/services/apiService.js` - Already has phase methods

### Launch Script (No changes needed)
1. ✅ `/launch-dev.sh` - Already starts Flask on port 5000 and React on port 3000

## Expected Behavior After Fix

### Before Fix ❌
```
User clicks "Start Phase Pipeline" → 404 Error → Buttons don't work
```

### After Fix ✅
```
User clicks "Start Phase Pipeline"
  → POST /api/phases/phaseA01_intake/start
  → Backend emits: phase_started event
  → Backend emits: phase_progress_update (50%)
  → Frontend shows: "📥 A01_Intake: Processing documents..."
  → Backend emits: phase_progress_update (100%)
  → Frontend shows: "✅ A01_Intake: Intake complete"
  → Auto-advance to phaseA02_research
  → Repeat for all 7 phases
```

## Verification Commands

```bash
# 1. Check backend routes exist
curl http://localhost:5000/api/health | jq

# 2. Test phase endpoint (should return 200, not 404)
curl -X POST http://localhost:5000/api/phases/phaseA01_intake/start \
  -H "Content-Type: application/json" \
  -d '{"case_id": "test"}' -v

# 3. Monitor Socket.IO events
# In browser console:
const socket = io('http://localhost:5000');
socket.on('phase_progress_update', (data) => console.log('Progress:', data));
socket.on('phase_started', (data) => console.log('Started:', data));
socket.on('phase_completed', (data) => console.log('Completed:', data));
```

## Related Documentation

- **Project Architecture**: `.github/copilot-instructions.md`
- **Phase Structure**: `src/lawyerfactory/phases/README.md`
- **API Service**: `apps/ui/react-app/src/services/apiService.js`
- **Launch Script**: `launch-dev.sh`
- **Backend Server**: `apps/api/server.py`

## Summary

**Problem**: Frontend buttons don't work because they call `/api/phases/*` endpoints that don't exist on the backend.

**Root Cause**: API endpoint mismatch - frontend expects unified phase orchestration, backend has scattered individual endpoints.

**Solution**: Implement unified `/api/phases/<phase_id>/start` endpoint on backend with proper Socket.IO integration.

**Status**: 🔴 **CRITICAL** - Core workflow functionality is broken  
**Priority**: 🔥 **HIGH** - Should be fixed before production use  
**Complexity**: ⭐⭐⭐ **Medium** - Requires backend route addition and phase handler mapping

---

**Next Steps**: Implement Option 2 (Comprehensive Fix) by adding the phase orchestrator route to `server.py`.
