#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting LyftrAI Assignment Setup..."

# 1. Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3.8 or higher."
    exit 1
fi

# 2. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 4. Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium

# 6. Check if frontend exists and build it
if [ -d "frontend" ]; then
    echo "🎨 Building frontend..."
    cd frontend
    
    # Install Node dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing Node dependencies..."
        npm install
    fi
    
    # Build frontend
    echo "🔨 Building React app..."
    npm run build
    
    cd ..
    echo "✅ Frontend built successfully!"
else
    echo "⚠️  Frontend directory not found. Skipping frontend build."
    echo "   API will still be available at http://localhost:8000"
fi

# 7. Start FastAPI server
echo ""
echo "✅ Setup complete! Starting server..."
echo "🌐 Server will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn backend.main:app --host 0.0.0.0 --port 8000
