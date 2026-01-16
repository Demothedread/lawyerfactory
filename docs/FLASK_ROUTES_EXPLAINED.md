# Understanding Flask Route Registration in LawyerFactory

**Document Version:** 1.0  
**Date:** October 20, 2025  
**Status:** Reference Guide

---

## 🎯 What Does "Register Flask Routes" Mean?

### Definition
"Registering Flask routes" means **connecting HTTP endpoints (URLs) to Python functions** in your Flask application so that when a frontend requests a URL, the backend knows which Python code to run.

### The Basic Process

```python
# Step 1: Create a Blueprint (modular collection of routes)
from flask import Blueprint

evidence_queue_bp = Blueprint('evidence_queue', __name__, url_prefix='/api/evidence/queue')

# Step 2: Define route handlers (functions that handle HTTP requests)
@evidence_queue_bp.route('/status/<case_id>', methods=['GET'])
def get_queue_status_endpoint(case_id: str):
    # This function runs when frontend calls GET /api/evidence/queue/status/CASE-001
    return jsonify(status), 200

# Step 3: Register the Blueprint with Flask app (CONNECT EVERYTHING)
def register_evidence_queue_routes(app):
    app.register_blueprint(evidence_queue_bp)
    logger.info("Registered evidence queue API routes")
```

### What Happens Behind the Scenes

```
Frontend                           Backend
─────────────────────────────────────────────
GET /api/evidence/queue/status/CASE-001
        │
        ├──────────> Flask receives request
                     │
                     ├──> Looks up route in registry
                     │
                     ├──> Finds Blueprint: 'evidence_queue'
                     │    URL pattern: '/api/evidence/queue'
                     │    Handler: get_queue_status_endpoint
                     │
                     ├──> Extracts case_id = "CASE-001"
                     │
                     ├──> Calls get_queue_status_endpoint("CASE-001")
                     │
                     ├──> Function runs
                     │    - Queries database
                     │    - Builds response
                     │
                     └──> Returns JSON response
        <──────────── Response sent back to frontend
```

---

## 📁 Backend Files Location in LawyerFactory

### Primary Backend Files for Evidence Pipeline

```
/Users/jreback/Projects/LawyerFactory/src/
├── lawyerfactory/
│   ├── api/
│   │   ├── evidence_queue_api.py          ← ⭐ API ROUTES (What you need to register)
│   │   ├── shot_list.py
│   │   └── timeline.py
│   │
│   ├── storage/
│   │   └── core/
│   │       └── evidence_queue.py          ← ⭐ QUEUE LOGIC (Processing happens here)
│   │
│   └── config/
│       └── case_types.py                  ← ⭐ CASE TYPE ENUMS
│
└── phaseB01_review/ui/
    └── api_app_main.py                    ← ⭐ MAIN FLASK APP (Where to register)
```

### What Each File Does

| File | Location | Purpose |
|------|----------|---------|
| `evidence_queue_api.py` | `src/lawyerfactory/api/` | Defines REST endpoints for evidence queue |
| `evidence_queue.py` | `src/lawyerfactory/storage/core/` | Core queue logic, classification, processing |
| `case_types.py` | `src/lawyerfactory/config/` | Case type enums and classification functions |
| `api_app_main.py` | `src/lawyerfactory/phases/phaseB01_review/ui/` | **Main Flask app where you register blueprints** |

---

## 🔌 How to Register Routes (Step-by-Step)

### Current State: Routes are DEFINED but NOT REGISTERED

The file `evidence_queue_api.py` has the **function** to register:

```python
def register_evidence_queue_routes(app):
    """Register evidence queue API blueprint with Flask app"""
    app.register_blueprint(evidence_queue_bp)
    logger.info("Registered evidence queue API routes")
```

But this function is **never called** in the Flask app.

### Step 1: Find the Main Flask App

Currently: **`/Users/jreback/Projects/LawyerFactory/src/lawyerfactory/phases/phaseB01_review/ui/api_app_main.py`**

This is where the Flask app is created:

```python
# Line 160 approximately
app = Flask(__name__)
```

### Step 2: Import the Registration Function

At the top of `api_app_main.py`, add:

```python
from lawyerfactory.api.evidence_queue_api import register_evidence_queue_routes
```

### Step 3: Call the Registration Function

After the Flask app is created and configured, call:

```python
# Example location in api_app_main.py (after app = Flask(__name__))
register_evidence_queue_routes(app)
```

### Step 4: Verify It Worked

```bash
# Check the Flask app logs for:
# "Registered evidence queue API routes"
```

---

## 🛣️ Available Routes After Registration

Once registered, these endpoints become available:

### Evidence Queue Endpoints

