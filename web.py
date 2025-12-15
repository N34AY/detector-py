#!/usr/bin/env python3
"""
Web Interface Launcher
Simple script to start the web application
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add web directory to Python path
web_dir = current_dir / 'web'
sys.path.insert(0, str(web_dir))

# Import and run the web application
from web.app import app, socketio, logger, WEB_HOST, WEB_PORT, start_global_sleep_prevention, stop_global_sleep_prevention

if __name__ == '__main__':
    print("=" * 50)
    print("🎯 Motion Detection Web Interface")
    print("=" * 50)
    print(f"📡 Starting server on http://{WEB_HOST}:{WEB_PORT}")
    print("🔧 Use Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start sleep prevention when web app starts
        start_global_sleep_prevention()
        socketio.run(app, host=WEB_HOST, port=WEB_PORT, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        # Stop sleep prevention when web app stops
        stop_global_sleep_prevention()