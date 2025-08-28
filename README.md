# LawyerFactory - Legal Document Processing System

## Overview

LawyerFactory is an advanced AI-powered legal document processing system that orchestrates the complete workflow from document intake through final legal document generation. The system uses a sophisticated 7-phase workflow to transform raw legal documents into attorney-ready legal products.

## Key Features

- **📥 Intelligent Document Intake**: Automated document classification and evidence extraction
- **🔍 Advanced Legal Research**: CourtListener API integration with academic legal databases
- **📋 Claims Matrix Analysis**: Comprehensive cause-of-action identification and analysis
- **⚖️ Interactive Legal Analysis**: Attorney-guided decision tree analysis
- **✍️ AI-Powered Drafting**: Context-aware legal document generation
- **👥 Human Review Integration**: Seamless attorney collaboration workflows
- **📄 Post-Production Processing**: Automated formatting, citation management, and compliance checking
- **🎯 Orchestration Engine**: Coordinated multi-agent workflow management
- **🧠 Multi-Purpose Vector Stores**: Specialized vector databases for evidence, case law, and RAG
- **🔍 Semantic Search & RAG**: Retrieval-augmented generation with context-aware LLM integration
- **📊 Validation Type Filtering**: User-selectable validation criteria with sub-vector creation
- **⚡ Real-time Vector Processing**: Automated evidence ingestion with tokenization
- **🎨 Retro Mechanical UI**: Eastern European mechanical punk aesthetic with interactive controls

## Architecture

### Core Workflow Phases

The system follows a sequential 7-phase workflow:

1. **phaseA01_intake** - Document ingestion and initial processing
2. **02_research** - Legal research and authority identification
3. **03_outline** - Claims analysis and case structuring
4. **04_human_review** - Attorney review and feedback integration
5. **05_drafting** - Legal document generation
6. **06_post_production** - Formatting and compliance
7. **07_orchestration** - Workflow coordination and state management

### Component Organization

```
/src/lawyerfactory/
├── phases/                    # Sequential workflow phases
├── agents/                    # Specialized AI agents by function
│   ├── research/             # Legal research agents
│   ├── drafting/             # Document drafting agents
│   ├── analysis/             # Claims analysis agents
│   └── review/               # Review and validation agents
├── infrastructure/           # Technical infrastructure
│   ├── storage/              # Object/blob storage (S3 or local dir) and data storage
│   ├── messaging/            # Event system and notifications
├── vectors/                   # Vector storage and retrieval system
│   ├── enhanced_vector_store.py # Multi-purpose vector store manager
│   ├── evidence_ingestion.py    # Automated evidence ingestion pipeline
│   ├── research_integration.py  # Research rounds integration
│   ├── llm_rag_integration.py   # LLM RAG functionality
│   ├── ui_components.py         # UI components for vector controls
│   └── memory_compression.py    # MCP memory compression system
│   └── monitoring/           # Logging and metrics
├── knowledge_graph/          # Legal knowledge representation
├── config/                   # Configuration management
### Vector Store System

The system includes a sophisticated multi-purpose vector storage system:

#### Specialized Vector Stores
- **Primary Evidence Store**: For Statement of Facts construction and evidence management
- **Case Opinions Store**: For knowledge graph integration and legal precedent storage
- **General RAG Store**: For semantic search and LLM augmentation
- **Validation Sub-Vectors**: Filtered collections for specific validation types

#### Key Capabilities
- **Automated Evidence Ingestion**: Tokenizes and stores text from intake/research phases
- **Research Rounds Integration**: Accumulates knowledge across research iterations
- **Semantic Search & RAG**: Retrieval-augmented generation with context-aware LLM integration
- **Validation Type Filtering**: User-selectable validation criteria (default: "complaints against tesla")
- **Real-time Processing**: Automated vectorization with caching and optimization
- **IRAC/IR{C}C Format Support**: Structured legal writing with vector-enhanced context
- **Directory-Based Keys for Evidence**: Uploaded files are stored with directory-like prefixes (store/case_id/YYYY/MM/uuid_filename) in S3 or a local uploads folder; vectors reference the blob via `blob_key` and `blob_locator`.

#### UI Integration
- **Validation Type Selector**: Dropdown for choosing validation types with descriptions
- **Vector Store Status**: Real-time metrics and health indicators
- **Activity Monitoring**: Live updates on evidence ingestion and processing
- **Retro Mechanical Design**: Eastern European mechanical punk aesthetic with interactive controls
└── shared/                   # Common utilities and base classes
```

## Quick Start

### Prerequisites

- Python 3.8+
- Qdrant vector database
- OpenAI API key (for AI features)
- CourtListener API token (for legal research)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lawyerfactory
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Initialize the system**
   ```bash
   python -m src.lawyerfactory
   ```

