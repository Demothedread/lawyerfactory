# Frontend-Backend Integration Map

## Summary

**Is `ai_document_generator.py` being used by App.jsx?**  
**NO** - The `ai_document_generator.py` file is NOT directly used by the React frontend. It's a compatibility shim that's currently stubbed out and not integrated into the active API endpoints.

---

## Backend Modules Actually Used by Frontend

### ✅ Active Integration Points

The React app (`App.jsx`) communicates with the backend through the following **lawyerfactory** modules:

### 1. **Research System** (`lawyerfactory.agents.research`)

**Backend Modules**:
- `lawyerfactory.agents.research.research.ResearchBot`
- `lawyerfactory.agents.research.court_authority_helper.CourtAuthorityHelper`
- `lawyerfactory.research.tavily_integration.TavilyResearchIntegration`

**API Endpoints**:
- `POST /api/research/start` - Start research for a case
- `GET /api/research/status/<case_id>` - Get research status
- `GET /api/research/results/<case_id>` - Get research results
- `POST /api/research/execute` - Execute Tavily research (NEW)
- `POST /api/research/extract-keywords` - Extract keywords from evidence (NEW)

**Frontend Components Using**:
- `App.jsx` - Calls `startResearch()` from `apiService.js`
- `apiService.js` - `startResearch()`, `getResearchStatus()`, `getResearchResults()`

**Socket.IO Events**:
- `research_started` - Research initiated
- `research_completed` - Research finished
- `research_failed` - Research error

---

### 2. **Evidence Management** (`lawyerfactory.storage.evidence`)

**Backend Modules**:
- `lawyerfactory.storage.evidence.table.EnhancedEvidenceTable`
- `lawyerfactory.storage.evidence.table.EvidenceEntry`
- `lawyerfactory.storage.evidence.table.EvidenceSource` (PRIMARY/SECONDARY)

**API Endpoints**:
- `GET /api/evidence` - Fetch all evidence (from `evidence_flask.py`)
- `POST /api/evidence` - Create PRIMARY evidence
- `PUT /api/evidence/:id` - Update evidence
- `DELETE /api/evidence/:id` - Delete evidence

**Frontend Components Using**:
- `EvidenceTable.jsx` - Main evidence CRUD component
- `EvidenceUpload.jsx` - File upload interface
- `ShotList.jsx` - Evidence organization

**Features**:
- PRIMARY evidence (user uploads)
- SECONDARY evidence (research results)
- Filtering by evidence_source
- Real-time updates via Socket.IO

---

### 3. **Unified Storage** (`lawyerfactory.storage`)

**Backend Modules**:
- `lawyerfactory.storage.enhanced_unified_storage_api.get_enhanced_unified_storage_api()`
- Coordinates S3/Local, Evidence Table, Vector Store

**API Endpoints**:
- `POST /api/storage/documents` - Upload documents
- `GET /api/storage/documents/<object_id>` - Retrieve by ObjectID
- `GET /api/storage/cases/<case_id>/documents` - Get all case documents

**Frontend Components Using**:
- `App.jsx` - Calls `uploadDocumentsUnified()`, `getCaseDocuments()`
- `apiService.js` - `uploadDocumentsUnified()`, `getDocumentByObjectId()`, `getCaseDocuments()`
- `EvidenceUpload.jsx` - File upload to unified storage

**Integration**:
- All file uploads go through unified storage
- ObjectID tracking across tiers
- Automatic vector embedding

---

### 4. **Phase Orchestration** (`lawyerfactory.phases`)

**Backend Modules**:
- `lawyerfactory.phases.phase_orchestrator.PhaseOrchestrator`
- `lawyerfactory.phases.socket_events.set_socketio_instance()`
- Phase-specific modules:
  - `lawyerfactory.phases.phaseA01_intake.intake_processor.EnhancedIntakeProcessor`
  - `lawyerfactory.phases.phaseA01_intake.enhanced_document_categorizer.EnhancedDocumentCategorizer`
  - `lawyerfactory.phases.phaseB02_drafting.drafting_validator.DraftingValidator`

**API Endpoints**:
- `POST /api/phases/<phase_id>/start` - Start a phase
- `POST /api/intake` - Process intake form
- `POST /api/intake/process-document` - Process uploaded document

**Frontend Components Using**:
- `PhasePipeline.jsx` - Phase workflow visualization
- `LegalIntakeForm.jsx` - Intake form submission
- `WorkflowPanel.jsx` - Phase status monitoring
- `apiService.js` - `startPhase()`, `processIntake()`

**Socket.IO Events**:
- `phase_progress_update` - Real-time phase progress
- `phase_completed` - Phase finished
- `phase_failed` - Phase error

---

### 5. **Claims Matrix** (`lawyerfactory.claims`)

**Backend Modules**:
- `lawyerfactory.claims.matrix.ComprehensiveClaimsMatrixIntegration`
- `lawyerfactory.claims.research_api.ClaimsMatrixResearchAPI`

**API Endpoints**:
- `GET /api/claims/matrix/<case_id>` - Get claims matrix