```
GET  /api/evidence/queue/status/<case_id>
     ↳ Get current processing status for a case

POST /api/evidence/queue/upload/<case_id>
     ↳ Upload and queue evidence files for processing
     ↳ Body: FormData { files, case_type }

POST /api/evidence/queue/start/<case_id>
     ↳ Start processing the queue

POST /api/evidence/queue/cancel/<case_id>/<item_id>
     ↳ Cancel processing a specific item

GET  /api/evidence/queue/filter/<case_id>
     ↳ Get evidence filtered by class/type
     ↳ Query: ?evidence_class=primary&evidence_type=email

GET  /api/evidence/queue/stats/<case_id>
     ↳ Get statistics about queue and classifications
```

### Example Usage from Frontend

```javascript
// After routes are registered, frontend can call:
const response = await fetch('/api/evidence/queue/status/CASE-001');
const data = await response.json();
// Returns: { queue_items: [...], total: 10, completed: 3, processing: 2, queued: 5 }
```

---

## 🔍 What's a Blueprint?

A **Blueprint** in Flask is a modular way to organize routes. Think of it like a "route package":

```python
# Instead of registering 100 routes directly on app:
app.route('/api/endpoint1')
app.route('/api/endpoint2')
app.route('/api/endpoint3')
# ... 97 more ...

# You group them by feature:
evidence_queue_bp = Blueprint('evidence_queue', __name__, url_prefix='/api/evidence/queue')

@evidence_queue_bp.route('/status/<case_id>')  # Full URL: /api/evidence/queue/status/<case_id>
def get_status(...): ...

@evidence_queue_bp.route('/upload/<case_id>')  # Full URL: /api/evidence/queue/upload/<case_id>
def upload(...): ...

# Then register once:
app.register_blueprint(evidence_queue_bp)
```

**Benefits:**
- ✅ Cleaner code organization
- ✅ Easier to maintain
- ✅ Can enable/disable entire feature sets
- ✅ Reusable across projects

---

## 🎲 Duplicate Files Analysis

### Evidence-Related Components

There are **TWO similar evidence upload components** for different purposes:

#### 1. `EvidenceUpload.jsx` (Generic Storage Upload)
**Location:** `/Users/jreback/Projects/LawyerFactory/apps/ui/react-app/src/components/ui/EvidenceUpload.jsx`

**Purpose:** Generic file upload to unified storage system
```
- Endpoint: /api/storage/documents
- Features:
  - Drag-and-drop upload
  - File validation
  - Metadata attachment
  - Progress tracking
  - Returns: object_id, evidence_id, s3_url
- Used in: Any phase needing file uploads
```

**Capabilities:**
```jsx
<EvidenceUpload
  apiEndpoint="/api/storage/documents"
  maxFileSize={10 * 1024 * 1024}
  acceptedTypes={['.pdf', '.doc', '.docx']}
  onUploadComplete={handleUploadComplete}
/>
```

#### 2. `EvidenceUploadQueue.jsx` (Specialized Evidence Classification Queue)
**Location:** `/Users/jreback/Projects/LawyerFactory/apps/ui/react-app/src/components/ui/EvidenceUploadQueue.jsx`

**Purpose:** Upload evidence with automatic classification (primary/secondary, type detection)
```
- Endpoint: /api/evidence/queue/upload/<case_id>
- Features:
  - Batch upload
  - Real-time processing queue display
  - Automatic classification badges
  - Confidence scores
  - Hierarchical grouping (primary vs secondary)
  - Error handling per file
- Used in: Evidence intake pipeline (LegalIntakeForm)
```

**Capabilities:**
```jsx
<EvidenceUploadQueue
  caseId="CASE-001"
  pollingInterval={2000}
  onQueueStatusUpdate={handleStatusUpdate}
/>
```

### Why Two Components?

| Feature | EvidenceUpload | EvidenceUploadQueue |
|---------|---|---|
| **Purpose** | Generic storage | Evidence classification |
| **Processing** | None (just stores) | Classifies + processes |
| **Queue Display** | Simple list | Real-time animated queue |
| **Classification** | No | Yes (Primary/Secondary + Type) |
| **Best For** | General file uploads | Legal case evidence |
| **API Used** | `/api/storage/documents` | `/api/evidence/queue/upload` |

### Python Duplicates

#### 1. `shot_list.py` (Evidence Shot Extraction)
**Location:** `src/lawyerfactory/evidence/shotlist.py`

**Purpose:** Extract "shots" (key facts) from evidence for drafting

#### 2. `shot_list.py` (API Layer)
**Location:** `src/lawyerfactory/api/shot_list.py`

**Relationship:** API layer probably wraps the core logic

---

## 📊 Data Flow with Registered Routes

### Upload → Classification → Usage

