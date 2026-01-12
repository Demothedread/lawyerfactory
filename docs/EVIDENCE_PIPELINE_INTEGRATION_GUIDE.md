# Evidence Pipeline - Integration Guide for Existing Components

**Status:** Ready for Integration  
**Date:** October 19, 2025  

---

## 🔗 How to Integrate with Existing Components

### 1. **LegalIntakeForm.jsx Integration**

The intake form needs to:
- Determine case type from user input
- Pass case_type to evidence upload
- Trigger EvidenceUploadQueue after form submission

**Current File:** `apps/ui/react-app/src/components/terminal/LegalIntakeForm.jsx`

**Integration Points:**

```jsx
import EvidenceUploadQueue from '../ui/EvidenceUploadQueue';

// Inside component
const [showEvidenceQueue, setShowEvidenceQueue] = useState(false);
const [caseType, setCaseType] = useState(null);

// In form submission
const handleFormSubmit = (formData) => {
  // Determine case type from form
  const determinedCaseType = determineCaseType(formData);
  setCaseType(determinedCaseType);
  
  // Store form data in backend
  await submitIntakeForm(formData);
  
  // Show evidence queue
  setShowEvidenceQueue(true);
};

// In render
{showEvidenceQueue && (
  <EvidenceUploadQueue
    caseId={caseId}
    onQueueStatusUpdate={(status) => {
      console.log(`Processing: ${status.processing} items`);
    }}
    onItemComplete={(item) => {
      console.log(`Completed: ${item.filename}`);
      // Trigger downstream updates if needed
    }}
  />
)}
```

**Determine Case Type Function:**
```jsx
const determineCaseType = (formData) => {
  // Map form data to case type
  if (formData.otherPartyName?.includes('Tesla') || 
      formData.claimDescription?.includes('autonomous') ||
      formData.claimDescription?.includes('self-driving')) {
    return 'autonomous_vehicle';
  }
  
  if (formData.claimDescription?.includes('product')) {
    return 'product_liability';
  }
  
  if (formData.eventType === 'vehicle_accident') {
    return 'auto_accident';
  }
  
  if (formData.agreementType === 'contract') {
    return 'contract_breach';
  }
  
  // Default
  return 'negligence';
};
```

---

### 2. **EvidenceTable.jsx Integration**

The evidence table needs to:
- Display hierarchical groups (Primary | Secondary)
- Sub-group by evidence type
- Filter and sort by classification

**Current File:** `apps/ui/react-app/src/components/ui/EvidenceTable.jsx`

**Integration Points:**

```jsx
// Add evidence class and type filters
const [evidenceClassFilter, setEvidenceClassFilter] = useState(null);
const [evidenceTypeFilter, setEvidenceTypeFilter] = useState(null);

// Fetch evidence with classification
const fetchClassifiedEvidence = async () => {
  try {
    let url = `/api/evidence/queue/filter/${caseId}`;
    
    if (evidenceClassFilter) {
      url += `?evidence_class=${evidenceClassFilter}`;
    }
    if (evidenceTypeFilter) {
      url += `&evidence_type=${evidenceTypeFilter}`;
    }
    
    const response = await fetch(url);
    const data = await response.json();
    
    // Group by evidence type
    const grouped = data.by_type || {};
    setGroupedEvidence(grouped);
    
  } catch (error) {
    console.error('Error fetching classified evidence:', error);
  }
};

// Render hierarchical groups
<Box>
  {/* Primary Evidence Section */}
  <Typography variant="h6">Primary Evidence</Typography>
  {Object.entries(groupedEvidence).map(([type, items]) => (
    <Accordion key={`primary-${type}`}>
      <AccordionSummary>
        <Chip 
          label={`${type} (${items.length})`}
          icon={getPrimaryIcon(type)}
        />
      </AccordionSummary>
      <AccordionDetails>
        <Table>
          {items.map(item => (
            <TableRow key={item.id}>
              <TableCell>{item.filename}</TableCell>
              <TableCell>{item.evidence_type}</TableCell>
              <TableCell>
                <Chip 
                  label={`${(item.classification_confidence * 100).toFixed(0)}%`}
                  color="primary"
                />
              </TableCell>
              <TableCell>{item.summary?.substring(0, 100)}...</TableCell>
            </TableRow>
          ))}
        </Table>
      </AccordionDetails>
    </Accordion>
  ))}
  
  {/* Secondary Evidence Section */}
  <Typography variant="h6" sx={{ mt: 3 }}>Secondary Evidence</Typography>
  {/* Similar structure for secondary */}
</Box>
```

