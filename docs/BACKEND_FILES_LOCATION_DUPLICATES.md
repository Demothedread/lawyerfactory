# Backend Files Location & Duplicate Analysis

**Document Version:** 1.0  
**Date:** October 20, 2025  
**Status:** Architecture Reference

---

## 📍 Backend Files Location Map

### Directory Structure

```
/Users/jreback/Projects/LawyerFactory/src/
│
├── lawyerfactory/                           [Main Python Package]
│   ├── __init__.py
│   │
│   ├── api/                                 ⭐ [API ENDPOINTS]
│   │   ├── __init__.py
│   │   ├── evidence_queue_api.py            ✅ Evidence upload/processing routes
│   │   ├── shot_list.py                     ✅ Shot extraction API
│   │   └── timeline.py                      ✅ Timeline API
│   │
│   ├── storage/                             ⭐ [STORAGE & PROCESSING]
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   └── evidence_queue.py            ✅ Queue logic + classification
│   │   └── [other storage modules]
│   │
│   ├── config/                              ⭐ [CONFIGURATION]
│   │   ├── __init__.py
│   │   └── case_types.py                    ✅ Case type enums + classifiers
│   │
│   ├── phases/                              [PHASE IMPLEMENTATIONS]
│   │   ├── phaseA01_intake/
│   │   ├── phaseA02_research/
│   │   ├── phaseA03_outline/
│   │   ├── phaseB01_review/
│   │   │   └── ui/
│   │   │       └── api_app_main.py          ⭐ MAIN FLASK APP (Routes register here)
│   │   ├── phaseB02_drafting/
│   │   ├── phaseC01_editing/
│   │   └── phaseC02_orchestration/
│   │
│   ├── evidence/                            [EVIDENCE PROCESSING]
│   │   ├── __init__.py
│   │   ├── shotlist.py                      📋 Core shot extraction logic
│   │   ├── table.py                         📋 Evidence table functionality
│   │   └── react_grid.py                    📋 React integration
│   │
│   ├── agents/                              [AI AGENTS]
│   │   ├── analysis/
│   │   ├── drafting/
│   │   ├── intake/
│   │   ├── orchestration/
│   │   ├── research/
│   │   └── review/
│   │
│   ├── claims/                              [CLAIMS MANAGEMENT]
│   │   ├── matrix.py                        📋 Claims matrix logic
│   │   └── research_api.py                  📋 Claims research API
│   │
│   ├── lf_core/                             [CORE MODELS]
│   │   ├── models.py
│   │   ├── models_shared.py
│   │   ├── document_types.py
│   │   ├── agent_config.py
│   │   └── llm/
│   │
│   ├── knowledge_graph/                     [KNOWLEDGE GRAPH]
│   │   ├── api/
│   │   ├── core/
│   │   └── integrations/
│   │
│   ├── outline/                             [OUTLINE GENERATION]
│   │   ├── generator.py
│   │   ├── enhanced_generator.py
│   │   └── integration.py
│   │
│   ├── export/                              [DOCUMENT EXPORT]
│   │   ├── legal_document_generator.py
│   │   ├── renderers/
│   │   └── templates/
│   │
│   ├── ingest/                              [DOCUMENT INGESTION]
│   │   ├── adapters/
│   │   ├── assessors/
│   │   └── pipelines/
│   │
│   ├── kg/                                  [KG API]
│   │   ├── graph_api.py
│   │   ├── graph.py
│   │   ├── relations.py
│   │   └── legal_authorities.py
│   │
│   ├── research/                            [RESEARCH PIPELINE]
│   ├── post_production/                     [POST PRODUCTION]
│   ├── infra/                               [INFRASTRUCTURE]
│   ├── llm_integration/                     [LLM INTEGRATION]
│   └── compose/                             [COMPOSITION ENGINE]
│
└── shared/                                  [SHARED CODE]
```

---

## 🎯 Critical Backend Files

### For Evidence Processing Pipeline

| File | Path | Purpose | Language |
|------|------|---------|----------|
| **evidence_queue_api.py** | `src/lawyerfactory/api/` | REST endpoints for queue | Python (Flask) |
| **evidence_queue.py** | `src/lawyerfactory/storage/core/` | Queue logic + classifier | Python |
| **case_types.py** | `src/lawyerfactory/config/` | Case type taxonomy | Python |
| **api_app_main.py** | `src/lawyerfactory/phases/phaseB01_review/ui/` | Flask app setup | Python |

### For Downstream Components

| File | Path | Purpose | Language |
|------|------|---------|----------|
| **shot_list.py** | `src/lawyerfactory/evidence/` | Shot extraction | Python |
| **shot_list.py** | `src/lawyerfactory/api/` | Shot API wrapper | Python |
| **table.py** | `src/lawyerfactory/evidence/` | Evidence table logic | Python |
| **matrix.py** | `src/lawyerfactory/claims/` | Claims matrix logic | Python |

---

## 🔍 Duplicate/Similar Files Analysis

### Category 1: Evidence Shot Lists (Core Logic vs API)

