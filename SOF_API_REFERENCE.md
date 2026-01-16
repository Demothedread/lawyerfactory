# Statement of Facts API Reference

**Version:** 1.0  
**Status:** Production Ready  
**Base URL:** `http://localhost:5000` (development) or production domain

---

## Endpoints

### 1. Extract Facts from Narrative + Evidence

**Endpoint:** `POST /api/facts/extract`

**Purpose:** Extract pertinent facts from user's intake narrative and uploaded evidence documents using LLM analysis.

**Request:**
```json
{
  "case_id": "string (required)",
  "narrative": "string (required) - User's claim description from intake form",
  "evidence": [
    {
      "id": "string - Document ID",
      "title": "string - Document title",
      "type": "string - contract|email|report|etc",
      "content": "string - Document text/content"
    }
  ]
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "case_id": "string",
  "facts_count": 6,
  "extraction_timestamp": "2024-01-15T10:30:00Z",
  "facts": [
    {
      "fact_number": 1,
      "fact_text": "On January 15, 2024, Plaintiff entered into service agreement with Defendant.",
      "date": "2024-01-15",
      "entities": {
        "people": ["Plaintiff", "Defendant"],
        "places": [],
        "organizations": [],
        "dates": ["January 15, 2024"]
      },
      "supporting_evidence": ["doc_001"],
      "favorable_to_client": true,
      "chronological_order": 1
    },
    {
      "fact_number": 2,
      "fact_text": "The service agreement specified a 60-day delivery timeline.",
      "date": "2024-01-15",
      "entities": {
        "people": [],
        "places": [],
        "organizations": [],
        "dates": []
      },
      "supporting_evidence": ["doc_001"],
      "favorable_to_client": false,
      "chronological_order": 2
    }
    // ... additional facts
  ],
  "metadata": {
    "narrative_length": 1234,
    "evidence_documents": 4,
    "extraction_method": "llm",
    "llm_model": "gpt-4",
    "processing_time_seconds": 12.5
  }
}
```

**Response (Error - 400/500):**
```json
{
  "success": false,
  "error": "string - Error message",
  "error_type": "validation|api|extraction",
  "fallback_used": false
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/facts/extract \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_2024_001",
    "narrative": "On January 15, 2024, I entered into a contract...",
    "evidence": [
      {
        "id": "doc_001",
        "title": "Contract",
        "type": "contract",
        "content": "SERVICE AGREEMENT..."
      }
    ]
  }'
```

**Integration Notes:**
- Called automatically by ShotList component on mount
- Triggered by `loadFactsFromLLM()` method
- Results stored in `extractedFacts` state
- Fact data passed to `generateStatementOfFacts()` next
- Includes loading state management for UI feedback

---

### 2. Generate Statement of Facts

**Endpoint:** `POST /api/statement-of-facts/generate`

**Purpose:** Generate Rule 12(b)(6) compliant Statement of Facts with jurisdiction, venue, ripeness analysis, and chronologically ordered facts with evidence citations.

**Request:**
```json
{
  "case_id": "string (required)",
  "facts": [
    {
      "fact_number": 1,
      "fact_text": "string",
      "date": "YYYY-MM-DD",
      "supporting_evidence": ["doc_id"],
      "favorable_to_client": boolean,
      "chronological_order": 1
    }
  ],
  "intake_data": {
    "user_name": "string - Plaintiff/Client name",
    "other_party_name": "string - Defendant name",
    "jurisdiction": "string - Federal/State District",
    "venue": "string - Specific venue",
    "event_location": "string - Where events occurred"
  }
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "case_id": "string",
  "statement_of_facts": "## STATEMENT OF FACTS\n\n### I. JURISDICTION AND VENUE\n\n**1.1 Jurisdiction** ...",
  "word_count": 1456,
  "facts_incorporated": 6,
  "generation_timestamp": "2024-01-15T10:35:00Z",
  "metadata": {
    "includes_jurisdiction": true,
    "includes_venue": true,
    "includes_ripeness": true,
    "rule_12b6_compliant": true,
    "has_evidence_citations": true,
    "fact_references": ["fact_1", "fact_2", "fact_3", "fact_4", "fact_5", "fact_6"]
  },
  "compliance_status": {
    "rule_12b6_compliant": true,
    "issues": [],
    "warnings": []
  }
}
```

