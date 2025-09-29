"""
Fix Flask-SocketIO dependency issues by ensuring proper package versions
and resolving import conflicts.
"""

import os
import subprocess
import sys


def run_command(command):
    """Execute shell command and return result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def fix_socketio_dependencies():
    """Fix Flask-SocketIO dependency issues."""
    print("🔧 Fixing Flask-SocketIO dependencies...")

    # Step 1: Uninstall conflicting packages
    print("📦 Removing conflicting packages...")
    packages_to_remove = [
        "flask-socketio",
        "python-socketio",
        "gevent-socketio",
        "socketio",  # This is the conflicting old package
    ]

    for package in packages_to_remove:
        success, stdout, stderr = run_command(f"pip uninstall {package} -y")
        print(f"   - Removed {package}: {'✓' if success else '✗'}")

    # Step 2: Install correct versions
    print("📥 Installing correct package versions...")
    correct_packages = [
        "python-socketio==5.9.0",
        "flask-socketio==5.3.6",
        "eventlet==0.33.3",
        "gevent-websocket==0.10.1",
    ]

    for package in correct_packages:
        success, stdout, stderr = run_command(f"pip install {package}")
        print(f"   - Installed {package}: {'✓' if success else '✗'}")
        if not success:
            print(f"     Error: {stderr}")

    # Step 3: Verify installation
    print("🔍 Verifying installation...")
    try:
        import flask_socketio
        import socketio

        print("   - Flask-SocketIO: ✓")
        print(f"   - Version: {flask_socketio.__version__}")
        return True
    except ImportError as e:
        print(f"   - Import failed: {e}")
        return False


if __name__ == "__main__":
    success = fix_socketio_dependencies()
    if success:
        print("✅ Flask-SocketIO dependencies fixed successfully!")
    else:
        print("❌ Failed to fix dependencies. Manual intervention required.")
        sys.exit(1)
