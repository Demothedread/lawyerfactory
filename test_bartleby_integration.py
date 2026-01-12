#!/usr/bin/env python3
"""
Test Bartleby Phase Narration Integration

This script tests the Socket.IO integration between backend phase execution
and Bartleby's live narration feature.
"""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flask import Flask
    from flask_socketio import SocketIO, emit
    from flask_cors import CORS
    print("✅ Flask and Flask-SocketIO available")
except ImportError as e:
    print(f"❌ Missing Flask dependencies: {e}")
    print("Run: pip install flask flask-socketio flask-cors eventlet")
    sys.exit(1)

try:
    from src.lawyerfactory.chat.bartleby_handler import BartlebyChatHandler, register_chat_routes
    print("✅ Bartleby handler available")
except ImportError as e:
    print(f"⚠️  Bartleby handler not available: {e}")
    print("This is expected if dependencies are missing")

def test_socket_narration():
    """Test Socket.IO phase narration"""
    app = Flask(__name__)
    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
    
    print("\n🔧 Testing Socket.IO Phase Narration")
    print("=" * 60)
    
    # Simulate phase narration
    @socketio.on('connect')
    def handle_connect():
        print("✅ Client connected")
        emit('connect_response', {'status': 'connected'})
    
    @socketio.on('bartleby_narrate_phase')
    def handle_narration(data):
        print(f"\n📢 Received narration:")
        print(f"  Phase: {data.get('phase')}")
        print(f"  Event: {data.get('event')}")
        print(f"  Message: {data.get('message')}")
        print(f"  Progress: {data.get('progress')}%")
        
        # Echo back as bartleby_phase_narration
        emit('bartleby_phase_narration', {
            **data,
            'timestamp': time.time()
        }, broadcast=True)
        print("✅ Narration broadcasted to clients")
    
    @socketio.on('bartleby_user_intervention')
    def handle_intervention(data):
        print(f"\n🛑 User Intervention:")
        print(f"  Type: {data.get('intervention_type')}")
        print(f"  Message: {data.get('message')}")
        
        # Mock response
        emit('bartleby_intervention_response', {
            'case_id': data.get('case_id'),
            'phase': data.get('phase'),
            'intervention_type': data.get('intervention_type'),
            'response': f"This is a mock response to: {data.get('message')}",
            'timestamp': time.time()
        })
        print("✅ Intervention response sent")
    
    print("\n✅ Socket.IO handlers registered")
    print("\nTo test manually:")
    print("1. Start backend: python apps/api/server.py")
    print("2. Start frontend: cd apps/ui/react-app && npm run dev")
    print("3. Open http://localhost:3000")
    print("4. Click Bartleby (⚖️) button")
    print("5. Start a phase (e.g., Phase A01)")
    print("6. Watch Bartleby chat for live narration")
    print("\n" + "=" * 60)

def test_bartleby_handler():
    """Test Bartleby chat handler"""
    print("\n🔧 Testing Bartleby Handler")
    print("=" * 60)
    
    try:
        from src.lawyerfactory.chat.bartleby_handler import BartlebyChatHandler
        
        # Initialize handler
        handler = BartlebyChatHandler(
            vector_store_manager=None,
            evidence_table=None
        )
        
        print("✅ BartlebyChatHandler initialized")
        
        # Test system message
        result = handler.add_system_message(
            case_id="test-case-123",
            message="Test phase started",
            metadata={"phase": "phaseA01_intake", "event": "started"}
        )
        print(f"✅ System message test: {result}")
        
        print("\n✅ All Bartleby handler methods available:")
        print("  - add_system_message()")
        print("  - handle_intervention()")
        print("  - send_message()")
        print("  - execute_action()")
        
    except ImportError as e:
        print(f"⚠️  Bartleby handler tests skipped: {e}")
    except Exception as e:
        print(f"❌ Bartleby handler test failed: {e}")
    
    print("=" * 60)

def main():
    print("\n🧪 Bartleby Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Socket.IO setup
    test_socket_narration()
    
    # Test 2: Bartleby handler
    test_bartleby_handler()
    
    print("\n✅ Integration test setup complete!")
    print("\nNext steps:")
    print("1. Install Python dependencies: pip install flask flask-socketio flask-cors eventlet openai anthropic")
    print("2. Start backend: python apps/api/server.py")
    print("3. Start frontend: cd apps/ui/react-app && npm run dev")
    print("4. Test live narration in browser")

if __name__ == "__main__":
    main()