### Basic Usage

```python
from src.lawyerfactory.phases.intake.intake_processor import IntakeProcessor
from src.lawyerfactory.phases.orchestration.maestro import Maestro

# Initialize the system
maestro = Maestro()

# Process a legal document
result = await maestro.process_document("path/to/legal/document.pdf")
```

## Documentation

- **[Architecture Guide](docs/architecture/)** - System design and data models
- **[API Reference](docs/api/)** - Complete API documentation
- **[Development Guide](docs/development/)** - Setup and contribution guidelines
- **[User Manual](docs/guides/user_manual.md)** - End-user documentation

## Development

### Project Structure

- **Source Code**: `src/lawyerfactory/`
- **Tests**: `tests/`
- **Documentation**: `docs/`
- **Configuration**: `configs/`
- **Tools**: `tools/`

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Code Organization

The codebase follows these principles:

### Vector Store APIs
- `POST /api/vector-store/ingest` - Ingest evidence into vector stores
- `POST /api/vector-store/ingest-file` - Upload a file; stores in S3/local and indexes extracted text
- `POST /api/vector-store/search` - Perform semantic search across stores
- `GET /api/vector-store/status` - Get vector store metrics and health
- `POST /api/vector-store/apply-validation-filter` - Apply validation type filtering
- `POST /api/vector-store/rag-context` - Get RAG context for LLM augmentation
- `GET /api/vector-store/validation-types` - List available validation types
1. **Phase-based workflow**: Clear sequential processing steps
2. **Functional agent grouping**: Agents organized by purpose (research, drafting, etc.)
3. **Infrastructure consolidation**: All technical components in one place
4. **Shared utilities**: Common functionality centralized
5. **Clean separation**: Clear boundaries between components

## API Endpoints

### Core Processing
- `POST /api/intake` - Document intake and classification
- `POST /api/research` - Legal research and authority identification
- `POST /api/analyze` - Claims matrix analysis
- `POST /api/draft` - Document generation
- `POST /api/review` - Human review integration

### Document Storage & Retrieval
- `POST /api/upload` - General document upload with unified storage
- `POST /api/upload-fact-draft` - Fact statement draft upload
- `POST /api/upload-case-draft` - Case complaint draft upload
- `POST /mcp/search` - Multi-tier document search across storage sources
- `GET /mcp/fetch?id={file_id}` - Document retrieval from unified storage
- `GET /uploads/{name}` - Direct file serving with storage fallback
- `GET /api/health/storage` - Storage system health check

### Management
- `GET /api/workflow/{id}` - Workflow status
- `POST /api/workflow` - Start new workflow
- `GET /api/health` - System health check

## Unified Storage Integration

### Overview

The LawyerFactory ingestion system now includes a robust Unified Storage API integration that provides enterprise-grade document storage, retrieval, and search capabilities with comprehensive fallback mechanisms.

### Key Features

#### 🔧 Storage Architecture
- **Primary Storage**: Unified Storage API with support for multiple storage backends (S3, Azure, local)
- **Fallback Storage**: Local filesystem storage when unified storage is unavailable
- **Transparent Operation**: Applications continue to work regardless of storage backend availability

#### 📤 Enhanced Upload Handlers
- `handle_upload()`: General document uploads with unified storage and local fallback
- `handle_upload_fact_draft()`: Fact statement draft uploads with metadata tracking
- `handle_upload_case_draft()`: Case complaint draft uploads with enhanced processing
- All handlers include automatic fallback to local storage on unified storage failure

#### 🔍 Multi-Tier Search & Retrieval
- `handle_search()`: Searches across unified storage, OpenAI vector store, and local index
- `handle_fetch()`: Unified retrieval from multiple storage sources with fallback
- `handle_uploaded_file()`: HTTP file serving with unified storage support

#### 🛡️ Fallback Mechanisms
- `safe_unified_storage_operation()`: Wrapper for safe storage operations
- `_upload_fallback()`: Local storage fallback for uploads
- `_retrieve_fallback()`: Local storage fallback for retrievals
- `_search_fallback()`: Local vector backup fallback for searches
- `check_unified_storage_health()`: Real-time health monitoring

#### 📊 Health Monitoring
- `/api/health/storage` endpoint for comprehensive storage system health checks
- Real-time monitoring of unified storage availability and performance
- Automatic fallback activation on storage system issues

### Storage Hierarchy
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Unified Storage│───▶│  Local Storage  │───▶│  Error Handling │
│     (Primary)   │    │   (Fallback)    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Usage Examples

#### Upload Document with Fallback
```python
# The system automatically tries unified storage first
response = await handle_upload(request)

# Response includes storage information
{
    "success": True,
    "upload_id": "file_123",
    "storage_info": {
        "storage_type": "unified",  # or "local" for fallback
        "storage_id": "unified_file_id",
        "storage_url": "https://..."
    }
}
```

