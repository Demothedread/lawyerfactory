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
│   ├── storage/              # File and data storage
│   ├── messaging/            # Event system and notifications
│   └── monitoring/           # Logging and metrics
├── knowledge_graph/          # Legal knowledge representation
├── config/                   # Configuration management
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