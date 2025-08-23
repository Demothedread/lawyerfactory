# Draft Document Processing Implementation

## Overview

This document describes the implementation of Phase 2 backend infrastructure for draft document ingestion, supporting the Facts Matrix & Statement of Facts Generation workflow. The implementation adds specialized processing for fact statement drafts and case/complaint drafts with priority handling and enhanced knowledge graph integration.

## Architecture Overview

```mermaid
graph TB
    subgraph Frontend
        UI[Enhanced Factory UI]
        FACT_UPLOAD[Fact Statement Upload Zone]
        CASE_UPLOAD[Case/Complaint Upload Zone]
    end
    
    subgraph Backend_Endpoints
        FACT_API[/api/upload-fact-draft]
        CASE_API[/api/upload-case-draft]
        REGULAR_API[/api/upload]
    end
    
    subgraph Processing_Layer
        DRAFT_PROCESSOR[Draft Document Processor]
        AGGREGATOR[Draft Aggregation Logic]
        ANALYZER[Enhanced Analysis Engine]
    end
    
    subgraph Storage_Layer
        FACT_DIR[uploads/fact_drafts/]
        CASE_DIR[uploads/case_drafts/]
        REGULAR_DIR[uploads/]
    end
    
    subgraph Knowledge_Graph
        KG_CORE[Knowledge Graph Core]
        KG_EXT[Knowledge Graph Extensions]
        FOUNDATIONAL[Foundational Entity Storage]
    end
    
    subgraph Enhanced_Maestro
        DRAFT_PROC[Draft Processing Logic]
        ENTITY_EXTRACT[Legal Entity Extraction]
        FACT_EXTRACT[Legal Fact Extraction]
    end
    
    FACT_UPLOAD --> FACT_API
    CASE_UPLOAD --> CASE_API
    FACT_API --> DRAFT_PROCESSOR
    CASE_API --> DRAFT_PROCESSOR
    DRAFT_PROCESSOR --> AGGREGATOR
    AGGREGATOR --> ANALYZER
    ANALYZER --> FACT_DIR
    ANALYZER --> CASE_DIR
    ANALYZER --> KG_CORE
    KG_CORE --> FOUNDATIONAL
    DRAFT_PROCESSOR --> DRAFT_PROC
    DRAFT_PROC --> ENTITY_EXTRACT
    DRAFT_PROC --> FACT_EXTRACT
```

## Implementation Details

### 1. New API Endpoints

#### `/api/upload-fact-draft` (POST)
- **Purpose**: Handle fact statement draft uploads with enhanced processing
- **Input**: Multipart form with `file` field
- **Processing**: 
  - Stores file in `uploads/fact_drafts/` directory
  - Applies enhanced legal fact extraction
  - Marks entities as foundational with high confidence (0.9)
  - Integrates with knowledge graph using high-priority categorization
- **Output**: JSON response with upload details and draft analysis

#### `/api/upload-case-draft` (POST)
- **Purpose**: Handle case/complaint draft uploads with legal issue extraction
- **Input**: Multipart form with `file` field
- **Processing**:
  - Stores file in `uploads/case_drafts/` directory
  - Extracts legal issues, claims, and parties
  - Marks entities as foundational with high confidence (0.9)
  - Integrates with knowledge graph using priority processing
- **Output**: JSON response with upload details and draft analysis

### 2. Enhanced Document Processing Functions

#### `_process_draft_document(content, metadata, draft_type)`
- Enhanced processing for draft documents with foundational categorization
- Applies confidence boost (+0.2) for draft-sourced entities
- Uses specialized system prompts for legal entity extraction
- Returns structured analysis with legal entities, facts, and issues

#### `_aggregate_draft_documents(draft_list, draft_type)`
- Aggregates multiple draft documents into unified fact base
- Deduplicates entities and facts across multiple drafts
- Combines content while maintaining source relationships
- Returns aggregated data with entity counts and confidence scores

#### `_ingest_to_knowledge_graph(entities, metadata)`
- Integrates draft entities into knowledge graph with high confidence
- Uses actual knowledge graph API when available
- Falls back to simulation mode if knowledge graph unavailable
- Marks draft-sourced entities as "foundational"

### 3. Storage Organization

```
uploads/
├── fact_drafts/          # Fact statement draft documents
│   └── fact_draft_[timestamp]_[filename]
├── case_drafts/          # Case/complaint draft documents
│   └── case_draft_[timestamp]_[filename]
└── [regular uploads]     # Standard evidence documents
```

### 4. Enhanced Maestro Integration

The Enhanced Maestro now includes specialized draft processing capabilities:

#### `process_draft_documents(draft_documents, session_id)`
- Processes draft documents with priority before general evidence processing
- Separates fact drafts and case drafts for specialized handling
- Updates workflow state with foundational information

#### `_process_fact_statement_drafts(fact_drafts, session_id)`
- Aggregates multiple fact statement drafts
- Extracts structured legal facts with high confidence
- Stores foundational knowledge in knowledge graph

