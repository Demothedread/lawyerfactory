# Evidence Pipeline - Developer Quick Reference

## 🚀 Quick Start

### Upload Evidence
```jsx
import EvidenceUploadQueue from './components/ui/EvidenceUploadQueue';

<EvidenceUploadQueue caseId="CASE-2024-001" />
```

### Get Queue Status
```javascript
// Polling (automatic in component)
fetch('/api/evidence/queue/status/CASE-2024-001')
  .then(r => r.json())
  .then(data => console.log(`${data.completed}/${data.total} done`))
```

### Upload Files from Code
```javascript
const uploadEvidence = async (caseId, files, caseType) => {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));
  formData.append('case_type', caseType);
  
  const response = await fetch(
    `/api/evidence/queue/upload/${caseId}`, 
    { method: 'POST', body: formData }
  );
  return response.json();
};
```

## 🔤 Evidence Classes

### PRIMARY Evidence
```python
PrimaryEvidenceType.EMAIL              # Email messages
PrimaryEvidenceType.CONTRACT           # Contracts/agreements
PrimaryEvidenceType.SYSTEM_LOG         # Software logs/debug
PrimaryEvidenceType.VIDEO_FOOTAGE      # Video files
PrimaryEvidenceType.PHOTOGRAPHS        # Images
PrimaryEvidenceType.ACCIDENT_REPORT    # Police reports
PrimaryEvidenceType.MEDICAL_RECORD     # Medical documents
PrimaryEvidenceType.WITNESS_STATEMENT  # Witness accounts
PrimaryEvidenceType.EXPERT_REPORT      # Expert analysis
```

### SECONDARY Evidence
```python
SecondaryEvidenceType.CASE_LAW         # Court opinions
SecondaryEvidenceType.STATUTES         # Laws/codes
SecondaryEvidenceType.REGULATIONS      # Administrative rules
SecondaryEvidenceType.JOURNAL_ARTICLE  # Academic papers
SecondaryEvidenceType.LAW_REVIEW       # Law review articles
SecondaryEvidenceType.TREATISE         # Legal treatises
```

## 📊 Case Types

```python
CaseType.AUTONOMOUS_VEHICLE    # Self-driving vehicle accidents
CaseType.PRODUCT_LIABILITY     # Defective products
CaseType.AUTO_ACCIDENT         # Car accidents
CaseType.NEGLIGENCE           # General negligence
CaseType.CONTRACT_BREACH      # Broken contracts
CaseType.EMPLOYMENT_DISPUTE   # Employment issues
CaseType.MEDICAL_MALPRACTICE  # Medical errors
CaseType.INTELLECTUAL_PROPERTY # Patent/copyright issues
```

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/evidence/queue/upload/{caseId}` | Upload files |
| `GET` | `/api/evidence/queue/status/{caseId}` | Get queue status |
| `GET` | `/api/evidence/queue/filter/{caseId}` | Filter by type |
| `GET` | `/api/evidence/queue/stats/{caseId}` | Get statistics |

## 🔍 Query Examples

### Get All Primary Evidence
```bash
curl '/api/evidence/queue/filter/CASE-001?evidence_class=primary'
```

### Get Emails Only
```bash
curl '/api/evidence/queue/filter/CASE-001?evidence_class=primary&evidence_type=email'
```

### Get Statistics
```bash
curl '/api/evidence/queue/stats/CASE-001'
```

## 💻 Response Examples

### Queue Status
```json
{
  "total": 25,
  "queued": 5,
  "processing": 2,
  "completed": 18,
  "queue_items": [...],
  "completed_items": [
    {
      "filename": "accident.pdf",
      "evidence_class": "primary",
      "evidence_type": "accident_report",
      "classification_confidence": 0.98,
      "summary": "Police report from 01/15/2024..."
    }
  ]
}
```

### Filtered Evidence
```json
{
  "evidence_class": "primary",
  "total_count": 12,
  "by_type": {
    "email": [item1, item2, ...],
    "contract": [item3, item4, ...],
    "video_footage": [item5, ...]
  }
}
```

### Statistics
```json
{
  "total_processed": 20,
  "primary_evidence": 12,
  "secondary_evidence": 8,
  "primary_percentage": 60,
  "error_count": 0,
  "average_confidence": 0.92,
  "evidence_type_breakdown": {
    "email": 5,
    "contract": 3,
    "case_law": 4
  }
}
```

## 📋 Processing Status Values

| Status | Meaning |
|--------|---------|
| `queued` | Waiting to process |
| `processing` | Currently being processed |
| `classified` | Classification complete |
| `summarized` | Summary created |
| `vectorized` | Stored in vector DB |
| `complete` | All steps done |
| `error` | Processing failed |

## 🎯 Classification Confidence

- **95%**: Metadata-driven (user uploaded with case_id)
- **85%**: Source URL indicates research material
- **80-90%**: Content keyword matching
- **<80%**: Should prompt user for confirmation

## 🔗 Component Integration

### In LegalIntakeForm
```jsx
onSubmit={(data) => {
  // Files uploaded with case_type from form
  uploadEvidence(caseId, files, data.caseType);
}}
```

### In EvidenceTable
```jsx
// Query primary evidence
const { data } = await fetch(
  `/api/evidence/queue/filter/${caseId}?evidence_class=primary`
);

