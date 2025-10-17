# Phase A03 - Outline Generation Deliverables

## Overview

Phase A03 (Outline) generates three critical deliverables that flow into the skeletal outline and final complaint:

1. **Shotlist** - Chronological timeline of all relevant facts from evidence
2. **Claims Matrix** - Legal analysis of potential causes of action with elements
3. **Skeletal Outline** - FRCP-compliant document structure generated from shotlist + claims matrix

**Integration Pattern**: Evidence → Shotlist (Timeline) → Claims Matrix (Legal Analysis) → Skeletal Outline (Document Structure)

---

## Architecture

### Workflow Sequence

```
Phase A03 Start
    ↓
Step 1: Generate Shotlist
    - Fetch all PRIMARY + SECONDARY evidence
    - Extract facts with timestamps, entities, citations
    - Sort chronologically
    - Export to CSV + JSON
    ↓
Step 2: Generate Claims Matrix
    - Analyze evidence for legal claims
    - Use ComprehensiveClaimsMatrixIntegration
    - Detect causes of action (negligence, breach of contract, etc.)
    - Map elements to facts
    - Calculate confidence scores
    - Export to JSON
    ↓
Step 3: Generate Skeletal Outline
    - Use shotlist for Statement of Facts section
    - Use claims matrix for Causes of Action sections
    - Generate FRCP-compliant structure
    - Export to JSON
    ↓
Phase A03 Complete → Deliverables Available for Download
```

---

## Backend Implementation

### API Endpoints

#### 1. Generate Shotlist

```http
POST /api/phaseA03/shotlist/<case_id>
```

**Description**: Extracts chronological facts from all evidence (PRIMARY user uploads + SECONDARY research results)

**Request**: None required (uses case_id from URL)

**Response**:
```json
{
  "success": true,
  "case_id": "case_123",
  "shotlist": [
    {
      "fact_id": "fact_case_123_1",
      "source_id": "evidence_object_id_456",
      "timestamp": "2024-01-15",
      "summary": "Defendant ran red light at intersection...",
      "entities": ["Defendant John Doe", "Intersection of Main & 5th"],
      "citations": ["Police Report #12345"]
    }
  ],
  "fact_count": 25,
  "csv_path": "./workflow_storage/cases/case_123/deliverables/shotlist.csv",
  "download_url": "/api/deliverables/case_123/shotlist.csv",
  "generated_at": 1704672000
}
```

**Socket.IO Event**:
```javascript
socketio.emit("shotlist_generated", {
  case_id: "case_123",
  fact_count: 25,
  csv_path: "...",
  timestamp: 1704672000
});
```

---

#### 2. Generate Claims Matrix

```http
POST /api/phaseA03/claims-matrix/<case_id>
```

**Description**: Analyzes evidence to detect potential legal claims and map elements to facts

**Request Body**:
```json
{
  "jurisdiction": "ca_state",
  "cause_of_action": "negligence"
}
```

**Response**:
```json
{
  "success": true,
  "case_id": "case_123",
  "session_id": "analysis_20250109_143000",
  "claims_matrix": {
    "header": {
      "analysis_id": "attorney_analysis_...",
      "cause_of_action": "Negligence",
      "jurisdiction": "California State Court",
      "generated_date": "January 9, 2025",
      "attorney_ready": true
    },
    "executive_summary": {
      "case_strength": {
        "overall_strength": "Strong",
        "confidence_score": 0.85,
        "strong_elements": ["duty", "breach"],
        "weak_elements": ["damages"],
        "critical_gaps": ["Strengthen evidence for damages"]
      }
    },
    "legal_definition": {
      "primary_definition": "Negligence is the failure to exercise...",
      "authority_citations": ["Rowland v. Christian (1968) 69 Cal.2d 108"],
      "jury_instructions": ["CACI No. 400"]
    },
    "element_analysis": {
      "duty": {
        "breakdown": {...},
        "provable_questions": [...],
        "decision_outcome": {...}
      },
      "breach": {...},
      "causation": {...},
      "damages": {...}
    },
    "practice_guidance": [
      "Prepare Rowland factor analysis for duty questions",
      "Retain medical expert early for complex causation"
    ],
    "discovery_recommendations": [
      "Request incident reports and documentation",
      "Depose defendant regarding standard operating procedures"
    ]
  },
  "json_path": "./workflow_storage/cases/case_123/deliverables/claims_matrix.json",
  "download_url": "/api/deliverables/case_123/claims_matrix.json"
}
```

