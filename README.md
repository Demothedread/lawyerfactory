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

1. **01_intake** - Document ingestion and initial processing
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

### Management
- `GET /api/workflow/{id}` - Workflow status
- `POST /api/workflow` - Start new workflow
- `GET /api/health` - System health check

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