**Frontend Components Using**:
- `ClaimsMatrix.jsx` - Legal claims management UI
- `App.jsx` - Stores claims matrix state
- `apiService.js` - `getClaimsMatrix()`

**Features**:
- Cause of action analysis
- Element-to-fact mapping
- Rule 12(b)(6) compliance checking

---

### 6. **Skeletal Outline** (`lawyerfactory.outline`)

**Backend Modules**:
- `lawyerfactory.outline.enhanced_generator.EnhancedSkeletalOutlineGenerator`
- `lawyerfactory.outline.generator.SkeletalOutlineGenerator`

**API Endpoints**:
- `POST /api/outline/generate` - Generate outline
- `GET /api/outline/status/<case_id>` - Get generation status
- `POST /api/outline/generate/<case_id>` - Generate skeletal outline with claims/shotlist

**Frontend Components Using**:
- `SkeletalOutlineSystem.jsx` - Outline visualization
- `App.jsx` - Outline state management
- `apiService.js` - `generateOutline()`, `getOutlineStatus()`, `generateSkeletalOutline()`

**Features**:
- FRCP-compliant complaint structure
- Claims matrix integration
- Shot list integration

---

### 7. **LLM Integration** (`lawyerfactory.lf_core.llm`)

**Backend Modules**:
- `lawyerfactory.lf_core.llm.LLMService`
- `lawyerfactory.llm_integration.provider_manager.LLMProviderManager`

**API Endpoints**:
- `GET /api/settings/llm` - Get LLM configuration
- `POST /api/settings/llm` - Update LLM settings

**Frontend Components Using**:
- `EnhancedSettingsPanel.jsx` - LLM settings UI
- `SettingsPanel.jsx` - Configuration panel
- `apiService.js` - `fetchLLMConfig()`, `updateSettings()`

**Configurable Settings**:
- AI Model: GPT-4, Claude, Groq, Gemini
- Temperature
- Max tokens
- Research mode
- Citation validation

---

## ❌ Modules NOT Used by Frontend

### `ai_document_generator.py`

**Status**: NOT INTEGRATED

**Why Not Used**:
1. It's a compatibility shim/wrapper
2. Imports `ComplaintPipeline` which may not be available
3. Returns stub results (`success=True, ready_for_filing=False`)
4. No API endpoints expose this functionality
5. Frontend doesn't call any endpoints that use this module

**Current Purpose**:
- Maintains backward compatibility for old examples/tests
- Placeholder for future document generation features
- Not part of active workflow

**Recommendation**:
- Either integrate it properly with active API endpoints
- Or remove it if not needed (marked as compatibility wrapper)

---

## Complete API Endpoint Map

### Evidence Management
```
GET    /api/evidence                      → EnhancedEvidenceTable
POST   /api/evidence                      → Create PRIMARY evidence
PUT    /api/evidence/:id                  → Update evidence
DELETE /api/evidence/:id                  → Delete evidence
```

### Research
```
POST   /api/research/start                → ResearchBot.start_research()
GET    /api/research/status/<case_id>     → ResearchBot.get_status()
GET    /api/research/results/<case_id>    → ResearchBot.get_results()
POST   /api/research/execute              → ResearchBot.research_from_evidence_keywords() [NEW]
POST   /api/research/extract-keywords     → ResearchBot.extract_keywords_from_evidence() [NEW]
```

### Storage
```
POST   /api/storage/documents             → UnifiedStorage.store_evidence()
GET    /api/storage/documents/<id>        → UnifiedStorage.get_by_object_id()
GET    /api/storage/cases/<id>/documents  → UnifiedStorage.get_case_documents()
```

### Phases
```
POST   /api/phases/<phase_id>/start       → PhaseOrchestrator.execute_phase()
POST   /api/intake                        → IntakeProcessor.process_intake()
POST   /api/intake/process-document       → IntakeProcessor.process_document()
```

### Claims & Outline
```
GET    /api/claims/matrix/<case_id>       → ClaimsMatrix.get_matrix()
POST   /api/outline/generate              → OutlineGenerator.generate()
GET    /api/outline/status/<case_id>      → OutlineGenerator.get_status()
POST   /api/outline/generate/<case_id>    → OutlineGenerator.generate_skeletal()
```

### LLM Settings
```
GET    /api/settings/llm                  → Get LLM configuration
POST   /api/settings/llm                  → Update LLM settings
```

### Drafting
```
POST   /api/drafting/validate             → DraftingValidator.validate()
```

---

## Frontend Component → Backend Module Map

| React Component | Backend Module | API Endpoint |
|----------------|----------------|--------------|
| `EvidenceTable.jsx` | `storage.evidence.table.EnhancedEvidenceTable` | `/api/evidence` |
| `EvidenceUpload.jsx` | `storage.enhanced_unified_storage_api` | `/api/storage/documents` |
| `PhasePipeline.jsx` | `phases.phase_orchestrator.PhaseOrchestrator` | `/api/phases/<id>/start` |
| `LegalIntakeForm.jsx` | `phases.phaseA01_intake.intake_processor` | `/api/intake` |
| `ClaimsMatrix.jsx` | `claims.matrix.ComprehensiveClaimsMatrixIntegration` | `/api/claims/matrix/<id>` |
| `SkeletalOutlineSystem.jsx` | `outline.enhanced_generator` | `/api/outline/generate/<id>` |
| `ShotList.jsx` | `evidence.shotlist` | (Stored in evidence table) |
| `EnhancedSettingsPanel.jsx` | `lf_core.llm.LLMService` | `/api/settings/llm` |
| `WorkflowPanel.jsx` | `phases.socket_events` | Socket.IO events |