**Response (Error - 400/500):**
```json
{
  "success": false,
  "error": "string - Error message",
  "error_type": "validation|generation|storage"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/statement-of-facts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_2024_001",
    "facts": [
      {
        "fact_number": 1,
        "fact_text": "On January 15, 2024, Plaintiff entered into service agreement...",
        "date": "2024-01-15",
        "supporting_evidence": ["doc_001"],
        "favorable_to_client": true,
        "chronological_order": 1
      }
    ],
    "intake_data": {
      "user_name": "John Doe",
      "other_party_name": "Acme Corp",
      "jurisdiction": "Southern District of New York",
      "venue": "U.S. District Court, S.D.N.Y.",
      "event_location": "New York, NY"
    }
  }'
```

**Integration Notes:**
- Called after fact extraction completes
- Triggered by `generateStatementOfFacts()` method
- Results stored in `sofContent` state
- Triggers `onStatementOfFactsReady` callback
- SOF displayed in dialog and PhaseB01Review Tab 0
- Saves to: `{case_dir}/deliverables/statement_of_facts.md`

---

### 3. Validate Rule 12(b)(6) Compliance

**Endpoint:** `POST /api/facts/validate-12b6`

**Purpose:** Validate extracted facts for Rule 12(b)(6) compliance including plausibility standard, who/what/when/where elements, evidence citations, and legal sufficiency.

**Request:**
```json
{
  "case_id": "string (required)",
  "facts": [
    {
      "fact_number": 1,
      "fact_text": "string",
      "date": "YYYY-MM-DD",
      "entities": {
        "people": ["string"],
        "places": ["string"],
        "dates": ["string"]
      },
      "supporting_evidence": ["string"]
    }
  ]
}
```

**Response (Success - 200):**
```json
{
  "case_id": "string",
  "compliant": true,
  "validation_timestamp": "2024-01-15T10:36:00Z",
  "compliance_score": 95,
  "checks": {
    "minimum_facts": {
      "passed": true,
      "message": "6 facts present (minimum 3 required)",
      "severity": "info"
    },
    "chronological_organization": {
      "passed": true,
      "message": "All facts properly ordered by date",
      "severity": "info"
    },
    "who_element": {
      "passed": true,
      "message": "Parties identified in all facts",
      "severity": "info"
    },
    "what_element": {
      "passed": true,
      "message": "Actions/events described in all facts",
      "severity": "info"
    },
    "when_element": {
      "passed": true,
      "message": "Dates present in all time-specific facts",
      "severity": "info"
    },
    "where_element": {
      "passed": false,
      "message": "Location missing in fact 3",
      "severity": "warning"
    },
    "evidence_citations": {
      "passed": true,
      "message": "All facts have supporting evidence",
      "severity": "info"
    },
    "plausibility": {
      "passed": true,
      "message": "Facts meet Ashcroft/Twombly standard",
      "severity": "info"
    }
  },
  "issues": [
    {
      "fact_id": 3,
      "issue": "Missing location information",
      "severity": "warning",
      "suggestion": "Add location where action occurred"
    }
  ],
  "warnings": [
    {
      "type": "temporal_gap",
      "description": "7-day gap between facts 2 and 3",
      "recommendation": "Consider whether intermediate facts are needed"
    }
  ],
  "summary": {
    "total_facts": 6,
    "passed_checks": 8,
    "failed_checks": 0,
    "warning_count": 1,
    "compliance_percentage": 95
  }
}
```

**Response (Error - 400/500):**
```json
{
  "success": false,
  "error": "string - Error message",
  "error_type": "validation|processing"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/facts/validate-12b6 \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_2024_001",
    "facts": [
      {
        "fact_number": 1,
        "fact_text": "On January 15, 2024, Plaintiff entered into service agreement with Defendant.",
        "date": "2024-01-15",
        "entities": {
          "people": ["Plaintiff", "Defendant"],
          "places": [],
          "dates": ["January 15, 2024"]
        },
        "supporting_evidence": ["doc_001"]
      }
    ]
  }'
```

**Integration Notes:**
- Called after fact extraction
- Triggered by `validateRule12b6Compliance()` method
- Results stored in `rule12b6Status` state
- Status displayed in Alert component
- Issues/warnings prevent approval if critical