**Add Filter UI:**
```jsx
<Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
  <Select
    value={evidenceClassFilter || ''}
    onChange={(e) => setEvidenceClassFilter(e.target.value)}
  >
    <MenuItem value="">All Evidence</MenuItem>
    <MenuItem value="primary">Primary Only</MenuItem>
    <MenuItem value="secondary">Secondary Only</MenuItem>
  </Select>
  
  <Select
    value={evidenceTypeFilter || ''}
    onChange={(e) => setEvidenceTypeFilter(e.target.value)}
  >
    <MenuItem value="">All Types</MenuItem>
    <MenuItem value="email">Emails</MenuItem>
    <MenuItem value="contract">Contracts</MenuItem>
    <MenuItem value="case_law">Case Law</MenuItem>
    {/* ... more types */}
  </Select>
</Box>
```

---

### 3. **ShotList.jsx Integration**

The shot list needs to:
- Pull facts from primary evidence only
- Extract entities and citations
- Link to evidence items

**Current File:** `apps/ui/react-app/src/components/ui/ShotList.jsx`

**Integration Points:**

```jsx
// Fetch primary evidence for shot extraction
const fetchPrimaryEvidenceForShots = async () => {
  try {
    const response = await fetch(
      `/api/evidence/queue/filter/${caseId}?evidence_class=primary`
    );
    const data = await response.json();
    
    // Extract shots from each primary evidence item
    const shots = [];
    for (const [type, items] of Object.entries(data.by_type || {})) {
      items.forEach((item, idx) => {
        const shot = {
          id: `shot-${item.id}`,
          fact: item.summary || item.filename,
          source: item.filename,
          evidence_id: item.id,
          evidence_type: item.evidence_type,
          evidence_class: 'primary',
          extracted_metadata: item.extracted_metadata,
        };
        shots.push(shot);
      });
    }
    
    setShots(shots);
    
  } catch (error) {
    console.error('Error fetching primary evidence:', error);
  }
};

// Enhanced shot display with evidence link
const renderShot = (shot) => (
  <Card>
    <CardContent>
      <Typography variant="body1">{shot.fact}</Typography>
      <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Chip 
          label={`Source: ${shot.source}`}
          size="small"
          icon={getEvidenceTypeIcon(shot.evidence_type)}
        />
        <Chip 
          label={shot.evidence_type}
          size="small"
          variant="outlined"
        />
        <Button 
          size="small"
          onClick={() => navigateToEvidence(shot.evidence_id)}
        >
          View Evidence
        </Button>
      </Box>
    </CardContent>
  </Card>
);
```

**Add Evidence Link Feature:**
```jsx
const handleLinkToClaim = async (shotId, claimId) => {
  try {
    // Find shot and its evidence
    const shot = shots.find(s => s.id === shotId);
    
    // Link to claim in backend
    await fetch(`/api/claims/${claimId}/add-evidence`, {
      method: 'POST',
      body: JSON.stringify({
        evidence_id: shot.evidence_id,
        evidence_type: shot.evidence_type,
        claim_element: 'fact'
      })
    });
    
  } catch (error) {
    console.error('Error linking to claim:', error);
  }
};
```

---

### 4. **ClaimsMatrix.jsx Integration**

The claims matrix needs to:
- Use both primary AND secondary evidence
- Map evidence to claim elements
- Display evidence support per element

**Current File:** `apps/ui/react-app/src/components/ui/ClaimsMatrix.jsx`

**Integration Points:**

