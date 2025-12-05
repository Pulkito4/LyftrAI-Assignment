# PowerShell script to set up and run the LyftrAI Assignment
# This is the Windows equivalent of run.sh

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting LyftrAI Assignment Setup..." -ForegroundColor Cyan

# 1. Check Python
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python 3\.(\d+)") {
            $pythonCmd = $cmd
            Write-Host "✅ Found $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python 3 is required but not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# 2. Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    & $pythonCmd -m venv venv
}

# 3. Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# 4. Install Python dependencies
Write-Host "📥 Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

# 5. Install Playwright browsers
Write-Host "🎭 Installing Playwright browsers..." -ForegroundColor Yellow
playwright install chromium

# 6. Build frontend if it exists
if (Test-Path "frontend") {
    Write-Host "🎨 Building frontend..." -ForegroundColor Yellow
    Push-Location frontend
    
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Installing Node dependencies..." -ForegroundColor Yellow
        npm install
    }
    
    Write-Host "🔨 Building React app..." -ForegroundColor Yellow
    npm run build
    
    Pop-Location
    Write-Host "✅ Frontend built successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Frontend directory not found. Skipping frontend build." -ForegroundColor Yellow
    Write-Host "   API will still be available at http://localhost:8000" -ForegroundColor Yellow
}

# 7. Start server
Write-Host ""
Write-Host "✅ Setup complete! Starting server..." -ForegroundColor Green
Write-Host "🌐 Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API documentation at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn backend.main:app --host 0.0.0.0 --port 8000
