# LawyerFactory User Guide & Troubleshooting Manual

## Table of Contents

### [🏁 Getting Started](#getting-started)
- [System Requirements](#system-requirements)
- [Quick Launch](#quick-launch)
- [First-Time Setup](#first-time-setup)
- [Accessing the System](#accessing-the-system)

### [🤖 Understanding the Agent Swarm](#understanding-the-agent-swarm)
- [The 7-Agent Architecture](#the-7-agent-architecture)
- [Agent Roles & Responsibilities](#agent-roles-responsibilities)
- [Workflow Phases](#workflow-phases)
- [Agent Communication](#agent-communication)

### [⚙️ System Components](#system-components)
- [Backend API Server](#backend-api-server)
- [Frontend Web Interface](#frontend-web-interface)
- [Storage Systems](#storage-systems)
- [Vector Databases](#vector-databases)
- [Knowledge Graph](#knowledge-graph)

### [🔧 Configuration & Customization](#configuration-customization)
- [Environment Variables](#environment-variables)
- [Agent Configuration](#agent-configuration)
- [LLM Provider Setup](#llm-provider-setup)
- [Legal Research APIs](#legal-research-apis)

### [📊 Using LawyerFactory](#using-lawyerfactory)
- [Case Intake Process](#case-intake-process)
- [Document Processing](#document-processing)
- [Research Integration](#research-integration)
- [Quality Assurance](#quality-assurance)

### [🔍 Monitoring & Health Checks](#monitoring-health-checks)
- [System Status](#system-status)
- [Agent Health](#agent-health)
- [Performance Metrics](#performance-metrics)
- [Log Files](#log-files)

### [🛠️ Troubleshooting](#troubleshooting)
- [Launch Issues](#launch-issues)
- [Agent Communication Problems](#agent-communication-problems)
- [API Connection Errors](#api-connection-errors)
- [Performance Issues](#performance-issues)
- [Storage Problems](#storage-problems)

### [🚀 Advanced Usage](#advanced-usage)
- [Custom Workflows](#custom-workflows)
- [Batch Processing](#batch-processing)
- [API Integration](#api-integration)
- [Scaling Strategies](#scaling-strategies)

---

## 🏁 Getting Started

### System Requirements

**Minimum Requirements:**
- **Operating System**: macOS 10.15+, Ubuntu 18.04+, Windows 10/11 (WSL2)
- **Python**: Version 3.8 or higher
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free disk space
- **Network**: Stable internet connection for LLM APIs

**Recommended Setup:**
- **Python**: 3.11+ for optimal performance
- **Memory**: 16GB+ RAM for concurrent workflows
- **Storage**: SSD with 50GB+ free space
- **Network**: High-speed internet (25Mbps+) for research APIs

### Quick Launch

The fastest way to get LawyerFactory running:

```bash
# Make launch script executable
chmod +x launch.sh

# Launch with defaults
./launch.sh
```

**Expected Output:**
```
[INFO] Setting up directory structure...
[SUCCESS] Directory structure ready
[INFO] Setting up Python environment...
[SUCCESS] Python environment ready
[INFO] LawyerFactory Enhanced Launch Script v1.0.0
[SUCCESS] All checks completed successfully
[INFO] 🎉 LawyerFactory is now running!
[SUCCESS] Backend API: http://127.0.0.1:5000/api/health
[SUCCESS] Frontend UI: http://127.0.0.1:8000/apps/ui/templates/consolidated_factory.html
```

### First-Time Setup

1. **Clone and Navigate:**
   ```bash
   git clone <repository-url>
   cd lawyerfactory
   ```

2. **Configure API Keys:**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit with your API keys
   nano .env
   ```

3. **Required API Keys:**
   ```bash
   # Choose at least one LLM provider
   OPENAI_API_KEY=sk-your-openai-key-here
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
   GROQ_API_KEY=gsk-your-groq-key-here

   # Legal research (optional but recommended)
   COURTLISTENER_API_KEY=your-courtlistener-key-here
   ```

4. **Launch System:**
   ```bash
   ./launch.sh
   ```

### Accessing the System

**Web Interface:**
- **Main UI**: http://127.0.0.1:8000/apps/ui/templates/consolidated_factory.html
- **API Documentation**: http://127.0.0.1:5000/docs
- **Health Check**: http://127.0.0.1:5000/api/health

**System will automatically open your browser to the main interface.**

---

## 🤖 Understanding the Agent Swarm

### The 7-Agent Architecture

LawyerFactory operates through a coordinated swarm of 7 specialized AI agents:

```
🎯 MAESTRO (Central Coordinator)
├── 📖 READER (Document Intake)
├── 🔍 RESEARCHER (Legal Research)
├── 📋 OUTLINER (Case Structure)
├── ✍️ WRITER (Document Drafting)
├── 🔧 EDITOR (Quality Assurance)
├── ⚖️ PARALEGAL (Jurisdiction & Evidence)
└── 📄 LEGAL FORMATTER (Citation & Formatting)
```

### Agent Roles & Responsibilities

#### **🎯 Maestro - Central Coordinator**
**What it does:** Orchestrates the entire workflow, manages agent communication, ensures quality standards.

**How it works:**
- Receives case intake from Reader
- Assigns research tasks to Researcher
- Coordinates with Outliner for case structure
- Oversees Writer and Editor collaboration
- Manages final review by Paralegal and Legal Formatter

**Common Issues:**
- If Maestro fails, entire workflow stops
- Check agent communication logs for coordination errors

#### **📖 Reader - Document Intake**
**What it does:** Processes client documents, extracts key facts, categorizes evidence.

**How it works:**
- Accepts uploaded documents (PDF, DOCX, TXT)
- Uses OCR for scanned documents
- Extracts entities (names, dates, amounts)
- Categorizes document types
- Feeds structured data to Maestro

**Common Issues:**
- Document parsing errors with complex PDFs
- OCR failures on poor quality scans
- Character encoding problems with special characters

#### **🔍 Researcher - Legal Research**
**What it does:** Performs comprehensive legal research using external APIs and internal knowledge.

**How it works:**
- Searches CourtListener for case law
- Queries Google Scholar for academic sources
- Analyzes precedent relevance
- Generates authority assessments
- Stores findings in vector database

**Common Issues:**
- API rate limits on CourtListener
- Authentication failures with research APIs
- Network timeouts during large searches

#### **📋 Outliner - Case Structure**
**What it does:** Creates comprehensive case outlines, identifies missing elements.

**How it works:**
- Analyzes intake data for case requirements
- Generates structured outlines with IRAC format
- Identifies evidentiary gaps
- Creates claim matrices
- Prepares drafting templates

**Common Issues:**
- Incomplete intake data causes outline gaps
- Jurisdiction-specific formatting requirements
- Complex multi-party case structures

#### **✍️ Writer - Document Drafting**
**What it does:** Generates professional legal documents using research and templates.

**How it works:**
- Applies Law of Threes methodology
- Integrates research findings
- Uses Jinja2 templates
- Generates multiple document sections
- Maintains consistent legal language

**Common Issues:**
- Template rendering errors
- Research integration conflicts
- LLM API rate limits during drafting

#### **🔧 Editor - Quality Assurance**
**What it does:** Reviews and refines document content for accuracy and coherence.

**How it works:**
- Performs style and grammar checks
- Validates legal accuracy
- Ensures factual consistency
- Requests additional research if needed
- Provides detailed feedback to Writer

**Common Issues:**
- False positives in legal accuracy checks
- Style guide conflicts
- Feedback loop deadlocks

#### **⚖️ Paralegal - Jurisdiction & Evidence**
**What it does:** Ensures procedural compliance and evidence organization.

**How it works:**
- Validates jurisdictional requirements
- Tags evidence with metadata
- Organizes discovery materials
- Ensures procedural timelines
- Prepares evidence matrices

**Common Issues:**
- Jurisdiction database updates
- Evidence chain of custody tracking
- Timeline calculation errors

#### **📄 Legal Formatter - Citation & Formatting**
**What it does:** Applies proper legal citation and formatting standards.

**How it works:**
- Formats citations (Bluebook, ALWD, APA)
- Applies court-specific formatting
- Generates tables of contents
- Creates table of authorities
- Ensures pagination and headers

**Common Issues:**
- Citation style inconsistencies
- Court rule updates
- Complex citation hierarchies

### Workflow Phases

LawyerFactory processes cases through 9 distinct phases:

1. **Preproduction Planning** - Initial case assessment
2. **Research and Development** - Legal research and precedent analysis
3. **Organization/Database Building** - Evidence organization and indexing
4. **1st Pass All Parts** - Initial document drafting
5. **Combining** - Integration of research and drafting
6. **Editing** - Content refinement and quality improvement
7. **2nd Pass** - Comprehensive review and revision
8. **Human Feedback** - Attorney review integration
9. **Final Draft** - Court-ready document production

### Agent Communication

**Communication Protocol:**
- **Real-time**: Socket.IO for instant messaging
- **Task Assignment**: Structured workflow tasks with dependencies
- **Status Updates**: Continuous health and progress reporting
- **Error Handling**: Graceful failure recovery and retries

**Communication Flow:**
```
Reader → Maestro → Researcher
Maestro → Outliner → Writer
Writer → Editor → Maestro
Maestro → Paralegal → Legal Formatter
```

---

## ⚙️ System Components

### Backend API Server

**Technology:** Flask + Socket.IO
**Port:** 5000 (configurable)
**Purpose:** Handles all business logic, agent coordination, API endpoints

**Key Endpoints:**
- `/api/health` - System health check
- `/api/workflow/start` - Initiate new workflow
- `/api/agents/status` - Agent status monitoring
- `/api/documents/upload` - Document intake
- `/api/research/search` - Legal research queries

### Frontend Web Interface

**Technology:** HTML5 + JavaScript + Socket.IO
**Port:** 8000 (configurable)
**Purpose:** User interface for case management and monitoring

**Features:**
- Real-time workflow monitoring
- Document upload interface
- Agent status dashboard
- Research results visualization
- Generated document preview

### Storage Systems

**Multi-tier Storage Architecture:**

1. **Local File System**
   - Document uploads: `./uploads/`
   - Generated documents: `./output/`
   - Temporary files: `./data/temp/`

2. **Vector Database**
   - Technology: Qdrant or Weaviate
   - Purpose: Semantic search and RAG
   - Content: Document embeddings, research results

3. **Relational Storage**
   - Technology: SQLite (default) or PostgreSQL
   - Purpose: Structured data and metadata
   - Content: Case information, agent logs, user data

### Vector Databases

**Purpose:** Enable semantic search and retrieval-augmented generation (RAG)

**Supported Systems:**
- **Qdrant**: High-performance vector search
- **Weaviate**: Graph-based vector storage
- **Chroma**: Lightweight embedded option

**Configuration:**
```bash
# Environment variables
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key
VECTOR_DB_TYPE=qdrant
```

### Knowledge Graph

**Purpose:** Structured representation of legal concepts, relationships, and workflows

**Components:**
- **Entity Extraction**: Identifies legal entities from documents
- **Relationship Mining**: Discovers connections between legal concepts
- **Knowledge Storage**: Graph database for complex queries
- **Inference Engine**: Derives new knowledge from existing relationships

---

## 🔧 Configuration & Customization

### Environment Variables

**Core Configuration:**
```bash
# Server Configuration
FRONTEND_PORT=8000
BACKEND_PORT=5000
HOST=127.0.0.1

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs/

# Performance
MAX_WORKERS=4
MEMORY_LIMIT=8GB
```

**AI Provider Configuration:**
```bash
# Primary LLM (choose one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk-...

# Fallback providers
SECONDARY_LLM_PROVIDER=anthropic
TERTIARY_LLM_PROVIDER=groq

# Model selection
DEFAULT_MODEL=gpt-4
FALLBACK_MODEL=claude-3-sonnet
```

### Agent Configuration

**Agent-specific Settings:**
```python
agent_config = {
    "maestro": {
        "coordination_mode": "parallel",
        "quality_threshold": 0.85,
        "max_retries": 3,
        "timeout_seconds": 300
    },
    "researcher": {
        "courtlistener_enabled": True,
        "google_scholar_enabled": True,
        "max_sources_per_query": 10,
        "authority_filter": "binding_only"
    },
    "writer": {
        "template_engine": "jinja2",
        "citation_style": "bluebook",
        "law_of_threes_enabled": True,
        "draft_iterations": 2
    }
}
```

### LLM Provider Setup

**Multi-Provider Strategy:**
1. **Primary**: OpenAI GPT-4 (highest quality)
2. **Secondary**: Anthropic Claude (good quality, cost-effective)
3. **Tertiary**: Groq (fast, budget option)

**Automatic Fallback Logic:**
- If primary fails → try secondary
- If secondary fails → try tertiary
- If all fail → graceful degradation with cached responses

### Legal Research APIs

**CourtListener Integration:**
```python
courtlistener_config = {
    "api_key": "your-key",
    "base_url": "https://www.courtlistener.com/api/rest/v3",
    "rate_limit": 100,  # requests per minute
    "timeout": 30
}
```

**Google Scholar Integration:**
```python
scholar_config = {
    "enabled": True,
    "max_results": 20,
    "date_range": "5years",
    "jurisdiction_filter": "federal"
}
```

---

## 📊 Using LawyerFactory

### Case Intake Process

1. **Document Upload:**
   - Drag & drop or click to upload
   - Supported formats: PDF, DOCX, TXT, RTF
   - Maximum file size: 50MB per document

2. **Case Information:**
   - Client details (name, contact, representation)
   - Opposing party information
   - Case description and claims
   - Jurisdiction and court information

3. **Evidence Organization:**
   - Automatic categorization
   - Metadata extraction
   - Timeline reconstruction

### Document Processing

**Processing Pipeline:**
1. **Intake** → Reader agent processes documents
2. **Research** → Researcher gathers legal precedents
3. **Outline** → Outliner creates case structure
4. **Draft** → Writer generates initial documents
5. **Review** → Editor refines content
6. **Format** → Legal Formatter applies citations

### Research Integration

**Research Sources:**
- **Primary Law**: Case law from CourtListener
- **Secondary Sources**: Law review articles, treatises
- **Statutory Law**: Relevant statutes and regulations
- **Procedural Rules**: Court rules and local rules

**Research Quality:**
- Authority scoring (binding vs. persuasive)
- Recency weighting (newer cases preferred)
- Citation count analysis
- Jurisdictional relevance

### Quality Assurance

**Multi-layer Review:**
1. **Automated Checks**: Grammar, style, consistency
2. **Legal Accuracy**: Precedent application validation
3. **Factual Verification**: Evidence citation accuracy
4. **Procedural Compliance**: Court rule adherence

---

## 🔍 Monitoring & Health Checks

### System Status

**Health Check Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-07T19:30:00Z",
  "version": "2.1.0",
  "components": {
    "backend": "healthy",
    "frontend": "healthy",
    "database": "healthy",
    "agents": "healthy"
  }
}
```

### Agent Health

**Individual Agent Status:**
```json
{
  "maestro": {
    "status": "active",
    "tasks_completed": 15,
    "current_task": "coordinating_research",
    "health_score": 0.98
  },
  "researcher": {
    "status": "busy",
    "tasks_completed": 23,
    "current_task": "courtlistener_search",
    "health_score": 0.95
  }
}
```

### Performance Metrics

**Key Metrics:**
- **Throughput**: Cases processed per hour
- **Latency**: Average processing time per phase
- **Success Rate**: Percentage of successful completions
- **Error Rate**: Percentage of failed operations

**Monitoring Dashboard:**
- Real-time metrics via Grafana
- Historical trends and analytics
- Alert system for anomalies
- Performance bottleneck identification

### Log Files

**Log Locations:**
- **Application Logs**: `./logs/lawyerfactory.log`
- **Agent Logs**: `./logs/agents/`
- **API Logs**: `./logs/api/`
- **Error Logs**: `./logs/errors/`

**Log Levels:**
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARN**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical system failures

---

## 🛠️ Troubleshooting

### Launch Issues

#### **"Python not found" Error**
**Symptoms:** Launch script fails with Python detection error
**Solutions:**
```bash
# Check Python installation
python3 --version

# Install Python 3.8+ if missing
# macOS
brew install python@3.11

# Ubuntu
sudo apt install python3.11

# Verify PATH
which python3
```

#### **Port Already in Use**
**Symptoms:** "Port 5000/8000 already in use"
**Solutions:**
```bash
# Find process using port
lsof -i :5000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different ports
./launch.sh --frontend-port 3000 --backend-port 8080
```

#### **Permission Denied**
**Symptoms:** "Permission denied" when running launch.sh
**Solutions:**
```bash
# Make script executable
chmod +x launch.sh

# Check file permissions
ls -la launch.sh
```

### Agent Communication Problems

#### **Agent Not Responding**
**Symptoms:** Agent shows as "unhealthy" or "disconnected"
**Solutions:**
1. Check agent logs: `tail -f logs/agents/<agent_name>.log`
2. Restart specific agent via API
3. Verify network connectivity
4. Check resource usage (memory/CPU)

#### **Workflow Stuck**
**Symptoms:** Workflow progress stops at specific phase
**Solutions:**
1. Check agent status: `GET /api/agents/status`
2. Review workflow logs for errors
3. Restart stuck agent
4. Check dependencies and prerequisites

### API Connection Errors

#### **LLM API Failures**
**Symptoms:** "API key invalid" or "Rate limit exceeded"
**Solutions:**
```bash
# Verify API keys in .env
cat .env | grep API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Check rate limits
# OpenAI: 10,000 RPM for GPT-4
# Anthropic: 50 requests/minute
```

#### **Research API Issues**
**Symptoms:** CourtListener/Google Scholar connection failures
**Solutions:**
1. Verify API keys are valid
2. Check network connectivity
3. Review API rate limits
4. Try alternative research sources

### Performance Issues

#### **Slow Processing**
**Symptoms:** Workflows taking longer than expected
**Solutions:**
1. Check system resources: `top` or `htop`
2. Monitor memory usage
3. Reduce concurrent workflows
4. Optimize LLM model selection (use faster models)

#### **Memory Issues**
**Symptoms:** Out of memory errors
**Solutions:**
```bash
# Check memory usage
free -h  # Linux
vm_stat  # macOS

# Increase system memory
# Or reduce batch sizes in configuration

# Monitor for memory leaks
ps aux --sort=-%mem | head
```

### Storage Problems

#### **Database Connection Issues**
**Symptoms:** "Database connection failed"
**Solutions:**
1. Verify database service is running
2. Check connection string in .env
3. Test database connectivity
4. Check disk space: `df -h`

#### **File Upload Failures**
**Symptoms:** Documents fail to upload
**Solutions:**
1. Check upload directory permissions
2. Verify file size limits
3. Check available disk space
4. Review file format support

---

## 🚀 Advanced Usage

### Custom Workflows

**Creating Custom Workflow Templates:**
```python
from src.lawyerfactory.workflows import WorkflowTemplate

# Define custom workflow
custom_workflow = WorkflowTemplate(
    name="complex_litigation",
    phases=[
        "intake",
        "preliminary_research",
        "expert_consultation",
        "motion_drafting",
        "discovery_planning",
        "trial_preparation"
    ],
    agent_assignments={
        "preliminary_research": ["researcher", "paralegal"],
        "expert_consultation": ["researcher", "maestro"],
        "motion_drafting": ["writer", "editor", "legal_formatter"]
    }
)
```

### Batch Processing

**Processing Multiple Cases:**
```python
from src.lawyerfactory.batch import BatchProcessor

# Initialize batch processor
batch_processor = BatchProcessor(max_concurrent=3)

# Process multiple cases
cases = [
    {"id": "case_001", "data": case_data_1},
    {"id": "case_002", "data": case_data_2},
    {"id": "case_003", "data": case_data_3}
]

results = await batch_processor.process_batch(cases)
```

### API Integration

**REST API Usage:**
```python
import requests

# Start new workflow
response = requests.post(
    "http://localhost:5000/api/workflow/start",
    json={
        "case_data": {
            "client_name": "John Doe",
            "case_type": "breach_of_contract",
            "jurisdiction": "California"
        }
    }
)

workflow_id = response.json()["workflow_id"]

# Monitor progress
status = requests.get(f"http://localhost:5000/api/workflow/{workflow_id}/status")
```

### Scaling Strategies

**Horizontal Scaling:**
```python
# Deploy multiple agent instances
agent_instances = {
    "research_pool": ["researcher_1", "researcher_2", "researcher_3"],
    "writing_pool": ["writer_1", "writer_2"],
    "review_pool": ["editor_1", "editor_2"]
}

# Load balancer configuration
load_balancer = LoadBalancer(
    pools=agent_instances,
    strategy="round_robin",
    health_check_interval=30
)
```

**Performance Optimization:**
```python
optimization_config = {
    "caching": {
        "redis_enabled": True,
        "cache_ttl": 3600,
        "cache_strategy": "lru"
    },
    "async_processing": {
        "enabled": True,
        "max_workers": 8,
        "queue_size": 100
    },
    "resource_limits": {
        "max_memory_per_agent": "2GB",
        "cpu_quota": 2.0,
        "timeout": 600
    }
}
```

---

## 📞 Support & Resources

### Getting Help

**Community Support:**
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community questions and troubleshooting
- **Documentation**: Comprehensive guides and tutorials

**Professional Support:**
- **Enterprise Support**: Commercial support options
- **Training**: Professional training programs
- **Consulting**: Implementation and customization services

### Additional Resources

**Learning Materials:**
- **[API Documentation](docs/api/)** - Complete API reference
- **[Developer Guide](docs/development/)** - Setup and contribution guidelines
- **[Integration Guide](docs/integrations/)** - External system integrations

**Tools & Utilities:**
- **Health Check Script**: `./scripts/health_check.py`
- **Log Analyzer**: `./scripts/analyze_logs.py`
- **Performance Monitor**: `./scripts/performance_monitor.py`

---

*This guide serves as your comprehensive companion for understanding, using, and troubleshooting LawyerFactory. For the latest updates and additional resources, visit our [documentation site](docs/).*