```jsx
// Fetch all evidence (primary + secondary)
const fetchAllEvidenceForClaims = async () => {
  try {
    // Get both primary and secondary
    const primaryResponse = await fetch(
      `/api/evidence/queue/filter/${caseId}?evidence_class=primary`
    );
    const primaryData = await primaryResponse.json();
    
    const secondaryResponse = await fetch(
      `/api/evidence/queue/filter/${caseId}?evidence_class=secondary`
    );
    const secondaryData = await secondaryResponse.json();
    
    // Combine all evidence
    const allEvidence = {
      primary: primaryData.by_type || {},
      secondary: secondaryData.by_type || {}
    };
    
    return allEvidence;
    
  } catch (error) {
    console.error('Error fetching evidence:', error);
    return { primary: {}, secondary: {} };
  }
};

// Map evidence to claim elements
const mapEvidenceToClaims = (allEvidence, claims) => {
  return claims.map(claim => ({
    ...claim,
    element_support: claim.elements.map(element => ({
      ...element,
      primary_evidence: findRelatedPrimaryEvidence(
        element, 
        allEvidence.primary
      ),
      secondary_evidence: findRelatedSecondaryEvidence(
        element, 
        allEvidence.secondary
      )
    }))
  }));
};

// Display evidence support
const renderClaimWithEvidence = (claim) => (
  <Accordion>
    <AccordionSummary>{claim.name}</AccordionSummary>
    <AccordionDetails>
      {claim.element_support.map(element => (
        <Box key={element.id}>
          <Typography variant="subtitle2">{element.name}</Typography>
          
          {/* Primary Evidence Support */}
          {element.primary_evidence?.length > 0 && (
            <Box sx={{ ml: 2, mb: 1 }}>
              <Typography variant="caption" color="primary">
                Primary Evidence:
              </Typography>
              <List dense>
                {element.primary_evidence.map(ev => (
                  <ListItem key={ev.id} dense>
                    <Chip 
                      label={`📄 ${ev.filename}`}
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
          
          {/* Secondary Evidence Support */}
          {element.secondary_evidence?.length > 0 && (
            <Box sx={{ ml: 2 }}>
              <Typography variant="caption" color="secondary">
                Legal Authority:
              </Typography>
              <List dense>
                {element.secondary_evidence.map(ev => (
                  <ListItem key={ev.id} dense>
                    <Chip 
                      label={`📚 ${ev.evidence_type}`}
                      size="small"
                      variant="outlined"
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </Box>
      ))}
    </AccordionDetails>
  </Accordion>
);
```

---

### 5. **API Integration in App.jsx**

Register the new API routes in the main Flask app:

**File:** `src/lawyerfactory/api/app.py` or similar

```python
# At app initialization
from lawyerfactory.api.evidence_queue_api import register_evidence_queue_routes

# Register blueprints
register_evidence_queue_routes(app)

# Also ensure CORS is enabled
from flask_cors import CORS
CORS(app)
```

---

## 📋 Integration Checklist

### Frontend Components

- [ ] **LegalIntakeForm.jsx**
  - [ ] Imports EvidenceUploadQueue
  - [ ] Determines case_type from form
  - [ ] Shows queue after form submission
  - [ ] Tests with 'autonomous_vehicle' case

- [ ] **EvidenceTable.jsx**
  - [ ] Fetches from /api/evidence/queue/filter
  - [ ] Groups by evidence_class (primary/secondary)
  - [ ] Sub-groups by evidence_type
  - [ ] Shows confidence scores
  - [ ] Has filter dropdowns

- [ ] **ShotList.jsx**
  - [ ] Queries for primary evidence only
  - [ ] Extracts facts from evidence summaries
  - [ ] Links to evidence source
  - [ ] Maps to claims (future)

- [ ] **ClaimsMatrix.jsx**
  - [ ] Fetches both primary and secondary
  - [ ] Maps evidence to claim elements
  - [ ] Displays evidence support per element
  - [ ] Shows confidence/authority per support

### Backend Components