#### Search Across Multiple Sources
```python
# Searches unified storage, OpenAI, and local index
response = await handle_search(request_with_query)

# Returns aggregated results with storage type indicators
{
    "results": [
        {
            "id": "file_1",
            "title": "Document Title",
            "storage_type": "unified",
            "score": 0.85
        }
    ]
}
```

#### Health Check
```python
# Check storage system status
response = await handle_storage_health_check(request)

# Returns comprehensive health information
{
    "healthy": True,
    "reason": "Unified storage operational",
    "fallback_available": True,
    "server_status": "operational",
    "timestamp": "2025-01-01T12:00:00Z"
}
```

### Configuration

#### Environment Variables
```bash
# Unified Storage Configuration
UNIFIED_STORAGE_PATH=data/intake_storage

# Optional: OpenAI Integration
OPENAI_API_KEY=your_openai_key
VECTOR_STORE_ID=your_vector_store_id

# Optional: Qdrant Integration
QDRANT_API_KEY=your_qdrant_key
QDRANT_URL=your_qdrant_url
```

#### Directory Structure
```
data/
├── intake_storage/          # Unified storage data
├── uploads/                 # Local fallback storage
│   ├── fact_drafts/        # Fact statement drafts
│   └── case_drafts/        # Case complaint drafts
└── vectors/                # Vector storage
```

### Error Handling

#### Storage Failures
- **Unified Storage Down**: Automatic fallback to local storage
- **Local Storage Full**: Error response with clear message
- **Network Issues**: Retry logic with exponential backoff
- **Permission Errors**: Fallback to alternative storage location

#### Logging
All storage operations are logged with:
- Operation type and parameters
- Success/failure status
- Storage type used
- Error details and stack traces
- Performance metrics

### Migration Notes

#### From Legacy Storage
- Existing local files remain accessible
- No data migration required
- Unified storage becomes primary for new uploads
- Legacy files served via fallback mechanism

#### Backward Compatibility
- All existing API endpoints maintain same interface
- Response format includes additional storage metadata
- No breaking changes for existing clients

### Performance Considerations

#### Optimization Strategies
- **Caching**: Frequently accessed files cached locally
- **Chunking**: Large files processed in chunks
- **Async Operations**: Non-blocking I/O for all storage operations
- **Connection Pooling**: Reused connections for unified storage

#### Monitoring
- Storage operation latency tracking
- Success/failure rate monitoring
- Storage utilization metrics
- Fallback frequency analysis

### Security

#### Access Control
- Storage credentials encrypted
- File access logged and audited
- Secure file serving with proper headers
- Input validation and sanitization

#### Data Protection
- Files encrypted at rest (when supported by storage backend)
- Secure deletion of temporary files
- Access logging for compliance
- Regular security updates

### Future Enhancements

#### Planned Features
- **Multi-region replication**: Geographic redundancy
- **Advanced caching**: CDN integration
- **Compression**: Automatic file compression
- **Versioning**: Document version management
- **Analytics**: Storage usage analytics

#### Scalability Improvements
- **Load balancing**: Distributed storage nodes
- **Sharding**: Horizontal scaling support
- **Queue-based processing**: Async upload queues
- **Batch operations**: Bulk upload/download support

## Configuration

### Environment Variables

```bash
# AI Services
OPENAI_API_KEY=your_openai_key
QDRANT_API_KEY=your_qdrant_key

# Legal Research
COURTLISTENER_API_KEY=your_courtlistener_key

# System Configuration
WORKFLOW_STORAGE_PATH=./workflow_storage
UPLOAD_DIR=./uploads

# Object/Blob Storage (choose one)
# Option A: S3 (recommended for cloud)
LF_S3_BUCKET=your_s3_bucket_name
LF_S3_REGION=us-west-2
LF_S3_PREFIX=lawyerfactory

# Option B: Local directory (default fallback)
LF_LOCAL_UPLOAD_DIR=./uploads
```

### Advanced Configuration

See `src/lawyerfactory/config/settings.py` for detailed configuration options.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines

- Follow the existing code organization patterns
- Add type hints to new functions
- Write comprehensive tests
- Update documentation for API changes
- Use descriptive commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting guide in `docs/guides/troubleshooting.md`
- Review the FAQ in `docs/guides/faq.md`

## Changelog

### Recent Updates
- **Streamlined Organization**: Reorganized codebase for better maintainability
- **Agent Reorganization**: Grouped agents by functional purpose
- **Infrastructure Consolidation**: Unified technical components
- **Documentation Consolidation**: Centralized documentation structure

For complete changelog, see `docs/development/changelog.md`.