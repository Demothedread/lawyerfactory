# LawyerFactory Automated Lawsuit Generation System

![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/framework-Flask-orange)
![OpenAI](https://img.shields.io/badge/AI-OpenAI-yellow)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start Guide](#quick-start-guide)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License & Legal Disclaimer](#license--legal-disclaimer)
- [References & Documentation](#references--documentation)

---

## Project Overview

LawyerFactory is a comprehensive, automated lawsuit generation platform designed to streamline legal document creation, research, and orchestration. It integrates advanced AI, knowledge graphs, and workflow automation to produce professional-grade legal filings with minimal manual intervention.

---

## Features

- **Automated Document Processing**: Ingests PDF, DOCX, TXT, EML, and CSV files.
- **7-Phase Workflow**: INTAKE → OUTLINE → RESEARCH → DRAFTING → LEGAL_REVIEW → EDITING → ORCHESTRATION.
- **Legal Research Bot**: Integrates with OpenAI and spaCy for advanced research.
- **Knowledge Graph**: Centralized legal data management and reasoning.
- **Document Generator**: Produces lawsuits in multiple formats using Jinja2 templates.
- **Web Interface**: Intuitive Flask-based UI with WebSocket support.
- **Orchestration Engine**: Coordinates bots, workflow, and document generation.
- **API Access**: RESTful endpoints for integration and automation.
- **Validation & Testing**: Includes Tesla case study for system validation.

---

## Architecture Overview

LawyerFactory consists of modular components:

- **Flask Web App** ([`app.py`](app.py)): Main entry point, handles UI and WebSockets.
- **Orchestration Engine** ([`maestro/`](maestro/)): Manages workflow, bots, and event system.
- **Knowledge Graph** ([`knowledge_graph.py`](knowledge_graph.py)): Stores and queries legal entities.
- **Document Generator** ([`lawyerfactory/document_generator/`](lawyerfactory/document_generator/)): Creates legal documents from templates.
- **Research Bot** ([`maestro/bots/research_bot.py`](maestro/bots/research_bot.py)): Automates legal research.
- **Database**: SQLite for persistent storage.
- **Integration Points**: See [`SYSTEM_DOCUMENTATION.md`](SYSTEM_DOCUMENTATION.md) and [`docs/system_architecture.md`](docs/system_architecture.md).

---

## System Requirements

- **Hardware**: 4GB+ RAM, 2+ CPU cores recommended
- **Software**:
  - Python 3.9+
  - pip (Python package manager)
  - SQLite (default, no setup required)
  - Internet access for AI features (OpenAI API)
- **Optional**: spaCy models, Docker (for containerized deployment)

---

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/lawyerfactory.git
   cd lawyerfactory
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy Models (Optional)**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Set Environment Variables**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SECRET_KEY`: Flask secret key
   - See [Configuration](#configuration) for details
-
---

## Quick Start Guide

1. **Start the System**
   ```bash
   python start_enhanced_factory.py
   ```

2. **Access the Web Interface**
   - Open [http://localhost:5000](http://localhost:5000) in your browser

3. **Upload Documents & Generate Lawsuits**
   - Use the UI to upload supported files and follow the workflow

---

## Usage

### Web Interface

- **Upload Documents**: PDF, DOCX, TXT, EML, CSV
- **Workflow Navigation**: Progress through the 7-phase workflow
- **Document Generation**: Download professional lawsuit documents

### Command Line

- **Start System**
  ```bash
  python start_enhanced_factory.py
  ```
- **Validate Integration**
  ```bash
  python validate_system_integration.py
  ```

### API Usage

- **Example: Generate Lawsuit via API**
  ```bash
  curl -X POST http://localhost:5000/api/generate \
    -H "Authorization: Bearer <OPENAI_API_KEY>" \
    -F "file=@sample.pdf"
  ```

- **Python Example**
  ```python
  import requests
  files = {'file': open('sample.pdf', 'rb')}
  headers = {'Authorization': 'Bearer <OPENAI_API_KEY>'}
  r = requests.post('http://localhost:5000/api/generate', files=files, headers=headers)
  print(r.json())
  ```

---

## Configuration

- **Environment Variables**
  - `OPENAI_API_KEY`: Required for AI features
  - `SECRET_KEY`: Flask session security
  - `DATABASE_URL`: (Optional) SQLite path or external DB
  - `UPLOAD_FOLDER`: Directory for uploads
- **System Settings**
  - See [`SYSTEM_DOCUMENTATION.md`](SYSTEM_DOCUMENTATION.md) for advanced options

---

## Project Structure

```
lawyerfactory/
├── app.py
├── start_enhanced_factory.py
├── requirements.txt
├── SYSTEM_DOCUMENTATION.md
├── docs/
│   ├── system_architecture.md
│   ├── research_bot_implementation.md
│   └── ...
├── lawyerfactory/
│   ├── enhanced_workflow.py
│   ├── knowledge_graph.py
│   ├── document_generator/
│   └── ...
├── maestro/
│   ├── enhanced_maestro.py
│   ├── bots/
│   └── ...
├── tests/
│   └── test_*.py
└── uploads/
```

---

## API Documentation

- **POST `/api/generate`**: Generate lawsuit from uploaded document
- **GET `/api/status`**: System health/status
- **GET `/api/workflow`**: Current workflow phase/status
- See [`SYSTEM_DOCUMENTATION.md`](SYSTEM_DOCUMENTATION.md) and [`docs/system_architecture.md`](docs/system_architecture.md) for full API specs

---

## Testing

- **Run All Tests**
  ```bash
  pytest tests/
  ```
- **Validate Tesla Case Example**
  ```bash
  python tesla_case_validation.py
  ```
- **Integration Tests**
  ```bash
  python tests/test_comprehensive_integration.py
  ```

---

## Troubleshooting

- **Common Issues**
  - Missing API key: Set `OPENAI_API_KEY`
  - Dependency errors: Run `pip install -r requirements.txt`
  - Database issues: Ensure SQLite file permissions
  - WebSocket errors: Check browser compatibility

- **Solutions**
  - See [`SYSTEM_DOCUMENTATION.md`](SYSTEM_DOCUMENTATION.md) for detailed troubleshooting

---

## Contributing

- Fork the repository and create a feature branch
- Follow PEP8 and project coding standards
- Add tests for new features
- Submit pull requests with clear descriptions
- See [`docs/implementation_roadmap.md`](docs/implementation_roadmap.md) for roadmap and guidelines

---

## License & Legal Disclaimer

- **License**: MIT License (see [LICENSE](LICENSE))
- **Disclaimer**: LawyerFactory is for educational and research purposes only. It does not provide legal advice. Use at your own risk. Generated documents should be reviewed by a qualified attorney before filing.

---

## References & Documentation

- [SYSTEM_DOCUMENTATION.md](SYSTEM_DOCUMENTATION.md): Comprehensive system documentation
- [docs/system_architecture.md](docs/system_architecture.md): Architecture details
- [docs/](docs/): Component documentation
- [Tesla Case Study](tesla_case_validation.py): Example validation

---