- [ ] **case_types.py**
  - [ ] Copied to config/
  - [ ] All enums defined
  - [ ] Classification functions work
  - [ ] Case type taxonomies complete

- [ ] **evidence_queue.py**
  - [ ] Copied to storage/core/
  - [ ] EvidenceQueueItem class works
  - [ ] EvidenceClassifier functional
  - [ ] Queue processes items
  - [ ] Async processing starts

- [ ] **evidence_queue_api.py**
  - [ ] Copied to api/
  - [ ] Endpoints registered with Flask
  - [ ] Handles file uploads
  - [ ] Returns correct status codes
  - [ ] CORS enabled

### Testing

- [ ] Upload single file
- [ ] Upload batch (10+ files)
- [ ] Check queue status updates
- [ ] Verify classifications appear
- [ ] Test primary vs secondary
- [ ] Test evidence type detection
- [ ] Verify confidence scores
- [ ] Check hierarchical grouping
- [ ] Test filtering by class
- [ ] Test filtering by type
- [ ] Verify error handling
- [ ] Load test with 40 files

---

## 🔄 Data Flow Example

**User Action:** Upload evidence after filling intake form

```
1. LegalIntakeForm submission
   └─> determineCaseType(formData) → "autonomous_vehicle"
   └─> setShowEvidenceQueue(true)

2. EvidenceUploadQueue renders
   └─> User selects files from disk
   └─> Component uploads to /api/evidence/queue/upload/CASE-001
       Request: FormData { files: [...], case_type: "autonomous_vehicle" }
       Response: { items: [...queue items...] }

3. Queue processing begins
   └─> Backend adds to EvidenceProcessingQueue
   └─> Processing starts (max 3 concurrent)
   └─> For each file:
       ├─ Read content
       ├─ Classify (primary/secondary)
       ├─ Determine type (email, contract, etc.)
       ├─ Extract metadata
       ├─ Create summary
       └─ Vectorize

4. Frontend polls status
   └─> GET /api/evidence/queue/status/CASE-001
   └─> Every 2 seconds
   └─> Updates queue item progress bars
   └─> Shows classification badges as complete

5. Downstream components access results
   └─> ShotList queries primary evidence
   └─> ClaimsMatrix queries both types
   └─> EvidenceTable displays hierarchical view
```

---

## 🎯 Expected Behavior After Integration

### For Users

1. Fill out LegalIntakeForm
2. See EvidenceUploadQueue appear below form
3. Upload evidence (single or batch)
4. See real-time progress for each file
5. When complete, see classification (Primary/Secondary + Type)
6. See confidence score for each classification
7. Use EvidenceTable to browse organized evidence
8. Create facts in ShotList from primary evidence
9. Build claims in ClaimsMatrix using both types

### For Developers

1. Query `/api/evidence/queue/status/{caseId}` → See all queue items
2. Query `/api/evidence/queue/filter/{caseId}?evidence_class=primary` → Get primary only
3. Query `/api/evidence/queue/stats/{caseId}` → Get statistics
4. Import EvidenceUploadQueue → Display queue UI
5. Use data in downstream components

---

## 🚨 Troubleshooting

### Queue not processing
- Check Flask app has registered blueprint
- Verify async task started
- Check logs for errors

### Classifications not appearing
- Verify classifier imported correctly
- Check classifier initialized
- Ensure content being read

### Hierarchical groups not showing
- Verify filter endpoint working
- Check data structure matches expected
- Ensure component rendering groups

### Confidence scores missing
- Check classifier returning confidence
- Verify data passed through pipeline
- Ensure UI displaying score

---

## 📚 Supporting Documentation

- `EVIDENCE_PROCESSING_PIPELINE.md` - Complete architecture
- `EVIDENCE_PIPELINE_QUICK_REFERENCE.md` - Quick API reference
- `legal_specialist_instructions.md` - Legal requirements
- `prompt_instructions.md` - LLM configuration

---

**Version:** 1.0  
**Status:** Ready for Integration  
**Last Updated:** October 19, 2025