---

## Socket.IO Real-Time Events

### Research Events
```javascript
socket.on('research_started', (data) => {
  // Research job initiated
  // data: { case_id, keywords, evidence_id }
});

socket.on('research_completed', (data) => {
  // Research finished, SECONDARY evidence created
  // data: { case_id, secondary_evidence_ids, confidence_score }
});

socket.on('research_failed', (data) => {
  // Research error
  // data: { case_id, error }
});
```

### Phase Events
```javascript
socket.on('phase_progress_update', (data) => {
  // Phase execution progress
  // data: { phase, status, progress, message }
});

socket.on('phase_completed', (data) => {
  // Phase finished
  // data: { phase, deliverables, status }
});

socket.on('phase_failed', (data) => {
  // Phase error
  // data: { phase, error }
});
```

---

## Data Flow Architecture

```
React Frontend (App.jsx)
    ↓
apiService.js (REST API + Socket.IO)
    ↓
Flask Server (apps/api/server.py)
    ↓
┌─────────────────────────────────────────┐
│  LawyerFactory Backend Modules          │
├─────────────────────────────────────────┤
│  1. Research Bot (Tavily integration)   │
│  2. Evidence Table (PRIMARY/SECONDARY)  │
│  3. Unified Storage (S3/Vector/Local)   │
│  4. Phase Orchestrator (7 phases)       │
│  5. Claims Matrix (Legal analysis)      │
│  6. Outline Generator (FRCP compliant)  │
│  7. LLM Service (Multi-provider)        │
└─────────────────────────────────────────┘
    ↓
Storage Tiers:
- S3/Local Raw Storage (ObjectID)
- Evidence Table (Metadata)
- Vector Store (Embeddings)
```

---

## Key Findings

### ✅ What IS Being Used

1. **Research System** - Tavily integration, CourtListener, keyword extraction
2. **Evidence Management** - PRIMARY/SECONDARY classification, CRUD operations
3. **Unified Storage** - Object/Vector/Local tier coordination
4. **Phase Orchestration** - 7-phase workflow pipeline
5. **Claims Matrix** - Legal analysis and validation
6. **Skeletal Outline** - FRCP-compliant document structure
7. **LLM Integration** - Multi-provider support (OpenAI, Anthropic, Groq)

### ❌ What IS NOT Being Used

1. **`ai_document_generator.py`** - Compatibility shim, not integrated
2. **`ComplaintPipeline`** - Referenced in ai_document_generator but not exposed
3. **Most of `compose/` module** - Not connected to API endpoints

### 🔄 What COULD Be Integrated

If you want to integrate `ai_document_generator.py`:

1. **Create API Endpoint**:
   ```python
   @app.route("/api/documents/generate", methods=["POST"])
   def generate_document():
       from lawyerfactory.document_generator.ai_document_generator import AIDocumentGenerator
       generator = AIDocumentGenerator()
       result = generator.generate_documents(request.json)
       return jsonify(result.__dict__)
   ```

2. **Add to apiService.js**:
   ```javascript
   export const generateDocument = async (caseData, options = {}) => {
     const response = await apiClient.post("/api/documents/generate", {
       case_data: caseData,
       options: options
     });
     return response.data;
   };
   ```

3. **Add React Component**:
   ```jsx
   const handleGenerateDocument = async () => {
     const result = await generateDocument(caseData, settings);
     // Handle result
   };
   ```

---

## Recommendations

1. **Keep Current Integration**: The active modules (Research, Evidence, Storage, Phases, Claims, Outline, LLM) are well-integrated and working.

2. **Document Generation**: If you need `ai_document_generator.py`, implement it properly with real `ComplaintPipeline` integration, not just a stub.

3. **Cleanup**: Consider removing unused compatibility shims to reduce confusion.

4. **Focus on Testing**: All active integration points are ready for end-to-end testing (Task 9 in todo list).

---

## Summary Answer

**Q: Is `ai_document_generator.py` being used by App.jsx?**  
**A: NO** - It's a compatibility wrapper that's not connected to any active API endpoints.

**Q: What lawyerfactory functionalities are being utilized in the frontend?**  
**A: Seven major systems:**
1. Research Bot (Tavily + CourtListener)
2. Evidence Table (PRIMARY/SECONDARY)
3. Unified Storage (3-tier coordination)
4. Phase Orchestrator (7 phases)
5. Claims Matrix (Legal analysis)
6. Skeletal Outline Generator (FRCP)
7. LLM Service (Multi-provider)

All integrated through REST API + Socket.IO real-time events.