**Socket.IO Event**:
```javascript
socketio.emit("claims_matrix_generated", {
  case_id: "case_123",
  session_id: "analysis_20250109_143000",
  claims_count: 4,
  json_path: "...",
  timestamp: 1704672100
});
```

---

#### 3. Generate All Phase A03 Deliverables (Orchestrator)

```http
POST /api/phaseA03/generate/<case_id>
```

**Description**: Orchestrates generation of all three deliverables in sequence

**Request Body**:
```json
{
  "jurisdiction": "ca_state",
  "cause_of_action": "negligence"
}
```

**Response**:
```json
{
  "success": true,
  "case_id": "case_123",
  "deliverables": {
    "shotlist": {
      "data": [...],
      "fact_count": 25,
      "download_url": "/api/deliverables/case_123/shotlist.csv"
    },
    "claims_matrix": {
      "data": {...},
      "download_url": "/api/deliverables/case_123/claims_matrix.json"
    },
    "skeletal_outline": {
      "data": {...},
      "section_count": 12,
      "download_url": "/api/deliverables/case_123/skeletal_outline.json"
    }
  },
  "generated_at": 1704672300
}
```

**Socket.IO Events** (emitted during orchestration):
```javascript
// Progress updates
socketio.emit("phase_progress_update", {
  phase: "phaseA03_outline",
  case_id: "case_123",
  status: "running",
  progress: 25,
  message: "Generating chronological shotlist timeline..."
});

socketio.emit("phase_progress_update", {
  phase: "phaseA03_outline",
  case_id: "case_123",
  status: "running",
  progress: 50,
  message: "Analyzing evidence for legal claims..."
});

socketio.emit("phase_progress_update", {
  phase: "phaseA03_outline",
  case_id: "case_123",
  status: "running",
  progress: 75,
  message: "Generating skeletal outline from timeline and claims..."
});

// Completion
socketio.emit("skeletal_outline_generated", {
  case_id: "case_123",
  json_path: "...",
  section_count: 12,
  timestamp: 1704672300
});

socketio.emit("phase_progress_update", {
  phase: "phaseA03_outline",
  case_id: "case_123",
  status: "completed",
  progress: 100,
  message: "Phase A03 deliverables generated successfully"
});
```

---

#### 4. Download Deliverable

```http
GET /api/deliverables/<case_id>/<deliverable_type>
```

**Description**: Download generated deliverable files

**Supported Types**:
- `shotlist.csv` - Chronological facts timeline (CSV format)
- `claims_matrix.json` - Legal analysis (JSON format)
- `skeletal_outline.json` - Document structure (JSON format)

**Example**:
```http
GET /api/deliverables/case_123/shotlist.csv
```

**Response**: File download with proper Content-Disposition headers

---

## Frontend Implementation

### API Service Functions (`apiService.js`)

#### 1. Generate Shotlist
```javascript
import { generateShotlist } from '../../services/apiService';

const result = await generateShotlist(caseId);
// Returns: { success, shotlist, fact_count, download_url }
```

#### 2. Generate Claims Matrix
```javascript
import { generateClaimsMatrix } from '../../services/apiService';

const result = await generateClaimsMatrix(caseId, {
  jurisdiction: "ca_state",
  causeOfAction: "negligence"
});
// Returns: { success, claims_matrix, download_url }
```

#### 3. Generate All Deliverables
```javascript
import { generatePhaseA03Deliverables } from '../../services/apiService';

const result = await generatePhaseA03Deliverables(caseId, {
  jurisdiction: "ca_state",
  causeOfAction: "negligence"
});
// Returns: { success, deliverables: { shotlist, claims_matrix, skeletal_outline } }
```

#### 4. Download Deliverable
```javascript
import { downloadDeliverable } from '../../services/apiService';

await downloadDeliverable(caseId, "shotlist.csv");
// Triggers browser download
```

#### 5. Check Deliverable Status
```javascript
import { getPhaseA03Deliverables } from '../../services/apiService';

const deliverables = await getPhaseA03Deliverables(caseId);
// Returns:
// {
//   shotlist: { available: true, url: "...", filename: "shotlist.csv" },
//   claimsMatrix: { available: true, url: "...", filename: "claims_matrix.json" },
//   skeletalOutline: { available: true, url: "...", filename: "skeletal_outline.json" }
// }
```

---

### React Component Integration

#### NeonPhaseCard.jsx - Deliverable Display