#### `_process_case_complaint_drafts(case_drafts, session_id)`
- Processes case/complaint drafts for legal issues and claims
- Extracts parties, legal issues, and claims
- Categorizes and deduplicates legal elements

### 5. Knowledge Graph Integration

#### Enhanced Entity Storage
- Draft-sourced entities marked as "foundational"
- Higher confidence scores (0.8-0.9) for draft content
- Special categorization for priority processing
- Integration with existing knowledge graph schema

#### Entity Types Supported
- **PARTY**: Legal parties extracted from drafts
- **DATE**: Important dates and deadlines
- **LEGAL_ISSUE**: Claims and causes of action
- **FACT**: Foundational facts from fact statements

### 6. Priority Processing Logic

1. **Draft Document Detection**: System identifies draft documents by upload endpoint
2. **Priority Queue**: Draft documents processed before general evidence
3. **Foundational Marking**: Draft content marked as foundational with high confidence
4. **Knowledge Graph Priority**: Draft entities stored with priority categorization
5. **Workflow Context**: Draft processing results feed into workflow context

## API Response Formats

### Fact Draft Upload Response
```json
{
  "success": true,
  "upload_id": "fact_draft_1734258123456_statement.pdf",
  "original_filename": "statement.pdf",
  "filename": "/path/to/uploads/fact_drafts/fact_draft_1734258123456_statement.pdf",
  "document_type": "fact_statement_draft",
  "draft_analysis": {
    "draft_type": "fact_statement",
    "confidence_boost": 0.2,
    "foundational": true,
    "legal_entities": [...],
    "key_facts": [...],
    "summary": "..."
  },
  "evidence_row": {
    "upload_id": "fact_draft_1734258123456_statement.pdf",
    "document_type": "fact_statement_draft",
    "priority": "foundational",
    "knowledge_graph_result": {...}
  },
  "processing_priority": "foundational"
}
```

### Case Draft Upload Response
```json
{
  "success": true,
  "upload_id": "case_draft_1734258123456_complaint.pdf",
  "original_filename": "complaint.pdf", 
  "filename": "/path/to/uploads/case_drafts/case_draft_1734258123456_complaint.pdf",
  "document_type": "case_complaint_draft",
  "draft_analysis": {
    "draft_type": "case_complaint",
    "legal_issues": [...],
    "parties": [...],
    "claims": [...],
    "foundational": true
  },
  "evidence_row": {
    "upload_id": "case_draft_1734258123456_complaint.pdf",
    "document_type": "case_complaint_draft", 
    "priority": "foundational",
    "knowledge_graph_result": {...}
  },
  "processing_priority": "foundational"
}
```

## Error Handling

- **File Validation**: Ensures uploaded files are valid and processable
- **Storage Errors**: Handles directory creation and file storage issues
- **Processing Failures**: Graceful degradation when analysis fails
- **Knowledge Graph Failures**: Fallback to simulation mode when KG unavailable
- **Content Extraction**: Robust handling of various file formats

## Testing

The implementation includes a comprehensive test script (`test_draft_endpoints.py`) that validates:

1. **Fact Draft Upload**: Tests `/api/upload-fact-draft` endpoint
2. **Case Draft Upload**: Tests `/api/upload-case-draft` endpoint  
3. **Evidence Table Integration**: Verifies draft documents appear in evidence table
4. **Server Connectivity**: Validates server availability and response format

## Deployment Considerations

### Directory Creation
- Draft directories are automatically created on server startup
- Proper permissions must be set for file storage
- Consider backup strategies for draft documents

### Performance
- Draft processing has priority but should not block regular uploads
- Consider async processing for large draft documents
- Monitor knowledge graph performance with high-confidence entities

### Security
- Validate file types and sizes for draft uploads
- Sanitize file names and content
- Implement access controls for draft documents

## Future Enhancements

1. **Advanced NER**: Integration with spaCy or transformer-based NER for better entity extraction
2. **Relationship Discovery**: Automated relationship discovery between draft entities
3. **Conflict Resolution**: Logic to handle conflicting information between drafts
4. **Version Control**: Track multiple versions of draft documents
5. **Collaborative Editing**: Support for collaborative draft editing and review

## Integration Points

### Frontend Integration
- Frontend UI expects these endpoints to be available
- Response format must match frontend expectations
- Error responses should provide actionable feedback

### Knowledge Graph Integration
- Uses existing knowledge graph schema and extensions
- Maintains backward compatibility with existing entity storage
- Supports both database-backed and JSON-based knowledge graphs

### Enhanced Maestro Integration
- Draft processing integrates with existing workflow phases
- Foundational entities feed into research and drafting phases
- Priority processing ensures draft content is available early in workflow

## Conclusion

This implementation provides robust backend support for draft document processing, enabling the Facts Matrix & Statement of Facts Generation workflow while maintaining compatibility with existing system components. The modular design allows for easy extension and enhancement as requirements evolve.