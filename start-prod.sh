#!/bin/bash
# Production Server Script
# Serves the built Vue frontend as static files with Flask backend

echo "🚀 Starting Motion Detection System (Production Mode)"
echo "====================================================="

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "📋 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo "⚠️  Warning: .env file not found, using defaults"
fi

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the detector-py root directory"
    exit 1
fi

# Check if production build exists
if [ ! -d "web/frontend/dist" ]; then
    echo "❌ Error: Production build not found!"
    echo "💡 Run './build.sh' first to create the production build"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Activating venv..."
    source venv/bin/activate
fi

# Set production environment
export ENV_MODE=production

# Use environment variables with defaults
WEB_HOST=${WEB_HOST:-0.0.0.0}
WEB_PORT=${WEB_PORT:-5001}
export PRODUCTION_MODE=true

echo "🔧 Starting Flask backend with static file serving..."
echo "📂 Serving static files from: web/frontend/dist/"
echo "🌐 Application will be available at: http://${WEB_HOST}:${WEB_PORT}"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start Flask backend with static file serving
cd web && python app.py