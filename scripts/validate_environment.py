"""
Environment validation script for LawyerFactory
Checks all required dependencies, API keys, and system configuration
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from typing import Dict, List, Tuple


class EnvironmentValidator:
    """Validates LawyerFactory environment and dependencies"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_failed = 0

    def check_python_version(self) -> bool:
        """Validate Python version >= 3.8"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
            self.checks_passed += 1
            return True
        else:
            error = f"✗ Python 3.8+ required, found {version.major}.{version.minor}"
            print(error)
            self.errors.append(error)
            self.checks_failed += 1
            return False

    def check_required_packages(self) -> bool:
        """Check if required Python packages are installed"""
        required_packages = [
            "flask",
            "flask_socketio",
            "eventlet",
            "openai",
            "anthropic",
            "qdrant_client",
            "boto3",
            "pytest",
        ]

        all_present = True
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✓ {package}")
                self.checks_passed += 1
            except ImportError:
                print(f"✗ {package} not installed")
                self.errors.append(f"Missing package: {package}")
                self.checks_failed += 1
                all_present = False

        return all_present

    def check_api_keys(self) -> bool:
        """Validate required API keys are present"""
        ai_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"]
        has_ai_key = any(os.getenv(key) for key in ai_keys)

        if has_ai_key:
            print("✓ AI service API key configured")
            self.checks_passed += 1
        else:
            error = "✗ No AI service API key found (need OPENAI_API_KEY, ANTHROPIC_API_KEY, or GROQ_API_KEY)"
            print(error)
            self.errors.append(error)
            self.checks_failed += 1
            return False

        # Optional keys
        if os.getenv("COURTLISTENER_API_KEY"):
            print("✓ CourtListener API key configured")
            self.checks_passed += 1
        else:
            self.warnings.append("CourtListener API key not configured")

        return True

    def check_storage_paths(self) -> bool:
        """Validate storage directories exist or can be created"""
        storage_paths = {
            "WORKFLOW_STORAGE_PATH": "./workflow_storage",
            "UPLOAD_DIR": "./uploads",
        }

        all_valid = True
        for env_var, default_path in storage_paths.items():
            path = Path(os.getenv(env_var, default_path))
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"✓ Created {path}")
                    self.checks_passed += 1
                except Exception as e:
                    error = f"✗ Could not create {path}: {e}"
                    print(error)
                    self.errors.append(error)
                    self.checks_failed += 1
                    all_valid = False
            else:
                print(f"✓ {path} exists")
                self.checks_passed += 1

        return all_valid

    def check_project_structure(self) -> bool:
        """Validate expected project structure"""
        required_paths = [
            "src/lawyerfactory",
            "apps/api",
            "tests",
            "requirements.txt",
        ]

        all_present = True
        for path in required_paths:
            if Path(path).exists():
                print(f"✓ {path}")
                self.checks_passed += 1
            else:
                error = f"✗ Missing: {path}"
                print(error)
                self.errors.append(error)
                self.checks_failed += 1
                all_present = False

        return all_present

    def check_services(self) -> bool:
        """Check if required services are accessible"""
        try:
            import requests

            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            try:
                response = requests.get(f"{qdrant_url}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✓ Qdrant accessible at {qdrant_url}")
                    self.checks_passed += 1
                    return True
            except Exception:
                self.warnings.append(f"Qdrant not accessible at {qdrant_url}")
                return False
        except ImportError:
            self.warnings.append("requests package not installed - cannot check services")
            return False

    def run_all_checks(self) -> bool:
        """Run all validation checks"""
        print("\n" + "=" * 50)
        print("LawyerFactory Environment Validation")
        print("=" * 50 + "\n")

        print("Checking Python version...")
        self.check_python_version()

        print("\nChecking required packages...")
        self.check_required_packages()

        print("\nChecking API keys...")
        self.check_api_keys()

        print("\nChecking storage paths...")
        self.check_storage_paths()

        print("\nChecking project structure...")
        self.check_project_structure()

        print("\nChecking services...")
        self.check_services()

        # Summary
        print("\n" + "=" * 50)
        print("Validation Summary")
        print("=" * 50)
        print(f"Checks passed: {self.checks_passed}")
        print(f"Checks failed: {self.checks_failed}")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  ✗ {error}")
            return False

        print("\n✓ Environment validation complete!")
        return True


if __name__ == "__main__":
    validator = EnvironmentValidator()
    success = validator.run_all_checks()
    sys.exit(0 if success else 1)