```
1️⃣  USER UPLOADS (Frontend)
    ↓
    LegalIntakeForm.jsx
    └─> determinesCaseType()
    └─> renders EvidenceUploadQueue
    └─> user selects files
    └─> POST /api/evidence/queue/upload/CASE-001
        ├─ files: [file1, file2, ...]
        └─ case_type: "autonomous_vehicle"

2️⃣  BACKEND RECEIVES & QUEUES (Flask Route Registered)
    ↓
    @evidence_queue_bp.route('/upload/<case_id>')
    └─> upload_evidence(case_id)
    └─> get_or_create_queue(case_id, case_type)
    └─> Save files to temp storage
    └─> Add to EvidenceProcessingQueue
    └─> Returns 202 Accepted + queue_items

3️⃣  ASYNC PROCESSING
    ↓
    _process_queue_async(queue, case_id)
    └─> Max 3 concurrent files
    └─> For each file:
        ├─ Read content
        ├─ EvidenceClassifier.classify()
        │  └─ Returns: evidence_class (primary/secondary)
        │  └─ Returns: evidence_type (email, contract, etc.)
        │  └─ Returns: confidence_score
        ├─ Extract metadata
        ├─ Create summary (LLM)
        └─ Vectorize for search

4️⃣  FRONTEND POLLS FOR STATUS
    ↓
    GET /api/evidence/queue/status/CASE-001
    └─> Returns updated queue items with:
        ├─ status: queued|processing|complete|error
        ├─ progress: 0-100%
        ├─ evidence_class: primary|secondary
        ├─ evidence_type: email|contract|case_law|etc
        └─ classification_confidence: 0-1

5️⃣  FRONTEND DISPLAYS IN COMPONENTS
    ↓
    EvidenceTable.jsx
    ├─ GET /api/evidence/queue/filter/CASE-001?evidence_class=primary
    ├─ Groups by evidence_type
    └─ Displays hierarchical view

    ShotList.jsx
    ├─ GET /api/evidence/queue/filter/CASE-001?evidence_class=primary
    └─ Extracts facts for drafting

    ClaimsMatrix.jsx
    ├─ GET /api/evidence/queue/filter/CASE-001?evidence_class=primary
    ├─ GET /api/evidence/queue/filter/CASE-001?evidence_class=secondary
    └─ Maps to claim elements
```

---

## ⚠️ Important: Missing Registration in Current Codebase

### Current Problem

The `evidence_queue_api.py` file **exists and is complete**, but the `register_evidence_queue_routes()` function is **never called** in `api_app_main.py`.

### Evidence

**File:** `src/lawyerfactory/api/evidence_queue_api.py` (Lines 256-259)
```python
def register_evidence_queue_routes(app):
    """Register evidence queue API blueprint with Flask app"""
    app.register_blueprint(evidence_queue_bp)
    logger.info("Registered evidence queue API routes")
```

**Status:** ❌ Not called anywhere in the codebase

### Solution

Add to `api_app_main.py` (after Flask app creation):

```python
from lawyerfactory.api.evidence_queue_api import register_evidence_queue_routes

# ... after app = Flask(__name__) ...
register_evidence_queue_routes(app)
```

---

## 🧪 Testing Route Registration

### Method 1: Check Flask Routes

```bash
# In Python
from lawyerfactory.phases.phaseB01_review.ui.api_app_main import app

# List all registered routes
for rule in app.url_map.iter_rules():
    if 'evidence' in rule.rule:
        print(rule.rule, rule.methods)
```

### Method 2: Check Logs

```bash
# Start Flask app and look for log message:
# "Registered evidence queue API routes"
```

### Method 3: Make Test Request

```bash
curl http://localhost:5000/api/evidence/queue/status/TEST-001
# Should return: {"error": "Queue not found for case"} or queue data
# NOT: 404 Page Not Found (which means route isn't registered)
```

---

## 📚 Summary

| Concept | Explanation |
|---------|-------------|
| **Route Registration** | Connecting HTTP URLs to Python functions in Flask |
| **Blueprint** | Modular collection of routes grouped by feature |
| **Why Needed** | Frontend can't call backend code without registered URLs |
| **Evidence Queue Endpoints** | 6 routes for upload, status, filtering, and statistics |
| **Current Status** | Routes defined but NOT registered in main Flask app |
| **Fix Required** | Import `register_evidence_queue_routes` and call in `api_app_main.py` |
| **Two Upload Components** | `EvidenceUpload` (generic) vs `EvidenceUploadQueue` (classification) |
| **Backend Files** | `evidence_queue_api.py`, `evidence_queue.py`, `case_types.py` |

---

## 🚀 Next Steps

1. ✅ Locate main Flask app: `api_app_main.py`
2. ✅ Import: `from lawyerfactory.api.evidence_queue_api import register_evidence_queue_routes`
3. ✅ Call: `register_evidence_queue_routes(app)` after app creation
4. ✅ Restart Flask server
5. ✅ Test with: `curl http://localhost:5000/api/evidence/queue/status/TEST-001`
6. ✅ Frontend components can now call the API

---

**Version:** 1.0 | **Status:** Ready for Implementation | **Last Updated:** October 20, 2025