// Group and display by type
groupByType(data.by_type).map(group => (
  <EvidenceTypeGroup items={group} />
))
```

### In ShotList
```jsx
// Get primary evidence only
const facts = completedItems
  .filter(i => i.evidence_class === 'primary')
  .map(i => extractFact(i));
```

### In ClaimsMatrix
```jsx
// Get both primary and secondary
const allEvidence = await fetch(
  `/api/evidence/queue/filter/${caseId}`
);

// Map to claim elements
```

## 🐛 Debugging Tips

### Check Queue Status
```javascript
// See what's in the queue
fetch('/api/evidence/queue/status/CASE-001')
  .then(r => r.json())
  .then(d => console.log(JSON.stringify(d, null, 2)))
```

### Get Error Details
```javascript
// Check for errors in completed items
const { data } = await fetch(...);
const errors = data.completed_items.filter(i => i.error_message);
errors.forEach(e => console.error(e.filename + ': ' + e.error_message));
```

### Manual Upload Test
```bash
# Upload files to test
curl -X POST \
  -F "files=@file1.pdf" \
  -F "files=@file2.txt" \
  -F "case_type=autonomous_vehicle" \
  http://localhost:5000/api/evidence/queue/upload/TEST-CASE
```

## ⚙️ Configuration

### Change Concurrent Jobs
```python
from lawyerfactory.storage.core.evidence_queue import get_or_create_queue
queue = get_or_create_queue('CASE-001', 'autonomous_vehicle')
queue.max_concurrent_jobs = 5  # Process 5 at a time
```

### Change Polling Interval
```jsx
<EvidenceUploadQueue 
  caseId={caseId} 
  pollingInterval={5000}  // 5 seconds
/>
```

### Register Status Callback
```python
def on_item_complete(item):
    print(f"Completed: {item.filename}")
    # Do something with completed item

queue.register_status_callback(on_item_complete)
```

## 📚 Documentation Files

- **EVIDENCE_PROCESSING_PIPELINE.md** - Complete architectural guide
- **EVIDENCE_PIPELINE_IMPLEMENTATION_SUMMARY.md** - Deployment steps
- **This file** - Quick reference

## 🚨 Common Issues

### Issue: Files stuck in "queued"
**Solution:** Check that async processing started
```python
# In Flask app
asyncio.create_task(_process_queue_async(queue, case_id))
```

### Issue: Classifications not appearing
**Solution:** Ensure classifier is initialized
```python
from evidence_queue import EvidenceClassifier
classifier = EvidenceClassifier()
```

### Issue: Queue never completes
**Solution:** Check max_concurrent_jobs setting and error logs
```python
queue.max_concurrent_jobs = 1  # Debug with 1 job
```

## ✅ Checklist for Integration

- [ ] Copy Python files to src/lawyerfactory/
- [ ] Copy React component to apps/ui/react-app/
- [ ] Register Flask blueprint in app.py
- [ ] Test single file upload
- [ ] Test multiple file batch
- [ ] Verify classifications
- [ ] Check confidence scores
- [ ] Test error handling
- [ ] Verify downstream components can access evidence
- [ ] Load test with 40+ files
- [ ] Performance acceptable?

## 📞 Support

For complete documentation, see:
- `EVIDENCE_PROCESSING_PIPELINE.md` - Detailed architecture
- `legal_specialist_instructions.md` - Legal requirements
- `COMPONENT_ENHANCEMENT_REPORT.md` - UI details

---

**Last Updated:** October 19, 2025  
**Version:** 1.0  
**Status:** Ready for Use
