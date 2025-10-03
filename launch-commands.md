# LawyerFactory development commands

.PHONY: help install launch stop test format clean health validate

help:
    @echo "LawyerFactory Development Commands"
    @echo "=================================="
    @echo "make install     - Install dependencies and setup environment"
    @echo "make launch      - Launch all services"
    @echo "make stop        - Stop all services"
    @echo "make test        - Run all tests"
    @echo "make format      - Format Python code"
    @echo "make clean       - Clean build artifacts and logs"
    @echo "make health      - Run health checks"
    @echo "make validate    - Validate environment configuration"

install:
    python3 -m venv law_venv
    . law_venv/bin/activate && pip install --upgrade pip
    . law_venv/bin/activate && pip install -r requirements.txt
    @echo "✓ Dependencies installed"

launch:
    ./launch-dev.sh

stop:
    ./scripts/stop-services.sh

test:
    . law_venv/bin/activate && python -m pytest tests/ -v

format:
    . law_venv/bin/activate && python -m isort .
    . law_venv/bin/activate && python -m black .
    . law_venv/bin/activate && python -m autopep8 --in-place --aggressive --aggressive .

clean:
    rm -rf logs/*.log
    rm -rf .pids/*.pid .health/*.status
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    @echo "✓ Cleaned build artifacts"

health:
    ./scripts/health-check.sh

validate:
    . law_venv/bin/activate && python scripts/validate_environment.py