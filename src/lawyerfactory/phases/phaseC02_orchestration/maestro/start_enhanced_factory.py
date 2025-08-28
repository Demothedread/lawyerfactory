"""
# Script Name: start_enhanced_factory.py
# Description: !/usr/bin/env python3
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Workflow
#   - Group Tags: orchestration
Enhanced LawyerFactory startup script.
Initializes all components and starts the web server.
"""

import logging
import os
from pathlib import Path
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("lawyerfactory.log")],
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []

    try:
        import eventlet
        import flask
        import flask_socketio
    except ImportError as e:
        missing_deps.append(f"Flask dependencies: {e}")

    try:
        from knowledge_graph import KnowledgeGraph
    except ImportError as e:
        missing_deps.append(f"Knowledge Graph: {e}")

    try:
        from maestro.enhanced_maestro import EnhancedMaestro
    except ImportError as e:
        missing_deps.append(f"Enhanced Maestro: {e}")

    try:
        from lawyerfactory.enhanced_workflow import EnhancedWorkflowManager
    except ImportError as e:
        missing_deps.append(f"Enhanced Workflow Manager: {e}")

    if missing_deps:
        logger.error("Missing dependencies:")
        for dep in missing_deps:
            logger.error(f"  - {dep}")
        logger.error(
            "Please install missing dependencies with: pip install -r requirements.txt"
        )
        return False

    return True


def setup_directories():
    """Create necessary directories"""
    directories = [
        "uploads",
        "knowledge_graphs",
        "workflow_storage",
        "templates",
        "static",
        "logs",
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")


def patch_app_imports():
    """Patch the app.py imports to include our extensions"""
    try:
        # Import and patch knowledge graph
        from knowledge_graph_extensions import extend_knowledge_graph

        from knowledge_graph import KnowledgeGraph

        # Monkey patch the KnowledgeGraph class
        original_init = KnowledgeGraph.__init__

        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            extend_knowledge_graph(self)

        KnowledgeGraph.__init__ = patched_init
        logger.info("Knowledge graph extensions applied successfully")

        return True
    except Exception as e:
        logger.error(f"Failed to patch app imports: {e}")
        return False


def main():
    """Main startup function"""
    logger.info("Starting Enhanced LawyerFactory Platform...")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup directories
    setup_directories()

    # Patch imports
    if not patch_app_imports():
        sys.exit(1)

    # Import and start the Flask app
    try:
        from app import app, initialize_components, socketio

        # Initialize backend components
        logger.info("Initializing backend components...")
        initialize_components()

        # Get configuration
        host = os.environ.get("FLASK_HOST", "0.0.0.0")
        port = int(os.environ.get("FLASK_PORT", 5000))
        debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

        logger.info(f"Starting server on {host}:{port} (debug={debug})")

        # Start the server
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,  # Disable reloader in production
        )

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
