#!/bin/bash
# Production Build Script
# Builds the Vue frontend for production deployment

echo "🏗️  Building Motion Detection System for Production"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the detector-py root directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed. Please install Node.js first."
    exit 1
fi

# Navigate to frontend directory
echo "📁 Navigating to frontend directory..."
cd web/frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Type check
echo "🔍 Running type check..."
npm run type-check
if [ $? -ne 0 ]; then
    echo "❌ Type check failed. Please fix TypeScript errors first."
    exit 1
fi

# Build for production
echo "🚀 Building frontend for production..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build completed successfully!"
    echo "📂 Built files are in: web/frontend/dist/"
    
    # Show build size
    echo ""
    echo "📊 Build Summary:"
    echo "================="
    if [ -d "dist" ]; then
        du -sh dist/
        echo ""
        echo "📁 Contents:"
        ls -la dist/
    fi
else
    echo "❌ Frontend build failed!"
    exit 1
fi

echo ""
echo "🎉 Production build complete!"
echo "💡 Run './start-prod.sh' to start the production server"