---

## Error Codes & Handling

| Code | Error | Solution |
|------|-------|----------|
| 400 | Missing required fields | Verify request includes all required fields |
| 401 | Unauthorized API key | Check OpenAI/Anthropic/Groq API keys in .env |
| 429 | Rate limit exceeded | Wait 60 seconds before retry |
| 500 | LLM API error | Fallback to Anthropic/Groq/heuristic occurs automatically |
| 503 | Service unavailable | Retry with exponential backoff |

## Fallback Chain

```
Request → OpenAI gpt-4
          ↓ (if error)
        Anthropic Claude-3
          ↓ (if error)
        Groq Mixtral-8x7b
          ↓ (if error)
        Heuristic Extraction (no LLM)
```

---

## Frontend Integration Pattern

### Using in React Component

```javascript
// 1. Import the component
import ShotList from './components/ui/ShotList';

// 2. Provide required props
<ShotList
  caseId={caseId}
  evidenceData={evidence}
  userNarrative={claimDescription}
  intakeData={{
    user_name: 'John Doe',
    other_party_name: 'Acme Corp',
    jurisdiction: 'Federal - S.D.N.Y.',
    venue: 'U.S. District Court, S.D.N.Y.',
    event_location: 'New York, NY'
  }}
  onStatementOfFactsReady={(sofData) => {
    // Called when SOF generation completes
    setSofContent(sofData);
  }}
/>

// 3. API calls happen automatically:
// - POST /api/facts/extract (on mount)
// - POST /api/statement-of-facts/generate (after extraction)
// - POST /api/facts/validate-12b6 (validation)
```

### State Management Pattern

```javascript
const [extractedFacts, setExtractedFacts] = useState(null);
const [sofContent, setSofContent] = useState(null);
const [rule12b6Status, setRule12b6Status] = useState(null);
const [loading, setLoading] = useState(false);

// In parent component:
const handleStatementOfFactsReady = (sofData) => {
  setSofContent(sofData.statement_of_facts);
  // Now can use in PhaseB01Review
};
```

---

## Testing the API

### Integration Test Suite

```bash
# Run all tests
cd /Users/jreback/Projects/LawyerFactory
python -m pytest test_sof_e2e.py -v

# Run specific test
python -m pytest test_sof_e2e.py::TestStatementOfFactsE2E::test_fact_extraction_from_narrative_and_evidence -v

# Run with detailed output
python -m pytest test_sof_e2e.py -vv -s
```

### Manual API Testing with Postman

1. Import into Postman (or use cURL)
2. Set Base URL: `http://localhost:5000`
3. Create test case with sample data
4. Test each endpoint in order:
   - First: POST /api/facts/extract
   - Second: POST /api/statement-of-facts/generate
   - Third: POST /api/facts/validate-12b6

---

## Performance Considerations

| Metric | Target | Notes |
|--------|--------|-------|
| Fact Extraction | < 15s | LLM API call + parsing |
| SOF Generation | < 5s | Template rendering + storage |
| Validation | < 2s | Pattern matching only |
| Total Pipeline | < 25s | User-acceptable latency |

**Optimization Tips:**
- Cache LLM responses for identical narratives
- Implement pagination for 50+ facts
- Use lazy loading for evidence documents
- Consider request debouncing in UI

---

## Security Notes

1. **API Keys:** Store in `.env` file, never commit to git
2. **Data Privacy:** Evidence content encrypted at rest
3. **Rate Limiting:** Implement 100 req/min per IP
4. **Input Validation:** All inputs sanitized before LLM
5. **Output Escaping:** All markdown outputs safely rendered

---

## Monitoring & Logging

### Key Metrics to Track

```python
# In server.py logging:
- Extraction time per case
- LLM API cost per extraction
- Compliance validation pass rate
- Error rate by LLM provider
- Average fact count per case
```

### Debug Logging

```javascript
// In ShotList.jsx:
console.log('🧠 Extracting facts...');
console.log('✅ Extracted', data.facts.length, 'facts');
console.log('📄 SOF generated:', data.word_count, 'words');
```

---

**API Version:** 1.0  
**Last Updated:** 2024  
**Maintainer:** LawyerFactory Development Team  
**Status:** Production Ready ✅