#### File 1: `shot_list.py` (Core Logic)
**Location:** `/Users/jreback/Projects/LawyerFactory/src/lawyerfactory/evidence/shotlist.py`

**Purpose:** Core shot extraction and management
```python
# Expected functions/classes:
- ShotListGenerator
- extract_facts_from_evidence()
- build_shot_list()
- validate_shot()
```

**Responsible For:**
- Extracting key facts from evidence
- Building shot lists for drafting
- Managing shot metadata

#### File 2: `shot_list.py` (API Layer)
**Location:** `/Users/jreback/Projects/LawyerFactory/src/lawyerfactory/api/shot_list.py`

**Purpose:** REST API wrapper for shot list operations
```python
# Expected functions/classes:
- Flask routes for shot operations
- Endpoint handlers
- Request/response validation
```

**Responsible For:**
- HTTP endpoints for shot operations
- Frontend communication
- API documentation

**Relationship:** `api/shot_list.py` → imports and wraps → `evidence/shotlist.py`

✅ **Assessment:** This is GOOD design (not duplication)
- Core logic separated from API layer
- Follows separation of concerns
- API can be replaced without changing core

---

### Category 2: Evidence Upload Components (Two Different Purposes)

#### Component 1: `EvidenceUpload.jsx` (Generic Storage)
**Location:** `/Users/jreback/Projects/LawyerFactory/apps/ui/react-app/src/components/ui/EvidenceUpload.jsx`

**What It Does:**
```jsx
// Generic file upload to storage system
- Drag-and-drop interface
- File validation (size, type)
- Metadata dialog
- Progress tracking
- Upload to: /api/storage/documents
- Returns: object_id, evidence_id, s3_url
```

**Code Structure:**
- 300+ lines
- Uses: `useState`, `useCallback`, `useRef`
- Material-UI components
- Metadata management
- Error handling

**Use Cases:**
- Upload any document during case workflow
- Generic file storage needs
- Any phase that needs file uploads

**Example Usage:**
```jsx
<EvidenceUpload
  currentCaseId="CASE-001"
  sourcePhase="phaseA01_intake"
  maxFileSize={10 * 1024 * 1024}
  onUploadComplete={handleUploadComplete}
/>
```

#### Component 2: `EvidenceUploadQueue.jsx` (Specialized Classification)
**Location:** `/Users/jreback/Projects/LawyerFactory/apps/ui/react-app/src/components/ui/EvidenceUploadQueue.jsx`

**What It Does:**
```jsx
// Specialized for evidence with real-time classification
- Displays animated processing queue
- Real-time status updates (polling)
- Shows classification badges (Primary/Secondary)
- Shows evidence type (email, contract, etc.)
- Shows confidence scores
- Hierarchical grouping
- Error display per item
- Upload to: /api/evidence/queue/upload/<case_id>
```

**Code Structure:**
- 300+ lines
- Uses: `useState`, `useEffect`, `useCallback`
- Material-UI components
- Polling mechanism (2s intervals)
- Soviet-themed styling
- Rich UI with animations

**Use Cases:**
- Evidence intake workflow
- Classification-aware uploads
- Real-time feedback on processing
- Legal evidence pipeline

**Example Usage:**
```jsx
<EvidenceUploadQueue
  caseId="CASE-001"
  pollingInterval={2000}
  onQueueStatusUpdate={handleStatusUpdate}
/>
```

### Comparison Matrix

| Aspect | EvidenceUpload | EvidenceUploadQueue |
|--------|---|---|
| **Purpose** | Generic file storage | Evidence classification & queue |
| **Backend API** | `/api/storage/documents` | `/api/evidence/queue/upload` |
| **Files Upload** | One or multiple | Multiple (batch) |
| **Processing** | None (just stores) | Active processing |
| **UI Display** | Simple list of files | Animated queue with real-time updates |
| **Classification** | No | Yes (Primary/Secondary + Type) |
| **Metadata** | Optional metadata dialog | Extracted automatically |
| **Confidence** | No | Yes (classification confidence %) |
| **Error Handling** | Per-file error messages | Per-file error + retry logic |
| **Polling** | No | Yes (every 2 seconds) |
| **Lines of Code** | ~300 | ~300 |
| **When to Use** | General uploads | Legal evidence intake |
| **Soviet Theme** | No | Yes |

### 🎯 Assessment: NOT Duplicates

**Verdict:** ✅ These are **intentionally different components** for different workflows

**Why They're Different:**
1. **Different APIs:** Different backend endpoints
2. **Different UI:** One is simple, one is animated with real-time updates
3. **Different Data:** One stores generic files, one classifies evidence
4. **Different Purpose:** One is generic upload, one is specialized legal workflow
5. **Different State:** One doesn't poll, one polls every 2 seconds

**Recommendation:** Keep both. They serve different purposes.

---

### Category 3: Evidence Tables (Data vs Rendering)

#### File 1: `table.py` (Core Logic)
**Location:** `/Users/jreback/Projects/LawyerFactory/src/lawyerfactory/evidence/table.py`

**Purpose:** Backend evidence table logic
```python
# Expected functions:
- build_evidence_table()
- filter_evidence()
- sort_evidence()
- generate_table_data()
```