The `NeonPhaseCard` component automatically displays Phase A03 deliverables when the phase is completed:

**Features**:
- Checks deliverable availability when phase status is "completed"
- Shows three deliverables with icons:
  - 📊 Shotlist Timeline (Timeline icon)
  - 📋 Claims Matrix (Assignment icon)
  - 📄 Skeletal Outline (Description icon)
- Download buttons for each available deliverable
- Neon-themed Soviet Industrial styling

**Props Required**:
```jsx
<NeonPhaseCard
  phase={{ id: 'phaseA03_outline', name: 'Phase A03 - Outline' }}
  phaseState={{ status: 'completed', progress: 100 }}
  caseId="case_123"  // CRITICAL: Required for deliverable checking
  onStart={() => {}}
  onViewDetails={() => {}}
/>
```

**Automatic Behavior**:
1. When `phase.id === 'phaseA03_outline'` and `phaseState.status === 'completed'`:
   - Calls `getPhaseA03Deliverables(caseId)`
   - Updates deliverable status state
   - Displays deliverable cards with download buttons

2. User clicks download button:
   - Calls `downloadDeliverable(caseId, deliverableType)`
   - Browser automatically downloads file

---

#### SkeletalOutlineSystem.jsx - Outline Visualization

**Current State**: Component receives `claimsMatrix` and `shotList` as props

**Future Integration** (TODO Task 7):
- Fetch shotlist and claims matrix from backend API
- Add real-time Socket.IO updates for outline generation progress
- Display deliverables inline

```jsx
// Future implementation
useEffect(() => {
  const socket = getSocket();
  
  socket.on('shotlist_generated', (data) => {
    console.log('Shotlist generated:', data);
    // Fetch and display shotlist
  });
  
  socket.on('claims_matrix_generated', (data) => {
    console.log('Claims matrix generated:', data);
    // Fetch and display claims matrix
  });
  
  socket.on('skeletal_outline_generated', (data) => {
    console.log('Skeletal outline generated:', data);
    // Fetch and display outline
  });
}, [caseId]);
```

---

## File Storage Structure

```
workflow_storage/
└── cases/
    └── case_123/
        └── deliverables/
            ├── shotlist.csv              # Chronological facts timeline
            ├── claims_matrix.json        # Legal analysis report
            └── skeletal_outline.json     # Document structure
```

---

## Data Formats

### Shotlist CSV Format

```csv
fact_id,source_id,timestamp,summary,entities,citations
fact_case_123_1,evidence_obj_456,2024-01-15,"Defendant ran red light...","Defendant John Doe|Intersection Main & 5th","Police Report #12345"
fact_case_123_2,evidence_obj_457,2024-01-15,"Plaintiff vehicle struck...","Plaintiff Jane Smith|Vehicle Toyota Camry",""
```

### Claims Matrix JSON Structure

```json
{
  "header": {
    "analysis_id": "attorney_analysis_...",
    "cause_of_action": "Negligence",
    "jurisdiction": "California State Court",
    "generated_date": "January 9, 2025"
  },
  "executive_summary": {
    "case_strength": {
      "overall_strength": "Strong",
      "confidence_score": 0.85
    }
  },
  "element_analysis": {
    "duty": { "breakdown": {...}, "provable_questions": [...] },
    "breach": {...},
    "causation": {...},
    "damages": {...}
  },
  "practice_guidance": [...],
  "discovery_recommendations": [...]
}
```

### Skeletal Outline JSON Structure

```json
{
  "id": "outline_case_123_...",
  "caseId": "case_123",
  "sections": [
    {
      "id": "caption",
      "title": "Case Caption",
      "status": "pending",
      "required": true,
      "estimatedWords": 50
    },
    {
      "id": "introduction",
      "title": "Introduction",
      "status": "pending",
      "required": true,
      "estimatedWords": 200
    },
    {
      "id": "cause_0",
      "title": "Cause of Action: Negligence",
      "status": "pending",
      "required": true,
      "estimatedWords": 300,
      "claimData": { /* Claims matrix element data */ }
    }
  ],
  "totalEstimatedWords": 1500,
  "status": "draft",
  "rule12b6ComplianceScore": 85
}
```

---

## Testing & Validation

### Manual Testing Checklist

1. **Upload Evidence** (Phase A01)
   - Upload PRIMARY evidence documents
   - Verify vectorization completes
   - Check evidence table shows entries

2. **Run Research** (Phase A02 - Optional)
   - Trigger research to generate SECONDARY evidence
   - Verify SECONDARY evidence appears in table

