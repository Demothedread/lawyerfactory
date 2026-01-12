# Tavily Research Integration - PRIMARY/SECONDARY Evidence System

## Overview

The LawyerFactory platform now includes **Tavily-powered legal research** with automatic **PRIMARY/SECONDARY evidence classification**. This integration enables intelligent research automation where user-uploaded evidence triggers comprehensive academic and news searches, storing research findings as distinct SECONDARY evidence.

## Architecture

### Evidence Classification Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     EVIDENCE SOURCES                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐      ┌──────────────────────┐   │
│  │  PRIMARY EVIDENCE    │      │  SECONDARY EVIDENCE  │   │
│  │                      │      │                      │   │
│  │  • User Uploads      │─────▶│  • Tavily Search     │   │
│  │  • Direct Documents  │      │  • CourtListener     │   │
│  │  • Depositions       │      │  • Google Scholar    │   │
│  │  • Contracts         │      │  • Academic Sources  │   │
│  │  • Complaints        │      │  • News Articles     │   │
│  └──────────────────────┘      └──────────────────────┘   │
│           │                              │                  │
│           │ Keywords Extracted           │                  │
│           ▼                              ▼                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          UNIFIED EVIDENCE TABLE                      │  │
│  │  - Sortable by evidence_source                       │  │
│  │  - Filterable PRIMARY/SECONDARY                      │  │
│  │  - Real-time Socket.IO updates                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Workflow

### 1. Upload PRIMARY Evidence
User uploads documents (complaint, contract, deposition, etc.) → System stores as PRIMARY evidence with `evidence_source="primary"`.

### 2. Keyword Extraction
Research bot (`research.py`) extracts keywords from PRIMARY evidence using:
- **Validation Keywords**: `evidence_ingestion.py` patterns (COMPLAINTS_AGAINST_TESLA, CONTRACT_DISPUTES, PERSONAL_INJURY, etc.)
- **Legal Patterns**: Regex matching for "negligence", "liability", "breach", "contract", etc.
- **Document Classification**: Pattern-based categorization (complaint, case_opinion, deposition, expert_report)

### 3. Tavily Search Execution
Keywords trigger comprehensive Tavily research:
```python
# Academic Sources (12 domains)
scholar.google.com, SSRN, JSTOR, heinonline, westlaw, lexisnexis, etc.

# News Sources (8 outlets)
NYT, WSJ, Bloomberg, Reuters, AP, BBC, CNN, Fox

# Web Sources
General legal databases and authoritative sources
```

### 4. SECONDARY Evidence Storage
Research results stored with:
- `evidence_source="secondary"`
- `research_query` = original search terms
- `research_confidence` = Tavily confidence score
- Linked to PRIMARY evidence via `case_id` + `evidence_id`

### 5. Real-Time Updates
Socket.IO events for research lifecycle:
```javascript
'research_started'    → Research initiated
'research_completed'  → SECONDARY evidence created
'research_failed'     → Error handling
```

## Implementation Files

### Backend

1. **`src/lawyerfactory/storage/evidence/table.py`**
   - Added `EvidenceSource` enum (PRIMARY/SECONDARY)
   - Added `evidence_source` field to `EvidenceEntry`
   - Added `research_query` and `research_confidence` fields

2. **`src/lawyerfactory/agents/research/research.py`**
   - `extract_keywords_from_evidence()` - Keyword extraction from PRIMARY evidence
   - `research_from_evidence_keywords()` - Tavily search execution
   - Integrated `TavilyResearchIntegration` from `tavily_integration.py`

3. **`apps/api/routes/research_flask.py`** (NEW)
   - `/api/research/execute` - Trigger research from PRIMARY evidence
   - `/api/research/extract-keywords` - Extract keywords without executing research
   - `/api/research/status/<research_id>` - Research status tracking

4. **`apps/api/routes/evidence_flask.py`** (UPDATED)
   - Export `evidence_source`, `research_query`, `research_confidence` in GET `/api/evidence`
   - Accept `evidence_source` in POST/PUT operations

5. **`apps/api/server.py`** (UPDATED)
   - Registered `FlaskResearchAPI` with Socket.IO integration

