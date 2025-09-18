# Consolidated Storage System for LawyerFactory

This directory contains the complete consolidated storage system for LawyerFactory, implementing the triple storage architecture:

## 📁 Directory Structure

```
storage/
├── __init__.py              # Main module interface with all imports
├── core/                    # Core unified storage APIs
│   ├── unified_storage_api.py
│   ├── enhanced_unified_storage_api.py
│   └── evidence_ingestion.py
├── cloud/                   # Cloud storage components
│   ├── s3bucket_temp-serv.py    # S3 service with FastAPI
│   ├── cloud_storage_integration.py
│   ├── database_manager.py
│   └── base_repository.py
├── local/                   # Local storage utilities
├── vectors/                 # Vector storage for RAG
│   ├── enhanced_vector_store.py
│   ├── llm_rag_integration.py
│   ├── memory_compression.py
│   ├── research_integration.py
│   └── cloud_storage_integration.py
└── evidence/                # Evidence table and management
    ├── table.py
    └── shotlist.py
```

## 🏗️ Triple Storage Architecture

### 1. Local Storage (`./uploads/tmp`)

- **Purpose**: Temporary processing and immediate access
- **Implementation**: Files saved locally before cloud upload
- **Cleanup**: Automatic cleanup after configurable retention period
- **Configuration**: `UPLOAD_TMP_DIR` environment variable

### 2. Cloud Storage (AWS S3)

- **Purpose**: Permanent storage with public access
- **Implementation**: FastAPI service in `s3bucket_temp-serv.py`
- **Features**:
  - Object versioning and metadata tagging
  - Public HTTPS URLs for web access
  - Backup and recovery capabilities
  - Configurable via environment variables

### 3. Vector Storage (Qdrant/Weaviate)

- **Purpose**: Tokenized content for semantic search and RAG
- **Implementation**: `EnhancedVectorStoreManager`
- **Features**:
  - Multiple vector stores for different content types
  - Semantic search and retrieval-augmented generation
  - Integration with LLM processing pipeline

## 🔄 Storage Pipeline Flow

1. **File Upload** → Local temp storage (`./uploads/tmp`)
2. **Processing** → Vector tokenization and metadata extraction
3. **Cloud Storage** → Permanent S3 storage with public URLs
4. **Vector Storage** → Semantic indexing for RAG retrieval
5. **Evidence Table** → Structured data with user editing capabilities

## 📊 Integration Points

The storage system integrates with:

- **Evidence Table**: User-modifiable interface for claims/facts linking
- **Claims Matrix**: Structured legal element analysis
- **Shotlist**: Document organization and categorization
- **Skeletal Outline**: Hierarchical document structuring
- **Statement of Facts**: Narrative synthesis from evidence
- **Pleadings**: Legal document drafting with IRAC methodology
- **Reference Table**: Citation management and bibliography

## 🚀 Usage Examples

### Basic File Storage

```python
from lawyerfactory.storage import store_evidence_file, retrieve_evidence

# Store a file
result = await store_evidence_file(
    file_content=b"file content",
    filename="document.pdf",
    metadata={"case_id": "CASE001"},
    source_phase="intake"
)

# Retrieve the file
evidence = await retrieve_evidence(result.object_id)
```

### Evidence Table Management

```python
from lawyerfactory.storage import EnhancedEvidenceTable

table = EnhancedEvidenceTable()
evidence = table.add_evidence(evidence_entry)
```

### Vector Search

```python
from lawyerfactory.storage import search_evidence

results = await search_evidence("contract breach", search_tier="vector")
```

## ⚙️ Configuration

### Environment Variables

- `UPLOAD_TMP_DIR`: Local temp directory (default: `./uploads/tmp`)
- `AWS_ACCESS_KEY_ID`: AWS credentials
- `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `AWS_REGION`: AWS region (default: `us-west-2`)
- `S3_BUCKET`: S3 bucket name
- `LF_S3_BUCKET`: Enhanced storage S3 bucket
- `LF_S3_REGION`: Enhanced storage region
- `LF_S3_PREFIX`: S3 key prefix for organization

### Storage Tiers

- **HOT**: Frequently accessed, local storage
- **WARM**: Occasionally accessed, fast cloud storage
- **COLD**: Rarely accessed, archival storage

## 🔧 Maintenance

### Cleanup Operations

- Temp files are automatically cleaned up after 7 days
- Storage tier policies manage data lifecycle
- Object registry tracks all stored items

### Backup and Recovery

- S3 provides automatic versioning
- Cross-region replication available
- Evidence table maintains data integrity

## 📈 Performance Considerations

- **Local Storage**: Fast access for processing
- **Cloud Storage**: Scalable permanent storage
- **Vector Storage**: Optimized for semantic search
- **Caching**: Local caching reduces cloud requests
- **Compression**: Automatic compression for large files

## 🔒 Security

- AWS IAM roles for access control
- Encryption at rest and in transit
- Secure temporary file handling
- Audit logging for all operations

## 🐛 Troubleshooting

### Common Issues

1. **S3 Connection Failed**: Check AWS credentials and region
2. **Vector Store Unavailable**: Verify Qdrant/Weaviate configuration
3. **Local Storage Full**: Check disk space and cleanup policies
4. **Import Errors**: Ensure all dependencies are installed

### Debug Mode

Set `DEBUG_QDRANT=true` for detailed vector store logging