3. **Start Phase A03**
   ```javascript
   await generatePhaseA03Deliverables(caseId, {
     jurisdiction: "ca_state",
     causeOfAction: "negligence"
   });
   ```

4. **Verify Shotlist Generation**
   - Check Socket.IO event: `shotlist_generated`
   - Verify CSV file exists: `workflow_storage/cases/<case_id>/deliverables/shotlist.csv`
   - Check fact count matches evidence count
   - Verify chronological ordering

5. **Verify Claims Matrix Generation**
   - Check Socket.IO event: `claims_matrix_generated`
   - Verify JSON file exists: `workflow_storage/cases/<case_id>/deliverables/claims_matrix.json`
   - Check cause of action matches request
   - Verify element breakdowns exist
   - Check practice guidance populated

6. **Verify Skeletal Outline Generation**
   - Check Socket.IO event: `skeletal_outline_generated`
   - Verify JSON file exists: `workflow_storage/cases/<case_id>/deliverables/skeletal_outline.json`
   - Check sections include claims from matrix
   - Verify FRCP compliance structure

7. **Test Downloads**
   - Click download button for shotlist.csv
   - Click download button for claims_matrix.json
   - Click download button for skeletal_outline.json
   - Verify files download correctly
   - Open files and validate content

8. **Verify UI Display**
   - Check NeonPhaseCard shows "DELIVERABLES" section
   - Verify three deliverable cards visible
   - Check download buttons are enabled
   - Verify neon-themed styling applied

---

## Integration with Existing Systems

### Evidence Table Integration

- **PRIMARY Evidence**: User-uploaded documents (Phase A01)
- **SECONDARY Evidence**: Research results (Phase A02)
- **Shotlist**: Extracts facts from BOTH evidence types

### Claims Matrix Integration

- Uses `ComprehensiveClaimsMatrixIntegration` from `src/lawyerfactory/phases/phaseA03_outline/claims_matrix.py`
- Requires `EnhancedKnowledgeGraph` for full functionality
- Falls back to mock generation if KG unavailable

### Unified Storage Integration

- All evidence fetched via `unified_storage.get_case_documents(case_id)`
- Deliverables stored in case-specific folders
- ObjectID tracking maintained across tiers

---

## Error Handling

### Common Errors & Solutions

**Error**: `No evidence found for this case`
- **Cause**: Phase A03 started before evidence uploaded
- **Solution**: Upload evidence in Phase A01 first

**Error**: `Phase A03 shotlist component not available`
- **Cause**: `shotlist.py` import failed
- **Solution**: Check Python path, verify `lawyerfactory.phases.phaseA03_outline.shotlist.shotlist` exists

**Error**: `Claims matrix generation failed`
- **Cause**: `ComprehensiveClaimsMatrixIntegration` import or initialization failed
- **Solution**: Check if `EnhancedKnowledgeGraph` available, falls back to mock if not

**Error**: `Deliverable not found`
- **Cause**: File doesn't exist at expected path
- **Solution**: Re-run Phase A03 generation

---

## Future Enhancements

1. **LLM-Enhanced Shotlist** (TODO)
   - Use LLM to generate fact summaries
   - Extract entities and dates automatically
   - Generate citations from evidence

2. **Interactive Claims Matrix** (TODO)
   - Real-time element selection
   - Fact-to-element drag-and-drop mapping
   - Confidence score adjustment

3. **Live Outline Editing** (TODO)
   - Edit skeletal outline sections in React
   - Save edits back to backend
   - Real-time collaboration

4. **PDF Export** (TODO)
   - Generate PDF versions of deliverables
   - Add Bluebook citations
   - Format for court filing

---

## Summary

Phase A03 deliverables provide the foundation for long-form legal document generation:

- **Shotlist**: Chronological fact timeline ensures Statement of Facts is complete
- **Claims Matrix**: Legal analysis ensures each cause of action has proper element mapping
- **Skeletal Outline**: FRCP-compliant structure ensures complaint meets Rule 12(b)(6) standards

All three deliverables are:
- ✅ Generated automatically in sequence
- ✅ Stored as downloadable files (CSV/JSON)
- ✅ Viewable in React UI with Soviet Industrial neon theme
- ✅ Integrated with unified storage and evidence systems
- ✅ Real-time progress updates via Socket.IO

**Next Steps**: Complete SkeletalOutlineSystem.jsx integration (Task 7) and run end-to-end testing (Task 9).