### Frontend

1. **`apps/ui/react-app/src/components/ui/EvidenceTable.jsx`** (ENHANCED)
   - **New Features**:
     * Evidence Source filter dropdown (All/PRIMARY/SECONDARY)
     * "Request Research" menu item (PRIMARY evidence only)
     * Research dialog with custom keywords input
     * Socket.IO listeners for `research_started`, `research_completed`, `research_failed`
     * "Source" column displaying PRIMARY/SECONDARY chips
     * Edit capability for evidence entries
     * Create new evidence button

## User Guide

### Requesting Research

1. **Upload PRIMARY Evidence**: Use evidence upload interface to upload documents
2. **Right-Click Evidence Row**: Click 3-dot menu on any PRIMARY evidence entry
3. **Select "Request Research"**: Opens research dialog
4. **Optional Keywords**: Enter custom comma-separated keywords, or leave blank for auto-extraction
5. **Execute Research**: Click "Execute Research" button
6. **Monitor Progress**: Watch real-time toast notifications for research status
7. **Review SECONDARY Evidence**: Filter by "SECONDARY Only" to see research results

### Filtering Evidence

- **Evidence Source Dropdown**: Filter by All Evidence / PRIMARY Only / SECONDARY Only
- **Search Box**: Search across filename, description, tags, object_id, research_query
- **Sort Columns**: Click column headers to sort by filename, upload_date, source, etc.

### Viewing Research Details

- Click on SECONDARY evidence to view:
  - Original research query
  - Research confidence score
  - Source URL (if available)
  - Linked PRIMARY evidence

## API Usage Examples

### Execute Research from PRIMARY Evidence

```bash
curl -X POST http://localhost:5000/api/research/execute \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_123",
    "evidence_id": "evidence_456",
    "keywords": ["tesla", "autonomous vehicle", "liability"],
    "max_results": 5
  }'
```

**Response:**
```json
{
  "research_id": "research_789",
  "status": "completed",
  "result": {
    "research_results": [...],
    "secondary_evidence_ids": ["evidence_111", "evidence_222"],
    "confidence_score": 0.85,
    "total_sources": 10,
    "academic_sources": 6,
    "news_sources": 4,
    "recommendations": [...]
  },
  "message": "Research completed with 2 SECONDARY evidence entries"
}
```

### Extract Keywords Only

```bash
curl -X POST http://localhost:5000/api/research/extract-keywords \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_id": "evidence_456"
  }'
```

**Response:**
```json
{
  "keywords": ["tesla", "autonomous vehicle", "liability", "negligence", "plaintiff"],
  "count": 5
}
```

### Filter Evidence by Source

```bash
curl "http://localhost:5000/api/evidence?evidence_source=secondary"
```

## Configuration

### Environment Variables

```bash
# Tavily API (required for research)
TAVILY_API_KEY=your_tavily_api_key

# CourtListener API (optional, enhances legal research)
COURTLISTENER_API_KEY=your_courtlistener_api_key

# OpenAI/Anthropic (required for keyword extraction LLM fallback)
OPENAI_API_KEY=your_openai_key
```

### Settings in React UI

Users can configure research behavior via LLM Settings panel:
- **Research Mode**: Enable/disable automatic research
- **Citation Validation**: Validate legal citations from research
- **Jurisdiction**: federal/state filtering for legal sources
- **Citation Style**: Bluebook formatting

## Technical Details

### Keyword Extraction Algorithm

1. **Validation Type Matching**: Match evidence content against predefined validation keywords
   ```python
   COMPLAINTS_AGAINST_TESLA: ["tesla", "elon musk", "autonomous vehicle", ...]
   CONTRACT_DISPUTES: ["breach", "contract", "agreement", ...]
   PERSONAL_INJURY: ["injury", "negligence", "damages", ...]
   ```

2. **Legal Pattern Matching**: Regex extraction of legal terms
   ```python
   r'\b(negligence|liability|breach|contract|damages|injury)\b'
   r'\b(plaintiff|defendant|court|judge|jury)\b'
   ```