#### Component 1: `EvidenceTable.jsx` (Frontend Rendering)
**Location:** `/Users/jreback/Projects/LawyerFactory/apps/ui/react-app/src/components/ui/EvidenceTable.jsx`

**Purpose:** React component to display evidence table
```jsx
// Renders hierarchical evidence display
- Groups by evidence_class (primary/secondary)
- Sub-groups by evidence_type
- Shows confidence scores
- Displays summaries
- Allows filtering and sorting
```

**Relationship:** 
- `table.py` → builds data structure
- `EvidenceTable.jsx` → displays the data

✅ **Assessment:** This is GOOD design
- Separation of backend logic and frontend rendering
- Backend provides data, frontend renders
- Can swap frontend without changing backend

---

## 📊 Summary of File Organization

### Backend Files (Python)

```
Tier 1: Configuration & Rules
├── case_types.py ........................ Case type definitions and classifiers
│   └── Used by: evidence_queue.py

Tier 2: Core Business Logic
├── evidence_queue.py .................... Queue management + classification
├── shotlist.py ......................... Shot extraction logic
├── table.py ............................ Evidence table operations
└── matrix.py ........................... Claims matrix operations

Tier 3: API Layer (Flask Routes)
├── evidence_queue_api.py ............... Exposes queue via REST
├── shot_list.py ........................ Exposes shots via REST
└── [other API files]

Tier 4: Application Setup
└── api_app_main.py ..................... Flask app + route registration
    └── Calls: register_evidence_queue_routes(app)
```

### Frontend Files (React/JSX)

```
Tier 1: Upload Components
├── EvidenceUpload.jsx .................. Generic file upload
└── EvidenceUploadQueue.jsx ............. Evidence with classification

Tier 2: Display Components
├── EvidenceTable.jsx ................... Hierarchical evidence display
├── ShotList.jsx ........................ Shots from evidence
└── ClaimsMatrix.jsx .................... Claims with evidence support

Tier 3: Support
├── [other UI components]
└── [styling & utilities]
```

### Data Flow Between Layers

```
Frontend (React)
    ↓
EvidenceUploadQueue.jsx ──────── calls ──────→ POST /api/evidence/queue/upload
    ↓
Backend (Flask/Python)
    ↓
evidence_queue_api.py (routes)
    ↓
evidence_queue.py (business logic)
    ├── case_types.py (classification rules)
    └── storage operations
    ↓
Frontend (React)
    ↓
EvidenceTable.jsx ──────── calls ──────→ GET /api/evidence/queue/filter
    ↓
Backend (Flask/Python)
    ↓
evidence_queue_api.py (routes)
    ↓
evidence_queue.py (retrieves data)
    ↓
Frontend (React) renders data
```

---

## ❌ Issues in Current Codebase

### Issue 1: Routes Not Registered ⚠️

**Location:** `src/lawyerfactory/phases/phaseB01_review/ui/api_app_main.py`

**Problem:** The function exists but is never called
```python
# evidence_queue_api.py defines this function:
def register_evidence_queue_routes(app):
    app.register_blueprint(evidence_queue_bp)
    logger.info("Registered evidence queue API routes")

# But api_app_main.py never calls it!
```

**Fix:**
```python
# Add to api_app_main.py after app = Flask(__name__)
from lawyerfactory.api.evidence_queue_api import register_evidence_queue_routes
register_evidence_queue_routes(app)
```

### Issue 2: Inconsistent Naming ⚠️

**Inconsistency:**
- Backend: `shotlist.py` (no underscore)
- API: `shot_list.py` (with underscore)

**Impact:** Can be confusing when searching for imports

**Recommendation:** Rename `shotlist.py` to `shot_list.py` for consistency

---

## 🎯 Files You Need to Know

### To Implement Evidence Pipeline

1. **`evidence_queue_api.py`** - Ready to use, just needs registration
2. **`evidence_queue.py`** - Core logic, already implemented
3. **`case_types.py`** - Configuration, already complete
4. **`api_app_main.py`** - Needs: import + register call

### To Use in Frontend

1. **`EvidenceUploadQueue.jsx`** - Drop-in component
2. **`EvidenceTable.jsx`** - Drop-in component
3. **`ShotList.jsx`** - Drop-in component
4. **`ClaimsMatrix.jsx`** - Drop-in component

### No Action Needed

1. **`EvidenceUpload.jsx`** - Different purpose, keep separate
2. **`table.py`** - Backend support for EvidenceTable.jsx
3. **`shotlist.py`** - Backend support for ShotList.jsx

---

## 📋 Checklist

- [ ] Understand difference between `EvidenceUpload` (generic) and `EvidenceUploadQueue` (specialized)
- [ ] Locate `api_app_main.py` as main Flask app
- [ ] Understand Flask route registration process
- [ ] Plan to add import statement to `api_app_main.py`
- [ ] Plan to add registration call to `api_app_main.py`
- [ ] Identify backend files location
- [ ] Confirm no action needed for frontend components (already implemented)

---

**Version:** 1.0 | **Status:** Reference Guide | **Last Updated:** October 20, 2025
