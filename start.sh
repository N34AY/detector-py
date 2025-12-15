#!/bin/bash
# Full Stack Development Server
# Starts both Flask backend and Vue frontend

echo "🚀 Starting Motion Detection Full Stack Application"
echo "================================================="

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

# Use environment variables with defaults
WEB_HOST=${WEB_HOST:-0.0.0.0}
WEB_PORT=${WEB_PORT:-5001}
VITE_DEV_PORT=${VITE_DEV_PORT:-5173}

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Activating venv..."
    source venv/bin/activate
fi

# Start Flask backend in background
echo "🔧 Starting Flask backend on http://${WEB_HOST}:${WEB_PORT}..."
python3 main.py &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
for i in {1..20}; do
    if curl -s http://${WEB_HOST}:${WEB_PORT}/api/status > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "❌ Backend failed to start after 20 seconds"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
    echo -n "."
done

# Start Vue frontend in background  
echo "🎨 Starting Vue frontend on http://localhost:${VITE_DEV_PORT}..."
cd web/frontend
npm run dev &
FRONTEND_PID=$!

# Go back to root
cd ../..

echo ""
echo "✅ Both servers started successfully!"
echo ""
echo "📡 Flask Backend:  http://${WEB_HOST}:${WEB_PORT}"
echo "🎨 Vue Frontend:   http://localhost:${VITE_DEV_PORT}"
echo ""
echo "💡 Open http://localhost:${VITE_DEV_PORT} in your browser to use the application"
echo ""
echo "🛑 Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped successfully!"
    exit 0
}

# Trap Ctrl+C to cleanup
trap cleanup INT

# Wait for user to press Ctrl+C
wait