3. **Deduplication**: Remove duplicate keywords and return unique set

### Tavily Research Execution

```python
# Tavily query construction
tavily_query = TavilyResearchQuery(
    query_text=" ".join(keywords[:10]),  # Top 10 keywords
    search_type="comprehensive",
    max_results=5
)

# Execute searches in parallel
academic_results = await tavily_client.search_academic_sources(tavily_query)
news_results = await tavily_client.search_news_sources(tavily_query)

# Combine and score results
research_result = tavily_client.comprehensive_research(tavily_query)
```

### Storage Tier Coordination

```python
# SECONDARY evidence storage via unified storage
storage_result = await unified_storage.store_evidence(
    file_content=source["content"].encode('utf-8'),
    filename=source["title"] + ".txt",
    metadata={
        "case_id": case_id,
        "primary_evidence_id": evidence_id,
        "research_query": query_text,
        "source_url": source.get("url"),
        "confidence_score": source.get("relevance_score"),
    },
    source_phase="phaseA02_research"
)

# Evidence table entry
evidence_entry = EvidenceEntry(
    source_document=source["title"],
    content=source["content"],
    evidence_source=EvidenceSource.SECONDARY,
    research_query=query_text,
    research_confidence=research_result.confidence_score,
    object_id=storage_result.object_id  # Links to S3/Local/Vector tiers
)
```

## Testing

### Integration Test

```bash
python test_integration_flow.py
```

### Manual Testing Checklist

1. **Upload PRIMARY Evidence**
   - ✅ Evidence appears with PRIMARY chip
   - ✅ Right-click menu shows "Request Research"

2. **Execute Research**
   - ✅ Research dialog opens with keyword input
   - ✅ Toast notification shows "Research started"
   - ✅ Socket.IO real-time update received

3. **Verify SECONDARY Evidence**
   - ✅ SECONDARY evidence entries created
   - ✅ SECONDARY chip displayed in Source column
   - ✅ Research query visible in details dialog
   - ✅ Linked to PRIMARY evidence via case_id

4. **Filter by Evidence Source**
   - ✅ "PRIMARY Only" filter shows only uploads
   - ✅ "SECONDARY Only" filter shows only research results
   - ✅ "All Evidence" shows combined view

5. **Socket.IO Real-Time Updates**
   - ✅ `research_started` event triggers toast
   - ✅ `research_completed` event refreshes evidence table
   - ✅ `research_failed` event shows error toast

## Future Enhancements

1. **Automatic Research Triggers**: Auto-execute research on PRIMARY evidence upload
2. **Research Scheduling**: Queue research jobs for batch processing
3. **Citation Validation**: Validate legal citations from SECONDARY evidence
4. **Evidence Linking**: Visualize relationships between PRIMARY and SECONDARY evidence
5. **Research Analytics**: Dashboard showing research statistics and confidence trends
6. **Custom Research Agents**: User-defined research workflows beyond Tavily

## Troubleshooting

### Research Not Executing

- **Check TAVILY_API_KEY**: Ensure environment variable is set
- **Backend Logs**: Check `lawyerfactory.log` for Tavily errors
- **Socket.IO Connection**: Verify frontend connected to Socket.IO (check browser console)

### No Keywords Extracted

- **Evidence Content Empty**: Ensure PRIMARY evidence has text content
- **Evidence Ingestion Module**: Verify `evidence_ingestion.py` imported correctly
- **Fallback Extraction**: System uses simple regex if evidence_ingestion unavailable

### SECONDARY Evidence Not Created

- **Unified Storage**: Check unified storage API initialized (`UNIFIED_STORAGE_AVAILABLE=True`)
- **Evidence Table**: Verify `EnhancedEvidenceTable` accessible
- **ObjectID Generation**: Ensure S3/Local storage tier working

## Support

For issues or questions:
1. Check backend logs: `lawyerfactory.log`
2. Check frontend console: Browser DevTools
3. Review integration test: `python test_integration_flow.py`
4. Consult `knowledge_graph.json` for entity relationships

---

**Version**: 2.1.0  
**Last Updated**: 2025-01-16  
**Status**: ✅ Production Ready
